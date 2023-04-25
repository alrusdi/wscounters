import pytest
from server.game import Game
from server.tests.helpers import load_data

@pytest.mark.asyncio
async def test_game_calc_players():
    game = Game.from_json(load_data('game_02a1aeb0-4417-4536-9271-354032a138d7.json'))

    players = list(game.calc_players().values())

    assert players == []
