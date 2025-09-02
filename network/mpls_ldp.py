from network.paramiko_connection_CiscoDevices import create_device


def get_mpls_ldp_neighbors(ip, username, password):
    """
    Retrieves a list of MPLS LDP neighbors from a Cisco router.

    Args:
    - ip (str): The IP address of the Cisco router.
    - username (str): The username to use for SSH authentication.
    - password (str): The password to use for SSH authentication.

    Returns:
    - A list of dictionaries containing information about each LDP neighbor.
    """

    # Create an SSH session
    device = create_device(ip, username, password)

    # Execute the command to retrieve LDP neighbors
    command = "show mpls ldp neighbor"
    output = device.execute_command(command)

    # If the command was not executed successfully, return an empty list
    if output is None:
        return []

    # Initialize an empty list to store the LDP neighbors
    ldp_neighbors = []

    # Split the output into lines
    lines = output.splitlines()

    # Initialize a variable to store the current neighbor
    neighbor_info = {}
    neighbor_info["ldp_discovery_sources"] = []
    neighbor_info["addresses"] = []

    # Iterate over the lines to extract neighbor information
    i = 0
    while i < len(lines):
        # Check if the line contains neighbor information
        line = lines[i]
        if "Peer LDP Identifier" in line:
            if neighbor_info:
                ldp_neighbors.append(neighbor_info)
                neighbor_info = {}
                neighbor_info["ldp_discovery_sources"] = []
                neighbor_info["addresses"] = []
            neighbor_info["ldp_identifier"] = line.split(":")[1].strip()
        elif "TCP connection:" in line:
            neighbor_info["tcp_connection"] = line.split(":")[1].strip()
        elif "Graceful Restart:" in line:
            neighbor_info["graceful_restart"] = line.split(":")[1].strip()
        elif "Session Holdtime:" in line:
            neighbor_info["session_holdtime"] = line.split(":")[1].strip()
        elif "State:" in line:
            parts = line.split(";")
            state_parts = parts[0].split(":")
            neighbor_info["state"] = state_parts[1].strip()
            neighbor_info["messages"] = parts[1].split(" sent/rcvd: ")[1].split("/")
            neighbor_info["messages_sent"] = neighbor_info["messages"][0]
            neighbor_info["messages_received"] = neighbor_info["messages"][1]
        elif "Up time:" in line:
            neighbor_info["up_time"] = line.split(":")[1].strip()
        elif "LDP Discovery Sources:" in line:
            i += 1
            line = lines[i]
            if "IPv4:" in line:
                neighbor_info["ldp_discovery_sources"] = line.split(":")[1].strip().split()[1:]
                if len(neighbor_info["ldp_discovery_sources"]) == 0:
                    i += 1
                    line = lines[i]
                    neighbor_info["ldp_discovery_sources"] = line.strip().split()
                i += 1
                line = lines[i]
                while "IPv6:" not in line and i < len(lines) - 1:
                    neighbor_info["ldp_discovery_sources"].extend(line.strip().split())
                    i += 1
                    line = lines[i]
        elif "Addresses bound to this peer:" in line:
            i += 1
            line = lines[i]
            if "IPv4:" in line:
                neighbor_info["addresses"] = line.split(":")[1].strip().split()[1:]
                i += 1
                line = lines[i]
                while "IPv6:" not in line and i < len(lines) - 1:
                    neighbor_info["addresses"].extend(line.strip().split())
                    i += 1
                    line = lines[i]
        i += 1

    # Add the last neighbor to the list
    if neighbor_info:
        ldp_neighbors.append(neighbor_info)

    # Close the SSH session
    device.close_connection()

    return ldp_neighbors
