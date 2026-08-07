from dataclasses import dataclass
@dataclass
class Port:
    id:int
    pvid:int|None=None
    mode:str|None=None
