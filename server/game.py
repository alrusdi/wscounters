import datetime
import os
import uuid
from dataclasses import dataclass, field

from dataclasses_json import DataClassJsonMixin

from server.game_results import GameResults, GameResultsManager
from server.models.game_event import GameEvent, GameEventTypeEnum
from server.models.game_request import GameEventRequest
from server.models.player import Player
from server.settings import DEFAULT_TIMEZONE

SAVE_GAMES_DIR = "server/data/games"
TWO_PLAYERS = 2

@dataclass
class Game(DataClassJsonMixin):
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_finished: bool = False
    events: list[GameEvent] = field(default_factory=list)
    players: list[Player] = field(default_factory=list)

    def add_event(self, event: GameEvent) -> bool:
        if len(self.events):
            last_event = self.events[-1]
            if event.event_type == GameEventTypeEnum.END_BREAK and last_event.event_type == GameEventTypeEnum.END_BREAK:
                return False
        self.events.append(event)
        return True

    def undo_last_event(self) -> None:
        self.events = self.events[:-1]

    def calc_players(self) -> dict[str, Player]:
        results_map: dict[str, Player] = {}
        foul_counts: dict[str, int] = {}
        breaks: dict[str, list[int]] = {}
        self._calc_points_and_fouls(results_map, foul_counts, breaks)

        current_break, current_break_player_id = self._calc_breaks(breaks)

        if current_break and current_break_player_id in results_map:
            breaks[current_break_player_id].append(current_break)
            results_map[current_break_player_id].current_break = current_break

        player_ids = list(results_map.keys())
        for player_id, player in results_map.items():
            if len(player_ids) == TWO_PLAYERS:
                other_player_id = [pid for pid in player_ids if pid !=player_id][0]
                results_map[other_player_id].fouls = foul_counts.get(player_id, 0)
            else:
                player.fouls = foul_counts.get(player_id, 0)

        return results_map

    def _calc_points_and_fouls(
            self, results_map: dict[str, Player], foul_counts: dict[str, int], breaks: dict[str, list[int]],
        ) -> None:
        for ev in self.events:
            if not ev.player_id or ev.event_type != GameEventTypeEnum.COUNT:
                continue
            if ev.player_id not in results_map:
                results_map[ev.player_id] = Player(
                    id=ev.player_id,
                    name="",
                )
                foul_counts[ev.player_id] = 0
                breaks[ev.player_id] = []

            results_map[ev.player_id].points += (ev.value_integer or 0)
            if ev.is_foul:
                foul_counts[ev.player_id] += 1

    def _calc_breaks(self, breaks: dict[str, list[int]]) -> tuple[int, str]:
        current_break = 0
        current_break_player_id = ""
        for ev in self.events:
            if ev.event_type != GameEventTypeEnum.COUNT or not ev.player_id:
                if current_break:
                    breaks[current_break_player_id].append(current_break)
                current_break = 0
                continue
            if current_break_player_id and current_break_player_id != ev.player_id:
                if current_break:
                    breaks[current_break_player_id].append(current_break)
                current_break = 0
            current_break_player_id = ev.player_id

            if ev.value_integer and ev.value_integer > 0 and not ev.is_foul:
                current_break += ev.value_integer
        return current_break, current_break_player_id


    def get_date(self) -> datetime.datetime:
        for ev in self.events:
            if ev.started_at:
                return ev.started_at
        return datetime.datetime.now(DEFAULT_TIMEZONE)



class GameManager:
    def __init__(self) -> None:
        self.games: dict[str, Game] = {}

    async def create_new_game(self) -> Game:
        game = Game()
        await self.save_game(game)
        return game

    async def save_game(self, game: Game) -> None:
        self.games[game.id] = game
        data_raw = game.to_json(ensure_ascii=False, indent=4)
        with open(f"{SAVE_GAMES_DIR}/game_{game.id}.json", "w", encoding="utf8") as f:
            f.write(data_raw)

    async def get_game(self, game_id: str) -> Game | None:
        if game_id in self.games:
            return self.games[game_id]

        if os.path.exists(f"{SAVE_GAMES_DIR}/game_{game_id}.json"):
            with open(f"{SAVE_GAMES_DIR}/game_{game_id}.json") as f:
                raw_game_data = f.read()
                game = Game.from_json(raw_game_data)
                self.games[game_id] = game
                return game

        return None

    async def is_game_exists(self, game_id: str) -> bool:
        if game_id in self.games:
            return True

        if os.path.exists(f"{SAVE_GAMES_DIR}/game_{game_id}.json"):
            return True

        return False

    async def push_game_event(self, game: Game, event: GameEventRequest) -> None:
        game_event: GameEvent | None = None
        save_game = True

        if event.message_type in [GameEventTypeEnum.COUNT, GameEventTypeEnum.END_BREAK]:
            game_event = GameEvent(
                game_id=game.id,
                event_type=event.message_type,
                value_integer=event.value_integer,
                id=event.id,
                started_at=datetime.datetime.now(DEFAULT_TIMEZONE),
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

    async def finalize_game(self, game: Game, game_results_manager: GameResultsManager) -> GameResults:
        game.is_finished = True
        await self.save_game(game)

        players = sorted(game.calc_players().values(), key=lambda x: x.points, reverse=True)

        game_results = GameResults(
            game_id=game.id,
            game_date=game.get_date(),
            player_stats=players,
        )

        await game_results_manager.save_game_results(game_results)
        return game_results
