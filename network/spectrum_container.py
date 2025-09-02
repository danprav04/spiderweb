import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

# Constants
URL = 'https://{domain}/spectrum/restful/devices?attr=0x129e7&attr=0x12d7f&throttlesize=10000'
USERNAME = '{username}'
PASSWORD = '{password}'
NAMESPACE = '{http://www.ca.com/spectrum/restful/schema/response}'

def get_spectrum_container_data():
    try:
        response = requests.get(URL, auth=HTTPBasicAuth(USERNAME, PASSWORD), verify=False)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return []

def find_container_from_ip(ip_address: str, spectrum_container_data=None) -> list:
    """
    Find container from IP address.

    Args:
    - ip_address (str): IP address to search for.

    Returns:
    - list: List of containers associated with the IP address.
    """

    if not spectrum_container_data:
        spectrum_container_data = get_spectrum_container_data()

    root = ET.fromstring(spectrum_container_data.text)
    containers = set()

    for model in root.findall(f'.//{NAMESPACE}model'):
        attribute = model.find(f'.//{NAMESPACE}attribute[@id="0x12d7f"]')
        location = model.find(f'.//{NAMESPACE}attribute[@id="0x129e7"]')

        if attribute is not None and location is not None:
            try:
                if len(ip_address.split('.')) == 3:
                    ip_segment = ip_address + '.'
                    if ip_segment in attribute.text:
                        containers.add(location.text.split(':')[-1])
                elif attribute.text == ip_address:
                    containers.add(location.text.split(':')[-1])
            except IndexError:
                pass

    return list(containers)

def spec_test(ip: str) -> None:
    """
    Test the find_container_from_ip function.

    Args:
    - ip (str): IP address to test.
    """
    containers = find_container_from_ip(ip)
    print(containers)
