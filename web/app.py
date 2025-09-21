import os
import random
from flask import Flask, jsonify, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from config import Config
from azure.identity import DefaultAzureCredential
import struct

# --- Database Setup ---
db = SQLAlchemy()

class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# List of words for the game
WORDS = ["PYTHON", "AZURE", "DOCKER", "TERRAFORM", "FLASK", "DEVOPS", "GITHUB"]

# --- Application Factory ---
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Azure AD Token Injection for SQLAlchemy ---
    # If running in Azure, intercept DB connections to inject an AD token.
    # This is the core of the passwordless architecture.
    if app.config['IS_AZURE']:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "before_connect", once=True)
        def before_connect(dbapi_connection, connection_record):
            credential = DefaultAzureCredential(exclude_shared_cache_credential=True)
            token_bytes = credential.get_token("https://ossrdbms-aad.database.windows.net/.default").token.encode("UTF-16-LE")
            # See: https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-connect-azure-ad#connecting-with-python
            token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
            dbapi_connection.info.password = token_struct

    db.init_app(app)

    with app.app_context():
        db.create_all() # Create tables if they don't exist

    @app.route("/")
    def index():
        """Serve the main game page."""
        return render_template("index.html")

    @app.route("/api/health")
    def health_check():
        """Health check endpoint for smoke tests."""
        return "OK", 200

    @app.route("/api/start_game", methods=["POST"])
    def start_game():
        """Starts a new game."""
        word = random.choice(WORDS)
        session['word'] = word
        session['guesses'] = []
        session['wrong_attempts'] = 0
        
        game_state = {
            'word_display': ['_' for _ in word],
            'wrong_attempts': 0,
            'game_over': False,
            'message': 'New game started! Guess a letter.'
        }
        return jsonify(game_state)

    @app.route("/api/guess", methods=["POST"])
    def guess():
        """Handles a player's guess."""
        if 'word' not in session:
            return jsonify({'error': 'Game not started'}), 400

        guess = request.json.get('letter', '').upper()
        word = session['word']
        guesses = session['guesses']
        
        if not guess.isalpha() or len(guess) != 1:
            return jsonify({'error': 'Invalid guess'}), 400

        if guess in guesses:
            message = f"You already guessed '{guess}'."
        elif guess in word:
            message = f"Good guess! '{guess}' is in the word."
            guesses.append(guess)
        else:
            message = f"Sorry, '{guess}' is not in the word."
            guesses.append(guess)
            session['wrong_attempts'] += 1

        session['guesses'] = guesses

        # --- Update Game State ---
        word_display = [letter if letter in guesses else '_' for letter in word]
        wrong_attempts = session['wrong_attempts']
        game_over = '_' not in word_display or wrong_attempts >= 6
        win = '_' not in word_display

        score = 0
        if win:
            message = "Congratulations, you won!"
            # Simple score: 100 - 10 per wrong attempt
            score = max(10, 100 - (wrong_attempts * 10))
        elif game_over:
            message = f"Game over! The word was {word}."

        return jsonify({
            'word_display': word_display,
            'wrong_attempts': wrong_attempts,
            'guesses': guesses,
            'game_over': game_over,
            'win': win,
            'score': score,
            'message': message
        })

    @app.route("/api/scores", methods=["GET", "POST"])
    def high_scores():
        """Handles fetching and submitting high scores."""
        if request.method == "POST":
            player_name = request.json.get("player_name")
            score = request.json.get("score")
            if player_name and score:
                new_score = HighScore(player_name=player_name, score=score)
                db.session.add(new_score)
                db.session.commit()
        
        # Fetch top 10 scores
        scores = HighScore.query.order_by(HighScore.score.desc()).limit(10).all()
        return jsonify([
            {"player_name": s.player_name, "score": s.score} for s in scores
        ])

    return app