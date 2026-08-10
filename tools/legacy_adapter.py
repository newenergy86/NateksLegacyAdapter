import argparse
import json
import re

import requests
from bs4 import BeautifulSoup


IP = "10.0.110.28"
LOGIN = "admin"
PASSWORD = "1q2w3e4r"


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
    bitmap = 0

    for port in set(tagged) | set(untagged):
        if port not in PORT_BITS:
            raise ValueError(f"Unsupported port: {port}")

        bitmap |= PORT_BITS[port]

    return f"{bitmap >> 8:02X} {bitmap & 0xFF:02X}"


def login(session):
    response = session.post(
        f"http://{IP}/goform/SetSigninInfo",
        data={
            "userName": LOGIN,
            "password": PASSWORD,
            "language": "3",
            "result": "1",
        },
    )

    response.raise_for_status()


def get_vlan_ids(session):
    response = session.get(f"http://{IP}/vlan.asp")
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


def get_vlan_config(session, vlan_id):
    response = session.get(
        f"http://{IP}/vlan_show.asp?vlanid={vlan_id}"
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

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


def create_session():
    session = requests.Session()
    login(session)
    return session


def discovery(session):
    vlan_ids = get_vlan_ids(session)

    result = []

    for vlan_id in vlan_ids:
        result.append(
            {
                "{#VLANID}": str(vlan_id)
            }
        )

    print(json.dumps(result, separators=(",", ":")))


def vlan_value(session, vlan_id):
    vlan_ids = get_vlan_ids(session)

    vlan_ids = [int(vlan) for vlan in vlan_ids]

    if vlan_id not in vlan_ids:
        raise ValueError(f"VLAN {vlan_id} not found")

    tagged, untagged = get_vlan_config(
        session,
        vlan_id,
    )

    bitmap = encode_vlan_bitmap(
        tagged,
        untagged,
    )

    print(bitmap)


def main():
    parser = argparse.ArgumentParser(
        description="Nateks NXI-3030 legacy VLAN adapter"
    )

    parser.add_argument(
        "--discovery",
        action="store_true",
        help="Output VLAN discovery JSON",
    )

    parser.add_argument(
        "--vlan",
        type=int,
        help="Return bitmap for VLAN",
    )

    args = parser.parse_args()

    if not args.discovery and args.vlan is None:
        parser.error(
            "Specify --discovery or --vlan VLAN_ID"
        )

    session = create_session()

    if args.discovery:
        discovery(session)

    elif args.vlan is not None:
        vlan_value(session, args.vlan)


if __name__ == "__main__":
    main()