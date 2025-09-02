from crawler.sync_repos.sync_coredevice_repo import CoreDeviceRepository
from crawler.sync_repos.sync_link_repo import LinkRepository
from app.models.link import Link
from network.cdp import get_cdp_devices
from app.schemas.link import LinkCreate
from network.int import get_show_int_output, parse_show_int_output
from network.mpls_ldp import get_mpls_ldp_neighbors
from network.ospf import get_ospf_neighbors
from network.controllers_optics import get_show_optics_output, parse_show_optics_output
from network.spectrum_container import find_container_from_ip
from network.trino_getip import get_nihul_ip_by_int_ip, create_connection_instance


class LinkService:
    def __init__(self, ip, username, password, coredevice_id, core_devices, int_ips, spectrum_container_data, count):
        self.ip = ip
        self.username = username
        self.password = password
        self.coredevice_id = coredevice_id
        self.core_devices = core_devices
        self.count = count
        self.int_ips = int_ips
        self.links = {}
        self.link_repository = LinkRepository()
        self.spectrum_container_data = spectrum_container_data

        self.show_int_output = []
        self.show_int_data = []
        self.show_optics_output = []
        self.show_optics_data = []
        self.cdp_devices = []
        self.ospf_neighbors = []
        self.mpls_ldp_neighbors = []

    def fetch_data(self):
        """
        Fetch all the required data from the network devices.
        """
        self.show_int_output = get_show_int_output(self.ip, self.username, self.password)
        self.show_int_data = parse_show_int_output(self.show_int_output)
        self.show_optics_output = get_show_optics_output(self.ip, self.username, self.password)
        self.show_optics_data = parse_show_optics_output(self.show_optics_output)
        self.cdp_devices = get_cdp_devices(self.ip, self.username, self.password)
        self.ospf_neighbors = get_ospf_neighbors(self.ip, self.username, self.password)
        self.mpls_ldp_neighbors = get_mpls_ldp_neighbors(self.ip, self.username, self.password)

    def sort_and_create_links(self):
        """
        Sort and create the links based on the fetched data.
        """
        for device in self.cdp_devices:
            interface_name = device["interface"]
            if (interface_name, self.coredevice_id) in self.links:
                self.links[(interface_name, self.coredevice_id)]["link"].cdp = device["device_id"]
            else:
                new_link = LinkCreate(
                    name=interface_name,
                    physical_status="",
                    protocol_status="",
                    mpls_ldp="",
                    ospf="",
                    ospf_interface_address="",
                    bw="",
                    description="",
                    media_type="",
                    cdp=device["device_id"],
                    input_rate="",
                    output_rate="",
                    tx="",
                    rx="",
                    mtu="",
                    input_errors="",
                    output_errors="",
                    crc="",
                    interface_ip=""  # Added interface_ip field
                )
                self.links[(interface_name, self.coredevice_id)] = {"link": new_link, "coredevice_id": self.coredevice_id}

        for name, data in self.show_int_data.items():
            if (name, self.coredevice_id) in self.links:
                self.links[(name, self.coredevice_id)]["link"].physical_status = data.get('physical_status', '')
                self.links[(name, self.coredevice_id)]["link"].protocol_status = data.get('protocol_status', '')
                self.links[(name, self.coredevice_id)]["link"].description = data.get('description', '')
                self.links[(name, self.coredevice_id)]["link"].media_type = data.get('media_type', '')
                self.links[(name, self.coredevice_id)]["link"].mtu = data.get('mtu', '')
                self.links[(name, self.coredevice_id)]["link"].bw = data.get('bw', '')
                self.links[(name, self.coredevice_id)]["link"].input_rate = data.get('input_rate', '')
                self.links[(name, self.coredevice_id)]["link"].output_rate = data.get('output_rate', '')
                self.links[(name, self.coredevice_id)]["link"].tx = data.get('tx', '')
                self.links[(name, self.coredevice_id)]["link"].rx = data.get('rx', '')
                self.links[(name, self.coredevice_id)]["link"].input_errors = data.get('input_errors', '')
                self.links[(name, self.coredevice_id)]["link"].output_errors = data.get('output_errors', '')
                self.links[(name, self.coredevice_id)]["link"].crc = data.get('crc', '')
                self.links[(name, self.coredevice_id)]["link"].interface_ip = data.get('interface_ip', '')  # Added interface_ip
            elif data.get('description', '') and (name, self.coredevice_id) not in self.links:
                new_link = LinkCreate(
                    name=name,
                    physical_status=data.get('physical_status', ''),
                    protocol_status=data.get('protocol_status', ''),
                    mpls_ldp="",
                    ospf="",
                    ospf_interface_address="",
                    bw=data.get('bw', ''),
                    description=data.get('description', ''),
                    media_type=data.get('media_type', ''),
                    cdp="",
                    input_rate=data.get('input_rate', ''),
                    output_rate=data.get('output_rate', ''),
                    tx=data.get('tx', ''),
                    rx=data.get('rx', ''),
                    mtu=data.get('mtu', ''),
                    input_errors=data.get('input_errors', ''),
                    output_errors=data.get('output_errors', ''),
                    crc=data.get('crc', ''),
                    interface_ip=data.get('interface_ip', '')  # Added interface_ip field
                )
                self.links[(name, self.coredevice_id)] = {"link": new_link, "coredevice_id": self.coredevice_id}

        for port, data in self.show_optics_data.items():
            interface_name = self.get_interface_name(port)
            if (interface_name, self.coredevice_id) in self.links:
                self.links[(interface_name, self.coredevice_id)]["link"].tx = str(data.get('actual_tx_power', ''))
                self.links[(interface_name, self.coredevice_id)]["link"].rx = str(data.get('rx_power', ''))
                self.links[(interface_name, self.coredevice_id)]["link"].interface_ip = ""  # Placeholder for interface_ip
            elif interface_name and (interface_name, self.coredevice_id) not in self.links:
                new_link = LinkCreate(
                    name=interface_name,
                    physical_status="",
                    protocol_status="",
                    mpls_ldp="",
                    ospf="",
                    ospf_interface_address="",
                    bw="",
                    description="",
                    media_type="",
                    cdp="",
                    input_rate="",
                    output_rate="",
                    tx=str(data.get('actual_tx_power', '')),
                    rx=str(data.get('rx_power', '')),
                    mtu="",
                    input_errors="",
                    output_errors="",
                    crc="",
                    interface_ip=""  # Added interface_ip field
                )
                self.links[(interface_name, self.coredevice_id)] = {"link": new_link,
                                                                    "coredevice_id": self.coredevice_id}

        for ospf_neighbor in self.ospf_neighbors:
            if (ospf_neighbor['interface'], self.coredevice_id) in self.links:
                self.links[(ospf_neighbor['interface'], self.coredevice_id)]["link"].ospf = ospf_neighbor['state']
                self.links[(ospf_neighbor['interface'], self.coredevice_id)]["link"].ospf_interface_address = ospf_neighbor['interface_address']

        for mpls_ldp_neighbor in self.mpls_ldp_neighbors:
            for interface in mpls_ldp_neighbor['ldp_discovery_sources']:
                if (interface, self.coredevice_id) in self.links:
                    self.links[(interface, self.coredevice_id)]["link"].mpls_ldp = 'up'

    def get_interface_name(self, port):
        # Extract the numbers from the port name
        numbers = [int(''.join([char for char in part if char.isdigit()])) for part in port.split('_')]

        # Find an interface in the show_int_data that has the same numbers
        for name, _ in self.show_int_data.items():
            # Remove any non-numeric characters from the interface name
            interface_name = ''.join(filter(str.isdigit, name))

            # If the interface name contains numbers, compare them to the port numbers
            if interface_name:
                interface_numbers = [int(d) for d in interface_name]
                if len(interface_numbers) == len(numbers) and interface_numbers == numbers:
                    return name

        return None

    def save_to_database(self):
        """
        Save the created links to the database.
        """

        for value in self.links.values():
            neighbor_coredevice_id = None
            container_name = None
            neighbor_ip = None
            if value["link"].ospf_interface_address:
                neighbor_ip = None

                filtered_neighbor_ips = list(filter(lambda ip: ip[2] == value["link"].ospf_interface_address, self.int_ips))
                if len(filtered_neighbor_ips) > 0:
                    neighbor_ip = filtered_neighbor_ips[0][0]
                filtered_coredevices = list(filter(lambda device: device.ip == neighbor_ip, self.core_devices))
                if len(filtered_coredevices) > 0:
                    neighbor_coredevice_id = filtered_coredevices[0].id

                if neighbor_ip:
                    container_names = find_container_from_ip(neighbor_ip, self.spectrum_container_data)
                    if len(container_names) > 0:
                        container_name = container_names[0]

            self.link_repository.create_link(link=value["link"],
                                             coredevice_id=value["coredevice_id"],
                                             count=self.count,
                                             neighbor_coredevice_id=neighbor_coredevice_id,
                                             container_name=container_name,
                                             neighbor_ip=neighbor_ip
                                             )

    def process_links(self):
        """
        Fetch data, sort and create links, and save them to the database.
        """
        self.fetch_data()
        self.sort_and_create_links()
        self.save_to_database()
