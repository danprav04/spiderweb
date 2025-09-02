import json
import socket
from http import HTTPStatus
from starlette.responses import JSONResponse
from collections import defaultdict
import xml.etree.ElementTree as ET
import smbclient
from smbprotocol.exceptions import LogonFailure, AccessDenied


def copy_file(srv):
    username = ".\\{username}"
    password = "{password}"
    filepath = f"\\\\{srv}\\d$\\win32app\\Spectrum\\SS-Tools\\TzofeIsrael.xml"
    content = None
    try:
        with smbclient.open_file(filepath, mode='r') as file:
            content = file.read()
    except (LogonFailure, AccessDenied):
        try:
            with smbclient.open_file(filepath, mode='r', username=username, password=password) as file:
                content = file.read()
        except Exception:
            return None
    except Exception:
        return None
    return content


# Function to extract relevant data
def extract_relevant_data_xml(site_name, file_data):
    tree = ET.fromstring(file_data)  # Reading the xml
    root = tree  # tree is already the root element
    devices = []
    device_connections = defaultdict(list)

    # Iterate through the Topology_Container elements
    for topology_remove in root.iterfind('.//Topology_Container'):
        if topology_remove.attrib.get('name', None) != site_name:
            try:
                topology_remove.clear()
            except Exception as e:
                print(e)

    for topology_cont in root.iterfind('.//Topology_Container'):
        for device_element in topology_cont.iterfind('.//Device'):
            if topology_cont.attrib.get('name', None) != site_name:
                continue
            model_type = device_element.get('model_type', None)
            model_class = device_element.get('Model_Class', 0)
            if model_type:
                network_address = device_element.get('network_address', None)
                name = device_element.get('name', None)
                x_coordinate = int(device_element.get('x_coordinate', 0))-1000
                y_coordinate = int(device_element.get('y_coordinate', 0))-700
                devices.append((network_address, name, model_type, x_coordinate, y_coordinate, model_class))

        # Iterate through the Connection elements
        for connection in topology_cont.iterfind('.//Connection'):
            if topology_cont.attrib.get('name', None) != site_name:
                continue

            # Extracting data from each Connection
            devices_conn = connection.findall('.//Device')
            device_connections[devices_conn[0].attrib.get('network_address', None)].append(devices_conn[1].attrib.get('network_address', None))

    return devices, device_connections


def _create_sock(known_srv, container_name):
    sock = socket.socket()
    try:
        sock.settimeout(10)
        sock.connect((known_srv, 6901))
        msg = "{msg}" + container_name
        sock.send(msg.encode())
        data = sock.recv(1024).decode()
        sock.close()
        if "Modeling Gateway export finished successfully" in data:
            file_data = copy_file(known_srv)
            devices, devices_connections = extract_relevant_data_xml(container_name, file_data)
            return devices, devices_connections
    except ConnectionResetError as e:
        log_content = f'Connection refused {str(e)}'
        sock.close()
        return None
    except socket.timeout as e:
        log_content = f'timeout {str(e)}'
        sock.close()
        return None
    return ""


def export_map(container_name) -> JSONResponse:
    spec_servers = ["{domain_1}", "{domain_2}"]

    for srv in spec_servers:
        sock_res = _create_sock(srv, container_name)
        if sock_res is None:
            continue
        elif len(sock_res) == 2:
            return sock_res
    err_msg = "can not export map"
    return err_msg


if __name__ == '__main__':
    export_map('Kirya')
