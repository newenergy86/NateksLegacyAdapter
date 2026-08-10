import re
import random
import requests
from bs4 import BeautifulSoup

IP = "10.0.110.39"
LOGIN = "admin"
PASSWORD = "1q2w3e4r"

s = requests.Session()

print("Получаю страницу авторизации...")

r = s.get(f"http://{IP}/login.htm")

print("LOGIN:", r.status_code)

# Браузер перед login() создаёт cookie seid
s.cookies.set("seid", str(random.randint(1, 10)))

verify = input("Введите код с картинки: ").strip().lower()

print("Авторизация...")

r = s.post(
    f"http://{IP}/stat/login",
    data={
        "user": LOGIN,
        "pwd": PASSWORD,
        "verify": verify,
        "ssltype": "0"
    },
    allow_redirects=True
)

print("POST:", r.status_code)
print("URL:", r.url)

print()
print("COOKIES:")
for cookie in s.cookies:
    print(" ", cookie.name, "=", cookie.value)

print()
print("Проверяю index.htm...")

r = s.get(f"http://{IP}/index.htm")

print("INDEX:", r.status_code)
print("INDEX URL:", r.url)
print("INDEX SIZE:", len(r.text))

# Сохраняем страницу для исследования
with open("index_after_login.html", "w", encoding="utf-8") as f:
    f.write(r.text)

print()
print("Ищу ссылки на VLAN...")

for match in re.findall(
    r'(?:href|src)\s*=\s*["\']([^"\']+)["\']',
    r.text,
    re.IGNORECASE
):
    if "vlan" in match.lower():
        print("VLAN:", match)

print()
print("Ищу слова vlan в HTML...")

for line in r.text.splitlines():
    if "vlan" in line.lower():
        print(line[:300])

print()
print("Готово.")
print("Файл сохранён:")
print("index_after_login.html")

print()
print("=" * 60)
print("ПОЛУЧАЮ КОНФИГУРАЦИЮ VLAN НОВОЙ ПРОШИВКИ")

r = s.get(f"http://{IP}/config/vlan")

print("STATUS:", r.status_code)
print("URL:", r.url)
print("SIZE:", len(r.text))

print()
print("RAW RESPONSE:")
print(r.text)

with open("vlan_config_response.txt", "w", encoding="utf-8") as f:
    f.write(r.text)

print()
print("Ответ сохранён в vlan_config_response.txt")