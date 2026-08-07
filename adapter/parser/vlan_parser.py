from bs4 import BeautifulSoup

class VLANParser:
    def vlan_ids(self,html:str):
        soup=BeautifulSoup(html,"html.parser")
        text=soup.get_text(" ")
        return sorted(set(int(x) for x in __import__("re").findall(r"\b\d+\b",text) if 1<=int(x)<=4094))
