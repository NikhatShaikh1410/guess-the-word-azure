document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-button');
    const guessButton = document.getElementById('guess-button');
    const guessInput = document.getElementById('guess-input');
    const wordDisplay = document.getElementById('word-display');
    const messageEl = document.getElementById('message');
    const highScoresList = document.getElementById('high-scores-list');

    const updateUI = (state) => {
        wordDisplay.textContent = state.word_display.join(' ');
        messageEl.textContent = state.message;
        if (state.game_over) {
            guessInput.disabled = true;
            guessButton.disabled = true;
            if (state.win) {
                const playerName = prompt("You won! Enter your name for the high score list:");
                if (playerName) {
                    submitScore(playerName, state.score);
                }
            }
        } else {
            guessInput.disabled = false;
            guessButton.disabled = false;
        }
    };

    const fetchHighScores = async () => {
        const response = await fetch('/api/scores');
        const scores = await response.json();
        highScoresList.innerHTML = '';
        scores.forEach(score => {
            const li = document.createElement('li');
            li.innerHTML = `<span>${score.player_name}</span><span>${score.score}</span>`;
            highScoresList.appendChild(li);
        });
    };

    const submitScore = async (playerName, score) => {
        await fetch('/api/scores', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ player_name: playerName, score: score }),
        });
        fetchHighScores();
    };

    const startGame = async () => {
        const response = await fetch('/api/start_game', { method: 'POST' });
        const state = await response.json();
        guessInput.value = '';
        updateUI(state);
    };

    const makeGuess = async () => {
        const letter = guessInput.value;
        if (!letter) return;
        const response = await fetch('/api/guess', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ letter: letter }),
        });
        const state = await response.json();
        guessInput.value = '';
        updateUI(state);
    };

    startButton.addEventListener('click', startGame);
    guessButton.addEventListener('click', makeGuess);
    guessInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') makeGuess();
    });

    // Initial load
    fetchHighScores();
    startGame();
});