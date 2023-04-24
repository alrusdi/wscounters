import datetime
import uuid
from enum import Enum
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


class GameEventTypeEnum(Enum):
    START_GAME = 'start_game'
    MESSAGE = 'message'
    COUNT = 'count'
    ERROR = 'error'
    UNDO = 'undo'
    END_BREAK = 'end_break'
    INIT = 'init'

@dataclass_json
@dataclass
class GameEvent:
    game_id: str
    event_type: GameEventTypeEnum
    started_at: datetime.datetime
    value_string: str | None = None
    value_integer: int | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str | None = None
    is_foul: bool = False
