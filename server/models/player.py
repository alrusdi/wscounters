from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Player:
    id: str
    name: str
    points: int = 0
    max_break: int = 0
    current_break: int = 0
    fouls: int = 0
