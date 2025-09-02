from network.paramiko_connection_CiscoDevices import create_device


def get_interface_descriptions(ip, username, password):
    """
    Retrieves a list of interface descriptions from a Cisco router.

    Args:
    - ip (str): The IP address of the Cisco router.
    - username (str): The username to use for SSH authentication.
    - password (str): The password to use for SSH authentication.

    Returns:
    - A list of dictionaries containing interface information, including name, status, protocol, and description.
    """

    # Create an SSH session
    device = create_device(ip, username, password)

    # Execute the command to retrieve interface descriptions
    command = "show interface description"
    output = device.execute_command(command)

    # If the command was not executed successfully, return an empty list
    if output is None:
        return []

    # Initialize an empty list to store the interface descriptions
    interfaces = []

    # Split the output into lines
    lines = output.splitlines()

    # Skip the header lines
    start_idx = 0
    for i, line in enumerate(lines):
        if "Interface" in line:
            start_idx = i + 1
            break

    # Iterate over the lines to extract interface information
    for line in lines[start_idx:]:
        # Ignore blank lines
        if not line.strip():
            continue

        # Split the line into columns
        columns = line.split()

        if len(columns) < 4:
            continue

        # Create a dictionary to store the interface information
        interface = {
            "interface": columns[0],
            "status": columns[1],
            "protocol": columns[2],
            "description": " ".join(columns[3:])
        }

        # Add the interface to the list
        interfaces.append(interface)

    # Close the SSH session
    device.close_connection()

    return interfaces
