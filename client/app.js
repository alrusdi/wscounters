var ws = null;

function sendMessage(msg) {
    const data = {
        "message_type": msg.messageType,
        "game_id": msg.gameId,
        "player_id": msg.playerId,
        "value_integer": msg.integerValue,
        "value_string": msg.stringValue,
        "is_foul": msg.isFoul
    }
    if (ws) {
        ws.send(JSON.stringify(data))
    }
}

const SnookerScoreKeeper = {
    delimiters: ["[[", "]]"],
    mounted () {
        M.AutoInit()
        M.Sidenav.init(document.querySelectorAll('.sidenav'), {});
    },
    created() {
        const app = this;
        const host = window.location.host.toString();
        const protocol = window.location.protocol == 'https:' ? 'wss': 'ws'
        ws = new WebSocket(`${protocol}://${host}/ws/${this.clientId}`);

        ws.onmessage = (event) => {
            var results = JSON.parse(event.data)
            if (results.status != 'players') {
                console.log(results.message);
                return
            }
            players_data_map = results.message
            for (player of app.players) {
                pdata = players_data_map[player.id]
                if (pdata) {
                    player.points = pdata.points
                    player.current_break = pdata.current_break
                    player.max_break = pdata.max_break
                }
            }
        };

        ws.onopen = () => {
            sendMessage({
                messageType: 'init',
                gameId: app.gameId,
                playerId: app.currentPlayerId,
                integerValue: null,
                stringValue: null,
                isFoul: false
            })
        }
    },

    data() {
        const urlParams = new URLSearchParams(window.location.search);
        const clientId = Date.now()
        const gameId = urlParams.get("gid")
        const pset = urlParams.get("pset") || '01'
        const players = []
        for (playerIndex of pset) {
            playerIndex = parseInt(playerIndex)
            players.push(POSSIBLE_PLAYERS[playerIndex])
        }

        
        return {
            foulMode: false,
            clientId: clientId,
            gameId: gameId,
            currentPlayerId: '09eabde7-3a21-43f6-b197-c75452e7c214',
            buttons: [
                {label: '1', style: 'evt-btn-red', value: 1, group: 'default', action: 'count', disabled: false},
                {label: '2', style: 'evt-btn-yellow', value: 2, group: 'default', action: 'count', disabled: false},
                {label: '3', style: 'evt-btn-green', value: 3, group: 'default', action: 'count', disabled: false},
                {label: '4', style: 'evt-btn-brown', value: 4, group: 'foul', action: 'count', disabled: false},
                {label: '5', style: 'evt-btn-blue', value: 5, group: 'foul', action: 'count', disabled: false},
                {label: '6', style: 'evt-btn-pink', value: 6, group: 'foul', action: 'count', disabled: false},
                {label: '7', style: 'evt-btn-black', value: 7, group: 'foul', action: 'count', disabled: false},
                {label: 'Отмена', style: 'evt-btn-back', value: 0, group: 'bottom', action: 'undo', disabled: false},
                {label: 'Закончить серию', style: 'evt-btn-end-brake', value: null, group: 'bottom', action: 'end_break', disabled: false},
            ],
            players
        }
    },
    computed: {
        countButtons() {
            return this.buttons.filter((b) => b.group == 'default' || b.group == 'foul')
        },
        bottomButtons() {
            return this.buttons.filter((b) => b.group == 'bottom')
        },
    },
    methods: {
        onUiEvent(messageType, integerValue) {
            const currentPlayerId = document.querySelector('input[name=player]:checked').value
            this.currentPlayerId = currentPlayerId
            if (this.foulMode && integerValue && this.players.length > 2) {
                integerValue = -integerValue
            }
            msg = {
                messageType,
                integerValue: integerValue || null,
                gameId: this.gameId,
                playerId: currentPlayerId,
                stringValue: null,
                isFoul: this.foulMode
            }
            sendMessage(msg)
            this.foulMode = false
        },
        activateNextPlayer() {
            this.currentPlayerId = this.getNextPlayerId()
        },
        getNextPlayerId() {
            const currentPlayerId = this.currentPlayerId
            const playersCount = this.players.length
            if (playersCount < 2) return currentPlayerId;

            
            var currentPlayerIndex = -1;

            for (var idx in this.players) {
                if (this.players[idx].id == currentPlayerId) {
                    currentPlayerIndex = parseInt(idx);
                    break
                }
            }
     
            if (currentPlayerIndex > -1) {
                nextPlayerIndex = (playersCount > currentPlayerIndex + 1) ? currentPlayerIndex + 1 : 0
                return this.players[nextPlayerIndex].id
            }
            return currentPlayerId
        }
    }
}

Vue.createApp(SnookerScoreKeeper).mount('#snooker-score-keeper')
