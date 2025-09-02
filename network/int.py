import re
from network.paramiko_connection_CiscoDevices import create_device


def get_show_int_output(ip, username, password):
    """Get the 'show int' command output from the network device."""
    connection = create_device(ip, username, password)
    output = connection.execute_command("show int")
    return output

def parse_show_int_output(output):
    """Parse the 'show int' command output and extract relevant data."""
    data = {}
    lines = output.splitlines()
    current_interface = None
    for line in lines:
        if re.search(r".* is (up|down|administratively down)", line):
            interface_name = line.split()[0]
            if interface_name not in data:
                data[interface_name] = {}
                current_interface = interface_name
            match = re.search(r"is (up|down|administratively down)", line)
            if match:
                data[current_interface]['physical_status'] = match.group(1)
        if re.search(r"line protocol is (up|down|administratively down)", line):
            match = re.search(r"line protocol is (up|down|administratively down)", line)
            if match:
                data[current_interface]['protocol_status'] = match.group(1)
        if re.search(r"Description: (.*)", line):
            match = re.search(r"Description: (.*)", line)
            if match:
                data[current_interface]['description'] = match.group(1)
        if re.search(r"Full-duplex", line):
            words = line.split(', ')
            if len(words) > 3:
                data[current_interface]['media_type'] = words[2]
        if re.search(r"media type is (.*),", line):
            match = re.search(r"media type is (.*),", line)
            if match:
                data[current_interface]['media_type'] = match.group(1)
        if re.search(r"MTU (\d+) bytes", line):
            match = re.search(r"MTU (\d+) bytes", line)
            if match:
                data[current_interface]['mtu'] = match.group(1)
        if re.search(r"BW (\d+) Kbit", line):
            match = re.search(r"BW (\d+) Kbit", line)
            if match:
                data[current_interface]['bw'] = match.group(1)
        if re.search(r"30 second input rate", line):
            match = re.search(r"30 second input rate (\d+) bits/sec, (\d+) packets/sec", line)
            if match:
                data[current_interface]['input_rate'] = f"{match.group(1)}"
        if re.search(r"30 second output rate", line):
            match = re.search(r"30 second output rate (\d+) bits/sec, (\d+) packets/sec", line)
            if match:
                data[current_interface]['output_rate'] = f"{match.group(1)}"
        if re.search(r"5 minute input rate", line):
            match = re.search(r"5 minute input rate (\d+) bits/sec, (\d+) packets/sec", line)
            if match:
                data[current_interface]['input_rate'] = f"{match.group(1)}"
        if re.search(r"5 minute output rate", line):
            match = re.search(r"5 minute output rate (\d+) bits/sec, (\d+) packets/sec", line)
            if match:
                data[current_interface]['output_rate'] = f"{match.group(1)}"
        if re.search(r"(\d+) input errors", line):
            match = re.search(r"(\d+) input errors", line)
            if match:
                data[current_interface]['input_errors'] = match.group(1)
        if re.search(r"(\d+) output errors", line):
            match = re.search(r"(\d+) output errors", line)
            if match:
                data[current_interface]['output_errors'] = match.group(1)
        if re.search(r"(\d+) CRC", line):
            match = re.search(r"(\d+) CRC", line)
            if match:
                data[current_interface]['crc'] = match.group(1)

        # Added parsing for Internet address
        match = re.search(r"internet address is ((?:\d{1,3}\.){3}\d{1,3})", line.lower())
        if match:
            data[current_interface]['interface_ip'] = match.group(1)
    return data
