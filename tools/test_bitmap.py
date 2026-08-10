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
    """
    Convert VLAN port membership to the 2-byte bitmap
    used by the new Nateks firmware.

    tagged and untagged contain port numbers.
    Both types of membership are represented by the same bit.
    """

    bitmap = 0

    for port in set(tagged) | set(untagged):
        if port not in PORT_BITS:
            raise ValueError(f"Unsupported port: {port}")

        bitmap |= PORT_BITS[port]

    return f"{bitmap >> 8:02X} {bitmap & 0xFF:02X}"


tests = [
    ("VLAN 1", [], [5, 6, 7, 8, 9]),
    ("VLAN 15", [7, 8, 9], [4]),
    ("VLAN 20", [7, 8, 9], [1]),
    ("VLAN 30", [7, 8, 9], []),
    ("VLAN 40", [7, 8, 9], [2]),
    ("VLAN 50", [7, 8, 9], [3]),
    ("VLAN 60", [7, 8, 9], []),
    ("VLAN 150", [7, 8, 9], []),
    ("VLAN 777", [7, 8, 9], []),
]


for name, tagged, untagged in tests:
    print(
        f"{name:10} -> "
        f"{encode_vlan_bitmap(tagged, untagged)}"
    )