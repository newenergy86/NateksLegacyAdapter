from dataclasses import dataclass, field
@dataclass
class VLAN:
    vid:int
    tagged:list[int]=field(default_factory=list)
    untagged:list[int]=field(default_factory=list)
