import json
from pathlib import Path

class CacheManager:
    def __init__(self,file="cache.json"):
        self.file=Path(file)
    def save(self,data):
        self.file.write_text(json.dumps(data,indent=2),encoding="utf-8")
    def load(self):
        return json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}
