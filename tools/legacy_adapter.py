#!/usr/bin/env python3

import argparse
import json
import re

import requests
from bs4 import BeautifulSoup


LOGIN = "admin"
PASSWORD = "1q2w3e4r"


# Соответствие портов bitmap новой прошивки.
PORT_BITS = {
    1: 0x8000,
    2: 0x4000,
    3: 0x2000,
    4: 0x1000,
    5: 0x0800,
    6: 0x0400,
    7: 0x0200,
    8: 0x0100,
    9: 0x0080,
    10: 0x0040,
}


def encode_vlan_bitmap(tagged, untagged):
    """Convert VLAN membership to a two-byte bitmap."""

    bitmap = 0

    for port in set(tagged) | set(untagged):
        if port not in PORT_BITS:
            raise ValueError(f"Unsupported port: {port}")

        bitmap |= PORT_BITS[port]

    return f"{bitmap >> 8:02X} {bitmap & 0xFF:02X}"


def login(session, ip):
    """Authenticate to the legacy NXI-3030 Web interface."""

    response = session.post(
        f"http://{ip}/goform/SetSigninInfo",
        data={
            "userName": LOGIN,
            "password": PASSWORD,
            "language": "3",
            "result": "1",
        },
        timeout=10,
    )

    response.raise_for_status()


def get_vlan_ids(session, ip):
    """Get VLAN IDs from vlan.asp."""

    response = session.get(
        f"http://{ip}/vlan.asp",
        timeout=10,
    )

    response.raise_for_status()

    return sorted(
        set(
            re.findall(
                r"vlan_show\.asp\?vlanid=(\d+)",
                response.text,
            )
        ),
        key=int,
    )


def get_vlan_config(session, ip, vlan_id):
    """Read Tagged/Untagged ports for one VLAN."""

    response = session.get(
        f"http://{ip}/vlan_show.asp?vlanid={vlan_id}",
        timeout=10,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    tagged = []
    untagged = []

    for port in range(1, 10):

        checkbox = soup.find(
            "input",
            {
                "name": f"select{port}",
                "type": "checkbox",
            },
        )

        if checkbox is None:
            continue

        if not checkbox.has_attr("checked"):
            continue

        radios = soup.find_all(
            "input",
            {
                "name": f"rate{port}",
            },
        )

        for radio in radios:

            if not radio.has_attr("checked"):
                continue

            value = radio.get("value")

            if value == "1":
                tagged.append(port)

            elif value == "2":
                untagged.append(port)

    return tagged, untagged


def create_session(ip):
    """Create authenticated HTTP session."""

    session = requests.Session()

    login(
        session,
        ip,
    )

    return session


def discovery(session, ip):
    """Output Zabbix LLD discovery JSON."""

    vlan_ids = get_vlan_ids(
        session,
        ip,
    )

    result = []

    for vlan_id in vlan_ids:
        result.append(
            {
                "{#VLANID}": str(vlan_id)
            }
        )

    print(
        json.dumps(
            result,
            separators=(",", ":"),
        )
    )


def vlan_value(session, ip, vlan_id):
    """Output bitmap for one VLAN."""

    vlan_ids = get_vlan_ids(
        session,
        ip,
    )

    vlan_ids = [int(vlan) for vlan in vlan_ids]

    if vlan_id not in vlan_ids:
        raise ValueError(
            f"VLAN {vlan_id} not found"
        )

    tagged, untagged = get_vlan_config(
        session,
        ip,
        vlan_id,
    )

    bitmap = encode_vlan_bitmap(
        tagged,
        untagged,
    )

    print(bitmap)
    
def membership_value(session, ip, vlan_id, port):
    """Output membership for one VLAN port."""

    vlan_ids = get_vlan_ids(
        session,
        ip,
    )

    vlan_ids = [int(vlan) for vlan in vlan_ids]

    if vlan_id not in vlan_ids:
        raise ValueError(
            f"VLAN {vlan_id} not found"
        )

    tagged, untagged = get_vlan_config(
        session,
        ip,
        vlan_id,
    )

    if port in untagged:
        print("Untagged")
        return

    if port in tagged:
        print("Tagged")
        return

    raise ValueError(
        f"Port {port} is not a member of VLAN {vlan_id}"
    )

def membership_discovery(session, ip, vlan_id):
    """Output Zabbix LLD for VLAN port membership."""

    vlan_ids = get_vlan_ids(
        session,
        ip,
    )

    vlan_ids = [int(vlan) for vlan in vlan_ids]

    if vlan_id not in vlan_ids:
        raise ValueError(
            f"VLAN {vlan_id} not found"
        )

    tagged, untagged = get_vlan_config(
        session,
        ip,
        vlan_id,
    )

    result = []

    for port in untagged:
        result.append(
            {
                "{#VLANID}": str(vlan_id),
                "{#PORT}": str(port),
                "{#MEMBERSHIP}": "Untagged",
            }
        )

    for port in tagged:
        result.append(
            {
                "{#VLANID}": str(vlan_id),
                "{#PORT}": str(port),
                "{#MEMBERSHIP}": "Tagged",
            }
        )

    print(
        json.dumps(
            result,
            separators=(",", ":"),
        )
    )

def membership_discovery_all(session, ip):
    """Output Zabbix LLD for all VLAN port memberships."""

    vlan_ids = get_vlan_ids(
        session,
        ip,
    )

    result = []

    for vlan_id in vlan_ids:
        vlan_id = int(vlan_id)

        tagged, untagged = get_vlan_config(
            session,
            ip,
            vlan_id,
        )

        for port in untagged:
            result.append(
                {
                    "{#VLANID}": str(vlan_id),
                    "{#PORT}": str(port),
                    "{#MEMBERSHIP}": "Untagged",
                }
            )

        for port in tagged:
            result.append(
                {
                    "{#VLANID}": str(vlan_id),
                    "{#PORT}": str(port),
                    "{#MEMBERSHIP}": "Tagged",
                }
            )

    print(
        json.dumps(
            result,
            separators=(",", ":"),
        )
    )

def main():
    parser = argparse.ArgumentParser(
        description="Nateks NXI-3030 Legacy Adapter"
    )

    parser.add_argument(
        "ip",
        help="IP address of legacy NXI-3030",
    )

    group = parser.add_mutually_exclusive_group(
        required=True
    )

    group.add_argument(
        "--discovery",
        action="store_true",
        help="Output VLAN discovery JSON",
    )

    group.add_argument(
        "--vlan",
        type=int,
        metavar="VLAN_ID",
        help="Output bitmap for VLAN",
    )
    
    group.add_argument(
        "--membership",
        nargs=2,
        type=int,
        metavar=("VLAN_ID", "PORT"),
        help="Output Tagged/Untagged membership for VLAN port",
    )
    
    group.add_argument(
        "--membership-discovery",
        type=int,
        metavar="VLAN_ID",
        help="Output Zabbix LLD for VLAN port membership",
    )

    group.add_argument(
        "--membership-discovery-all",
        action="store_true",
        help="Output Zabbix LLD for all VLAN port memberships",
    )

    args = parser.parse_args()

    session = create_session(
        args.ip
    )

    if args.discovery:
        discovery(
            session,
            args.ip,
        )

    elif args.vlan is not None:
        vlan_value(
            session,
            args.ip,
            args.vlan,
        )
    
    elif args.membership is not None:
        membership_value(
            session,
            args.ip,
            args.membership[0],
            args.membership[1],
        )
        
    elif args.membership_discovery is not None:
        membership_discovery(
            session,
            args.ip,
            args.membership_discovery,
        )
        
    elif args.membership_discovery_all:
        membership_discovery_all(
            session,
            args.ip,
        )




if __name__ == "__main__":
    main()