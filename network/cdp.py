import re
from network.paramiko_connection_CiscoDevices import create_device


def get_cdp_devices(ip, username, password):
    """
    Retrieves a list of CDP devices from a Cisco router.

    Args:
    - ip (str): The IP address of the Cisco router.
    - username (str): The username to use for SSH authentication.
    - password (str): The password to use for SSH authentication.

    Returns:
    - A list of dictionaries containing information about each CDP device.
    """

    # Create an SSH session
    device = create_device(ip, username, password)

    # Execute the command to retrieve CDP devices
    command = "sh cdp n d"
    output = device.execute_command(command)

    # If the command was not executed successfully, return an empty list
    if output is None:
        return []

    # Initialize an empty list to store the CDP devices
    cdp_devices = []

    # Regular expressions to extract device information
    device_id_pattern = r"Device ID: (.*)"
    ip_address_pattern = r"IP address: (.*)"
    platform_pattern = r"Platform: (.*),"
    interface_pattern = r"Interface: (.*)"
    port_id_pattern = r"Port ID \(outgoing port\): (.*)"

    # Split the output into blocks separated by the "-------------------------" line
    blocks = re.split(r"-{20}", output)

    # Iterate over the blocks to extract device information
    for block in blocks:
        device_info = {}

        # Extract device ID
        match = re.search(device_id_pattern, block)
        if match:
            device_info["device_id"] = match.group(1).strip()

        # Extract IP address
        matches = re.findall(ip_address_pattern, block)
        if matches:
            device_info["ipv4_address"] = matches[0].strip()

        # Extract platform and capabilities
        match = re.search(platform_pattern, block)
        if match:
            parts = match.group(1).split(", ")
            device_info["platform"] = parts[0].strip()
            if len(parts) > 1:
                device_info["capabilities"] = parts[1].strip()

        # Extract interface and port ID
        match = re.search(interface_pattern, block)
        if match:
            device_info["interface"] = match.group(1).split(',')[0].strip()
        match = re.search(port_id_pattern, block)
        if match:
            device_info["port_id"] = match.group(1).strip()

        # Add the device to the list if it has a device ID
        if "device_id" in device_info:
            cdp_devices.append(device_info)

    # Close the SSH session
    device.close_connection()

    return cdp_devices
