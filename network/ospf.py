from network.paramiko_connection_CiscoDevices import create_device
import re


def get_ospf_neighbors(ip, username, password):
    """
    Retrieves a list of OSPF neighbors from a Cisco router.

    Args:
    - ip (str): The IP address of the Cisco router.
    - username (str): The username to use for SSH authentication.
    - password (str): The password to use for SSH authentication.

    Returns:
    - A list of dictionaries containing information about each OSPF neighbor.
    """

    # Create an SSH session
    device = create_device(ip, username, password)

    # Execute the command to retrieve OSPF neighbors
    command = "show ip ospf nei det"
    output = device.execute_command(command)

    # If the command was not executed successfully, return an empty list
    if output is None:
        return []

    # Initialize an empty list to store the OSPF neighbors
    ospf_neighbors = []

    # Split the output into lines
    lines = output.splitlines()

    # Initialize a dictionary to store the current neighbor's information
    neighbor_info = {}
    in_neighbor_block = False

    for line in lines:
        line = line.strip()

        # Check if the line contains the start of a neighbor block
        match = re.search(
            r"Neighbor\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}),\s+interface\s+address\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
            line)
        if match:
            if neighbor_info:
                ospf_neighbors.append(neighbor_info)
                neighbor_info = {}
            neighbor_info["neighbor_id"] = match.group(1)
            neighbor_info["interface_address"] = match.group(2)
            in_neighbor_block = True
        elif in_neighbor_block:
            # Check if the line contains the interface information
            match = re.search(r"In the area (.*) via interface (.*)", line)
            if match:
                neighbor_info["area"] = match.group(1)
                interface_name = match.group(2).split(',')[0].strip()
                neighbor_info["interface"] = interface_name
            # Check if the line contains the neighbor priority information
            match = re.search(r"Neighbor priority is (\d+), State is (\w+), (\d+) state changes", line)
            if match:
                neighbor_info["priority"] = int(match.group(1))
                neighbor_info["state"] = match.group(2)
                neighbor_info["state_changes"] = int(match.group(3))
            # Check if the line contains the DR and BDR information
            match = re.search(r"DR is (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) BDR is (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
            if match:
                neighbor_info["DR"] = match.group(1)
                neighbor_info["BDR"] = match.group(2)
            # Check if the line contains the options information
            match = re.search(r"Options is (0x[0-9a-fA-F]+)", line)
            if match:
                neighbor_info["options"] = match.group(1)
            match = re.search(r"LLS Options is (0x[0-9a-fA-F]+) \((\w+)\)", line)
            if match:
                neighbor_info["LLS_options"] = match.group(1)
                neighbor_info["LLS_options_mode"] = match.group(2)
            # Check if the line contains the dead timer information
            match = re.search(r"Dead timer due in (\d{2}:\d{2}:\d{2})", line)
            if match:
                neighbor_info["dead_timer"] = match.group(1)
            # Check if the line contains the uptime information
            match = re.search(r"Neighbor is up for (.+)", line)
            if match:
                neighbor_info["uptime"] = match.group(1)
            # Check if the line contains the DBD retrans information
            match = re.search(r"Number of DBD retrans during last exchange (\d+)", line)
            if match:
                neighbor_info["DBD_retrans"] = int(match.group(1))
            # Check if the line contains the index and retrans queue length information
            match = re.search(r"Index (\d+)/(\d+), retransmission queue length (\d+), number of retransmission (\d+)", line)
            if match:
                neighbor_info["index"] = int(match.group(1))
                neighbor_info["index_total"] = int(match.group(2))
                neighbor_info["retrans_queue_length"] = int(match.group(3))
                neighbor_info["number_retrans"] = int(match.group(4))
            # Check if the line contains the first and next information
            match = re.search(r"First (\d+)\(\d+\)/(\d+)\(\d+\) Next (\d+)\(\d+\)/(\d+)\(\d+\)", line)
            if match:
                neighbor_info["first"] = int(match.group(1))
                neighbor_info["first_total"] = int(match.group(2))
                neighbor_info["next"] = int(match.group(3))
                neighbor_info["next_total"] = int(match.group(4))
            # Check if the line contains the last retransmission scan information
            match = re.search(r"Last retransmission scan length (\d+), maximum is (\d+)", line)
            if match:
                neighbor_info["last_retransmission_scan_length"] = int(match.group(1))
                neighbor_info["last_retransmission_scan_length_max"] = int(match.group(2))
            match = re.search(r"Last retransmission scan time is (\d+) msec, maximum is (\d+) msec", line)
            if match:
                neighbor_info["last_retransmission_scan_time"] = int(match.group(1))
                neighbor_info["last_retransmission_scan_time_max"] = int(match.group(2))
            # Check if the line contains the LS Ack list information
            match = re.search(r"LS Ack list: NSR-sync pending (\d+), high water mark (\d+)", line)
            if match:
                neighbor_info["LS_Ack_pending"] = int(match.group(1))
                neighbor_info["LS_Ack_high_water_mark"] = int(match.group(2))
            # Check if the line contains the BFD status information
            match = re.search(r"Neighbor BFD status: (\w+)", line)
            if match:
                neighbor_info["BFD_status"] = match.group(1)
            # Check if the line contains the neighbor interface ID information
            match = re.search(r"Neighbor Interface ID: (\d+)", line)
            if match:
                neighbor_info["neighbor_interface_id"] = int(match.group(1))

    # Add the last neighbor to the list
    if neighbor_info:
        ospf_neighbors.append(neighbor_info)

    # Close the SSH session
    device.close_connection()

    return ospf_neighbors
