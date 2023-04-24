import datetime
import os
import uuid

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from server.models.game_event import GameEvent, GameEventTypeEnum
from server.models.game_request import GameEventRequest
from server.models.player import Player

SAVE_GAMES_DIR = 'server/data/games'


@dataclass_json
@dataclass
class Game:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: list[GameEvent] = field(default_factory=list)
    players: list[Player] = field(default_factory=list)
    
    def add_event(self, event: GameEvent) -> bool:
        if len(self.events):
            last_event = self.events[-1]
            if event.event_type == GameEventTypeEnum.END_BREAK and last_event.event_type == GameEventTypeEnum.END_BREAK:
                return False
        self.events.append(event)
        return True
    
    def undo_last_event(self):
        self.events = self.events[:-1]
    
    def calc_players(self) -> dict[str, Player]: 
        results_map: dict[str, Player] = {}
        for ev in self.events:
            if not ev.player_id or not ev.event_type == GameEventTypeEnum.COUNT:
                continue
            if ev.player_id not in results_map:
                results_map[ev.player_id] = Player(
                    id=ev.player_id,
                    name='',
                )
            
            results_map[ev.player_id].points += ev.value_integer
        
        current_break = 0
        current_break_player_id = ''
        for ev in reversed(self.events):
            if ev.event_type != GameEventTypeEnum.COUNT:
                break
            if current_break_player_id and current_break_player_id != ev.player_id:
                break
            current_break_player_id = ev.player_id
            if ev.value_integer > 0:
                current_break += ev.value_integer
        
        if current_break and current_break_player_id in results_map:
            results_map[current_break_player_id].current_break = current_break
        return results_map



class GameManager:
    def __init__(self):
        self.games: map[str, Game] = {}
    
    async def create_new_game(self) -> Game:
        game = Game()
        await self.save_game(game)
        self.games[game.id] = game
        return game
    
    async def save_game(self, game: Game) -> None:
        data_raw = game.to_json()
        with open(f'{SAVE_GAMES_DIR}/game_{game.id}.json', 'w') as f:
            f.write(data_raw)
    
    async def get_game(self, game_id: str) -> Game | None:
        if game_id in self.games:
            return self.games[game_id]

        if os.path.exists(f'{SAVE_GAMES_DIR}/game_{game_id}.json'):
            with open(f'{SAVE_GAMES_DIR}/game_{game_id}.json') as f:
                raw_game_data = f.read()
                game = Game.from_json(raw_game_data)
                self.games[game_id] = game
                return game
    
    async def push_game_event(self, game: Game, event: GameEventRequest):
        game_event: GameEvent | None = None
        save_game = True

        if event.message_type in [GameEventTypeEnum.COUNT, GameEventTypeEnum.END_BREAK]:
            game_event = GameEvent(
                game_id=game.id,
                event_type=event.message_type,
                value_integer=event.value_integer,
                id=event.id,
                started_at=datetime.datetime.now(),
                player_id=event.player_id,
                is_foul=event.is_foul,
            )
        elif event.message_type == GameEventTypeEnum.UNDO:
            game.undo_last_event()
        else:
            save_game = False

        if game_event:
            event_added = game.add_event(game_event)
            if not event_added:
                save_game = False    
        
        if save_game:
            await self.save_game(game)
