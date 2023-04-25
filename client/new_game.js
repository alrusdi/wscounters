const SnookerScoreKeeperNewGameForm = {
    delimiters: ["[[", "]]"],
    mounted () {
        M.AutoInit()
        const modals = document.querySelectorAll('.modal');
        M.Modal.init(modals, {});
    },
    created() {
        const app = this;
    },
    data() {
        return {
            selectedPlayers: [],
            errorMessage: ''
        }
    },
    methods: {
        sendForm() {
            const app = this
            this.errorMessage = ''
            if (this.selectedPlayers.length < 2) {
                this.errorMessage = 'нужно выбрать хотя бы двух игроков'
                return
            }

            const playerIndices = [];
            for (var idx in POSSIBLE_PLAYERS) {
                player = POSSIBLE_PLAYERS[idx]
                if (this.selectedPlayers.includes(player.id)) {
                    playerIndices.push(String(idx))
                }
            }
            const pset = playerIndices.join('');
    
            const fetch_options = {
                method: "POST",
                cache: "no-cache",
                headers: {
                  "Content-Type": "application/json",
                }
            }

            fetch('/create-new-game/', fetch_options)
                .then(response => response.json())
                .then(result => {
                    window.location.href = `/play/?gid=${result.game_id}&pset=${pset}`
                })
                .catch((error) => {
                    app.errorMessage = 'не удалось создать игру'
                    console.log(error)
                });
        }
    }
}

Vue.createApp(SnookerScoreKeeperNewGameForm).mount('#new-game-form')
