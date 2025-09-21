import pytest
from app import create_app

@pytest.fixture
def client():
    # Use a test config if you had one, for now, default is fine
    app = create_app()
    app.config['TESTING'] = True
    # In-memory SQLite for testing if needed, but we'll test API logic
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert rv.data == b'OK'

def test_start_game(client):
    """Test the start game endpoint."""
    with client.session_transaction() as sess:
        # Ensure session is clear before starting
        sess.clear()

    rv = client.post('/api/start_game')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert 'word_display' in json_data
    assert not json_data['game_over']

    with client.session_transaction() as sess:
        assert 'word' in sess
        assert 'guesses' in sess