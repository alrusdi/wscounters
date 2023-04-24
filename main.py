import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from server.game import GameManager
from server.models.game_event import GameEventTypeEnum
from server.models.game_request import GameEventRequest

from server.ws_connection_manager import WsConnectionManager
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles

app = FastAPI()
manager = WsConnectionManager()
game_manager = GameManager()


app.mount("/static", StaticFiles(directory="client"), name="static")

@app.get("/")
async def main_page():
    with open('client/index.html', encoding='utf8') as f:
        html = f.read()
    return HTMLResponse(html)

@app.post('/create-new-game/')
async def create_game_handler():
    new_game = await game_manager.create_new_game()
    return {"status": "Ok", "game_id": new_game.id}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            event = parse_ws_request(data)
            players_data = {}
            if event.game_id:
                game = await game_manager.get_game(event.game_id)
                if game:
                    await game_manager.push_game_event(game, event)
                    players_data = game.calc_players()

            await manager.broadcast(_to_message(jsonable_encoder(players_data)), current_websocket=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(_to_message(f"Client #{client_id} left the chat"))
    except KeyboardInterrupt:
        raise
    except:
        import traceback
        print(traceback.format_exc())
        await manager.broadcast(_to_message("Server error"))


def parse_ws_request(data: str) -> GameEventRequest:
    try:
        print(data)
        req = GameEventRequest.from_json(data)
        print(req)
        return req
    except:
        import traceback
        print(traceback.format_exc())
        return GameEventRequest(
            message_type=GameEventTypeEnum.ERROR,
            value_string='Unable to parse input json'
        )

def _to_message(data):
    return json.dumps({
        'message': data
    })