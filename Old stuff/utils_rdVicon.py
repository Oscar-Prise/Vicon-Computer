"""Read raw COP and GRF signals from a Vicon DataStream client."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vicon_dssdk import ViconDataStream


@dataclass
class ViconFrameSignals:
    """Raw per-frame readings from Vicon."""

    cop_r: float = 0.0
    cop_l: float = 0.0
    frz: float = 0.0
    flz: float = 0.0


def connect_vicon(host: str) -> ViconDataStream.Client:
    """Connect to Vicon and enable device data."""
    from vicon_dssdk import ViconDataStream

    client = ViconDataStream.Client()
    client.Connect(host)
    client.SetBufferSize(1)
    client.EnableDeviceData()
    return client


def wait_for_frame(client: ViconDataStream.Client, timeout: int = 50) -> int:
    """Block until the next Vicon frame is available."""
    from vicon_dssdk import ViconDataStream

    has_frame = False
    remaining = timeout
    while not has_frame:
        try:
            if client.GetFrame():
                has_frame = True
            remaining -= 1
            if remaining < 0:
                print("Failed to get frame")
                sys.exit(1)
        except ViconDataStream.DataStreamException:
            client.GetFrame()

    client.SetStreamMode(ViconDataStream.Client.StreamMode.EServerPush)
    return client.GetFrameNumber()


def read_cop_from_vicon(client: ViconDataStream.Client) -> tuple[float, float]:
    """Read raw COP Y from Vicon devices named Right and Left."""
    cop_right, cop_left = 0.0, 0.0
    devices = client.GetDeviceNames()
    for device_name, _device_type in devices:
        device_output_details = client.GetDeviceOutputDetails(device_name)
        for output_name, component_name, _unit in device_output_details:
            if component_name != "Cy":
                continue
            values, _occluded = client.GetDeviceOutputValues(
                device_name, output_name, component_name
            )
            if device_name == "Right":
                cop_right = float(values[0])
            elif device_name == "Left":
                cop_left = float(values[0])
    return cop_right, cop_left


def read_grf_from_vicon(
    client: ViconDataStream.Client,
    plate_right: int = 1,
    plate_left: int = 2,
) -> tuple[float, float]:
    """Read raw vertical GRF from force plates. Returns (frz, flz)."""
    frz = 0.0
    flz = 0.0
    forceplates = client.GetForcePlates()
    for plate in forceplates:
        global_force_vector_data = client.GetGlobalForceVector(plate)
        if plate == plate_right:
            frz = float(global_force_vector_data[0][2])
        elif plate == plate_left:
            flz = float(global_force_vector_data[0][2])
    return frz, flz


def read_frame_signals(
    client: ViconDataStream.Client,
    plate_right: int = 1,
    plate_left: int = 2,
    timeout: int = 50,
) -> ViconFrameSignals:
    """Wait for the next frame and read raw COP/GRF values."""
    wait_for_frame(client, timeout=timeout)
    cop_r, cop_l = read_cop_from_vicon(client)
    frz, flz = read_grf_from_vicon(
        client, plate_right=plate_right, plate_left=plate_left
    )
    return ViconFrameSignals(cop_r=cop_r, cop_l=cop_l, frz=frz, flz=flz)
