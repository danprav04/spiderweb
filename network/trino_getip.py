from pprint import pprint

from network.trino_connect import TrinoDatalake, HttpError
from time import sleep


class DataBaseError(Exception):
    def __init__(self, message="Couldn't find requested information in the database."):
        self.message = message
        super().__init__(self.message)


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except IndexError:
            raise DataBaseError
        except HttpError:
            try:
                sleep(8)
                result = func(*args, **kwargs)
            except HttpError or IndexError:
                sleep(12)
                result = func(*args, **kwargs)
        return result

    return wrapper


def create_connection_instance():
    return TrinoDatalake()


@error_handler
def get_nihul_ip_by_int_ip(datalake, nexthop_int_ip):
    nexthop = datalake.exec_query(f"""
                                    select ipv4, device_id
                                    from network."crawler-device-interface-inventory"
                                    where int_ip='{nexthop_int_ip}'
                                    order by timestamp DESC
                                        """)

    nexthop = nexthop[0][0]
    nexthop_ip = nexthop[0]
    hostname = nexthop[1]

    return nexthop_ip, hostname


@error_handler
def get_all_int_ips(datalake):
    int_ips = datalake.exec_query(f"""
                                    select ipv4, device_id, int_ip
                                    from network."crawler-device-interface-inventory"
                                    order by timestamp DESC
                                        """)

    int_ips = int_ips[0]

    return int_ips

def trino_test(int_ip):
    datalake = create_connection_instance()
    nexthop_int_ip = int_ip
    try:
        nexthop_ip, hostname = get_nihul_ip_by_int_ip(datalake, nexthop_int_ip)
        print(f"Nexthop IP: {nexthop_ip}")
        print(f"Hostname: {hostname}")
        return nexthop_ip
    except DataBaseError as e:
        print(f"Error: {e}")

