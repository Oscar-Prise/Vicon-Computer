import socket
import xml.etree.ElementTree as ET
import sys

class CaptureNotifier:
    def __init__(self, name, notes, description, database_path, delay_ms, packet_id, port):
        self.name = name
        self.notes = notes
        self.description = description
        self.database_path = database_path
        self.delay = delay_ms
        self.packet_id = packet_id
        self.port = port

    def _to_xml(self, root):
        # Generate XML string without indentation and extra whitespace
        xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        xml_content = ET.tostring(root, encoding='utf-8').decode('utf-8')
        return f"{xml_declaration}{xml_content}"

    def build_start_notification(self):
        """Constructs the XML for the CaptureStart notification."""
        root = ET.Element("CaptureStart")
        ET.SubElement(root, "Name", VALUE=self.name)
        if self.notes:
            ET.SubElement(root, "Notes", VALUE=self.notes)
        if self.description:
            ET.SubElement(root, "Description", VALUE=self.description)
        ET.SubElement(root, "DatabasePath", VALUE=self.database_path)
        ET.SubElement(root, "Delay", VALUE=str(self.delay))
        ET.SubElement(root, "PacketID", VALUE=str(self.packet_id))
        return self._to_xml(root)

    def build_stop_notification(self):
        """Constructs the XML for the CaptureStop notification."""
        root = ET.Element("CaptureStop", RESULT="SUCCESS")
        ET.SubElement(root, "Name", VALUE=self.name)
        ET.SubElement(root, "DatabasePath", VALUE=self.database_path)
        ET.SubElement(root, "Delay", VALUE=str(self.delay))
        ET.SubElement(root, "PacketID", VALUE=str(self.packet_id))
        return self._to_xml(root)

    def send_udp_broadcast(self, message, broadcast_address='127.255.255.255'):
        """Sends a null-terminated UDP broadcast message."""
        data = message.encode('utf-8') + b'\0'
        # Check the size of the message to ensure it fits in a single UDP packet
        if len(data) > 65507:
            print("Error: The XML message is too large to fit in a single UDP packet.")
            sys.exit(1)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(2)
                sock.sendto(data, (broadcast_address, self.port))
        except Exception as e:
            print(f"Failed to send UDP broadcast: {e}")
            sys.exit(1)

    def notify(self):
        """Start the Vicon Nexus capture."""
        self.send_udp_broadcast(self.build_start_notification())
        print(f"Vicon capture START sent on port {self.port} ({self.name}).", flush=True)

    def stop_capture(self):
        """Stop the Vicon Nexus capture. Nexus ignores repeated PacketIDs, so bump it."""
        self.packet_id = (self.packet_id + 1) % 2**32
        self.send_udp_broadcast(self.build_stop_notification())
        print(f"Vicon capture STOP sent on port {self.port} ({self.name}).", flush=True)
