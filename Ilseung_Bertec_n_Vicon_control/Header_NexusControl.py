import socket
import xml.etree.ElementTree as ET
import sys

class NexusController:
    def __init__(self, name, notes, description, database_path, delay_ms, packet_id, port):
        self.name = name
        self.notes = notes
        self.description = description
        self.database_path = database_path
        self.delay = delay_ms
        self.packet_id = packet_id
        self.port = port
        self.sock = " "

    def build_start_notification(self):
        """
        Constructs the XML for the Start notification.

        Returns:
            str: The XML string for the Start notification.
        """
        root = ET.Element("CaptureStart")
        
        ET.SubElement(root, "Name", VALUE=self.name)
        
        if self.notes:
            ET.SubElement(root, "Notes", VALUE=self.notes)
        
        if self.description:
            ET.SubElement(root, "Description", VALUE=self.description)
        
        ET.SubElement(root, "DatabasePath", VALUE=self.database_path)
        ET.SubElement(root, "Delay", VALUE=str(self.delay))
        ET.SubElement(root, "PacketID", VALUE=str(self.packet_id))
        
        # Generate XML string without indentation and extra whitespace
        xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'
        xml_content = ET.tostring(root, encoding='utf-8').decode('utf-8')
        full_xml = f"{xml_declaration}{xml_content}"
        
        return full_xml

    def send_udp_broadcast(self, message, broadcast_address='<broadcast>'):
        """
        Sends a UDP broadcast message.

        Args:
            message (str): The message to send.
            broadcast_address (str, optional): The broadcast address. Defaults to '<broadcast>'.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as self.sock:
                # Enable broadcasting mode
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                # Optional: Set a timeout (in seconds)
                self.sock.settimeout(2)
                
                # Encode the message and append a null byte
                data = message.encode('utf-8') + b'\0'
                
                # Send the UDP packet
                self.sock.sendto(data, (broadcast_address, self.port))
                # print(f"Start notification sent on port {self.port}.")
                print('Nexus TRIGGERED')
        except Exception as e:
            print(f"Failed to send UDP broadcast: {e}")
            sys.exit(1)

    def notify(self):
        """
        Main method to send the Start notification.
        """
        # Build the XML message
        xml_message = self.build_start_notification()
        
        # Check the size of the message to ensure it fits in a single UDP packet
        if len(xml_message.encode('utf-8')) + 1 > 65507:
            print("Error: The XML message is too large to fit in a single UDP packet.")
            sys.exit(1)
        
        # Send the UDP broadcast
        self.send_udp_broadcast(xml_message)

    def close_socket(self):
        """Closes the socket if it's open."""
        if self.sock:
            self.sock.close()
            print("Socket closed.")