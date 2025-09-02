import re
from network.paramiko_connection_CiscoDevices import create_device

def get_show_optics_output(ip, username, password):
    """Get the 'show controllers optics' command output from the network device."""
    connection = create_device(ip, username, password)
    output = connection.execute_command("show controllers optics *")
    return output

def parse_show_optics_output(output):
    """Parse the 'show controllers optics' command output and extract relevant data."""
    data = {}
    lines = output.splitlines()
    current_port = None
    for line in lines:
        if re.search(r"Port:.*Optics\d+_\d+_\d+_\d+", line):
            match = re.search(r"Port:.*Optics(\d+)_(\d+)_(\d+)_(\d+)", line)
            if match:
                port_number = f"Optics{match.group(1)}_{match.group(2)}_{match.group(3)}_{match.group(4)}"
                if port_number not in data:
                    data[port_number] = {}
                    current_port = port_number
        if re.search(r"Controller State: (Up|Down)", line):
            match = re.search(r"Controller State: (Up|Down)", line)
            if match:
                data[current_port]['controller_state'] = match.group(1)
        if re.search(r"Transport Admin State: (In Service|Out of Service)", line):
            match = re.search(r"Transport Admin State: (In Service|Out of Service)", line)
            if match:
                data[current_port]['transport_admin_state'] = match.group(1)
        if re.search(r"Laser State: (On|Off)", line):
            match = re.search(r"Laser State: (On|Off)", line)
            if match:
                data[current_port]['laser_state'] = match.group(1)
        if re.search(r"LED State: (Green|Red|Yellow)", line):
            match = re.search(r"LED State: (Green|Red|Yellow)", line)
            if match:
                data[current_port]['led_state'] = match.group(1)
        if re.search(r"Optics Type: (.*)", line):
            match = re.search(r"Optics Type: (.*)", line)
            if match:
                data[current_port]['optics_type'] = match.group(1)
        if re.search(r"Wavelength = (\d+\.\d+) nm", line):
            match = re.search(r"Wavelength = (\d+\.\d+) nm", line)
            if match:
                data[current_port]['wavelength'] = match.group(1)
        if re.search(r"Detected Alarms: (None|.*$)", line):
            match = re.search(r"Detected Alarms: (None|.*$)", line)
            if match:
                data[current_port]['detected_alarms'] = match.group(1)
        if re.search(r"Laser Bias Current = (\d+\.\d+) mA", line):
            match = re.search(r"Laser Bias Current = (\d+\.\d+) mA", line)
            if match:
                data[current_port]['laser_bias_current'] = match.group(1)
        if re.search(r"Actual TX Power = (-?\d+\.\d+) dBm", line):
            match = re.search(r"Actual TX Power = (-?\d+\.\d+) dBm", line)
            if match:
                data[current_port]['actual_tx_power'] = match.group(1)
        if re.search(r"RX Power = (-?\d+\.\d+) dBm", line):
            match = re.search(r"RX Power = (-?\d+\.\d+) dBm", line)
            if match:
                data[current_port]['rx_power'] = match.group(1)
        if re.search(r"Parameter.*High Alarm.*Low Alarm.*High Warning.*Low Warning", line):
            # Start parsing threshold values
            threshold_values = {}
            for i in range(5):
                line = lines[lines.index(line) + i + 1]
                match = re.search(r"(.*)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)", line)
                if match:
                    parameter = match.group(1)
                    high_alarm = match.group(2)
                    low_alarm = match.group(3)
                    high_warning = match.group(4)
                    low_warning = match.group(5)
                    threshold_values[parameter] = {
                        'high_alarm': high_alarm,
                        'low_alarm': low_alarm,
                        'high_warning': high_warning,
                        'low_warning': low_warning
                    }
            data[current_port]['threshold_values'] = threshold_values
        if re.search(r"Temperature = (\d+\.\d+) Celsius", line):
            match = re.search(r"Temperature = (\d+\.\d+) Celsius", line)
            if match:
                data[current_port]['temperature'] = match.group(1)
        if re.search(r"Voltage = (\d+\.\d+) V", line):
            match = re.search(r"Voltage = (\d+\.\d+) V", line)
            if match:
                data[current_port]['voltage'] = match.group(1)
        if re.search(r"Form Factor.*: (.*)", line):
            # Start parsing transceiver vendor details
            transceiver_vendor_details = {}
            for i in range(10):
                line = lines[lines.index(line) + i + 1]
                match = re.search(r"(.*)\s*:\s*(.*)", line)
                if match:
                    key = match.group(1)
                    value = match.group(2)
                    transceiver_vendor_details[key] = value
            data[current_port]['transceiver_vendor_details'] = transceiver_vendor_details
    return data
