import re
import requests
from bs4 import BeautifulSoup

IP = "10.0.110.28"
LOGIN = "admin"
PASSWORD = "1q2w3e4r"

s = requests.Session()

s.post(
    f"http://{IP}/goform/SetSigninInfo",
    data={
        "userName": LOGIN,
        "password": PASSWORD,
        "language": "3",
        "result": "1"
    }
)

# ---------- список VLAN ----------

html = s.get(f"http://{IP}/vlan.asp").text

vlans = sorted(set(re.findall(r"vlan_show\.asp\?vlanid=(\d+)", html)), key=int)

print("VLAN LIST:", vlans)

# ---------- читаем каждую VLAN ----------

for vlan in vlans:

    print("\n" + "=" * 50)
    print("VLAN", vlan)

    html = s.get(
        f"http://{IP}/vlan_show.asp?vlanid={vlan}"
    ).text

    soup = BeautifulSoup(html, "html.parser")

    for port in range(1, 10):

        checkbox = soup.find("input", {"name": f"select{port}", "type": "checkbox"})

        if checkbox is None:
            continue

        if not checkbox.has_attr("checked"):
            continue

        tagged = False
        untagged = False

        radios = soup.find_all("input", {"name": f"rate{port}"})

        for r in radios:

            if not r.has_attr("checked"):
                continue

            if r.get("value") == "1":
                tagged = True

            if r.get("value") == "2":
                untagged = True

        if tagged:
            print(f"Port {port}   Tagged")

        elif untagged:
            print(f"Port {port}   Untagged")

        else:
            print(f"Port {port}   Unknown")