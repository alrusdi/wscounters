import json
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from server.game import GameManager
from server.game_results import GameResultsManager
from server.models.game_event import GameEventTypeEnum
from server.models.game_request import GameEventRequest

from server.ws_connection_manager import WsConnectionManager
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
templtes = templates = Jinja2Templates(directory="server/templates")
manager = WsConnectionManager()
game_manager = GameManager()
game_results_manager = GameResultsManager()


app.mount("/static", StaticFiles(directory="client"), name="static")

@app.get("/play/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("play.jinja2", {"request": request})

@app.get("/new-game/", response_class=HTMLResponse)
def new_game_page(request: Request):
    return templates.TemplateResponse("new_game.jinja2", {"request": request})

@app.get("/game-results/{game_id}/", response_class=HTMLResponse)
async def game_results_page(request: Request, game_id:str):
    game_results = await game_results_manager.get_game_results(game_id=game_id)
    is_game_exists = await game_manager.is_game_exists(game_id=game_id)
    if not game_results and is_game_exists:
        game = await game_manager.get_game(game_id=game_id)
        if game:
            await game_manager.finalize_game(game, game_results_manager)
            game_results = await game_results_manager.get_game_results(game_id=game_id)

    if not game_results:
        raise HTTPException(status_code=404, detail="Item not found")
    return templates.TemplateResponse("game_results.jinja2", {"request": request, "game_results": game_results})

@app.post("/create-new-game/")
async def create_game_handler(request: Request):
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
                if game and not game.is_finished:
                    await game_manager.push_game_event(game, event)
                    players_data = game.calc_players()
                    await manager.broadcast(
                        _to_message(jsonable_encoder(players_data), status='players'),
                    )
                    continue

            await manager.broadcast(_to_message("Game not found", status='fail'))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(_to_message(f"Client #{client_id} left the chat", status='info'))
    except KeyboardInterrupt:
        raise
    except:
        import traceback
        print(traceback.format_exc())
        await manager.broadcast(_to_message("Server error", status='fail'))


def parse_ws_request(data: str) -> GameEventRequest:
    try:
        req = GameEventRequest.from_json(data)
        return req
    except:
        import traceback
        print(traceback.format_exc())
        return GameEventRequest(
            message_type=GameEventTypeEnum.ERROR,
            value_string='Unable to parse input json'
        )

def _to_message(data, status: str='ok'):
    return json.dumps({
        'status': status,
        'message': data,
    })
