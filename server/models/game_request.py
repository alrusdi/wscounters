import uuid
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from server.models.game_event import GameEventTypeEnum


@dataclass_json
@dataclass
class GameEventRequest:
    message_type: GameEventTypeEnum
    value_string: str | None = None
    value_integer: int | None = None
    game_id: str | None = None
    player_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_foul: bool = False
