import os
from dotenv import load_dotenv

load_dotenv()

physical_status_severity = os.getenv("PHYSICAL_STATUS_SEVERITY", 6)
physical_status_type = os.getenv("PHYSICAL_STATUS_TYPE", "Warning")

protocol_status_severity = os.getenv("PROTOCOL_STATUS_SEVERITY", 6)
protocol_status_type = os.getenv("PROTOCOL_STATUS_TYPE", "Warning")

mpls_ldp_severity = os.getenv("KPLS_LDP_SEVERITY", 9)
mpls_ldp_type = os.getenv("KPLS_LDP_TYPE", "Error")

ospf_severity = os.getenv("OSPF_SEVERITY", 10)
ospf_type = os.getenv("OSPF_TYPE", "Error")
