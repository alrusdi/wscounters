import datetime
import json
import os
from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin

from server.models.player import Player
from server.settings import BASE_DIR

SAVE_GAME_RESULTS_DIR = "server/data/results"

@dataclass
class GameResults(DataClassJsonMixin):
    game_id: str
    game_date: datetime.datetime
    player_stats: list[Player]


class GameResultsManager:
    def __init__(self) -> None:
        self.results: dict[str, GameResults] = {}

    async def is_game_results_exists(self, game_id: str) -> bool:
        if game_id in self.results:
            return True

        if os.path.exists(f"{SAVE_GAME_RESULTS_DIR}/result_{game_id}.json"):
            return True

        return False

    async def get_game_results(self, game_id: str) -> GameResults | None:
        if game_id in self.results:
            return self.results[game_id]

        if os.path.exists(f"{SAVE_GAME_RESULTS_DIR}/result_{game_id}.json"):
            with open(f"{SAVE_GAME_RESULTS_DIR}/result_{game_id}.json", encoding="utf8") as f:
                raw_game_results_data = f.read()
                results = GameResults.from_json(raw_game_results_data)
                self.results[game_id] = results
                return results
        return None

    async def save_game_results(self, game_results: GameResults) -> None:
        self.results[game_results.game_id] = game_results
        with open(f"{BASE_DIR}/client/common.js", encoding="utf8") as f:
            raw_data = f.read().replace("const POSSIBLE_PLAYERS = ", "")
            player_names = {p["id"]: p["name"] for p in json.loads(raw_data)}
        for pstat in game_results.player_stats:
            if not pstat.name and pstat.id and pstat.id in player_names:
                pstat.name = player_names[pstat.id]
        data_raw = game_results.to_json(ensure_ascii=False, indent=4)
        with open(f"{SAVE_GAME_RESULTS_DIR}/result_{game_results.game_id}.json", "w", encoding="utf8") as f:
            f.write(data_raw)
