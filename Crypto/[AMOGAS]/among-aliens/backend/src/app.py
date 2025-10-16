from flask import Flask, jsonify, send_file, render_template, session, request
from flask_cors import CORS
import random
import os
import uuid
from datetime import timedelta
import secrets
import requests
import json

app = Flask(__name__, static_url_path='', static_folder='', template_folder='')
app.secret_key = secrets.token_hex(16)
app.config['SESSION_COOKIE_NAME'] = 'alien_game_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

MATRIX_SERVICE_URL = "http://generate-matrix:5001"
LEVELS = 256
FLAG_TEXT = os.getenv('FLAG_TEXT', "THIS_IS_NOT_REAL_FLAG_TRY_HARDER")

CORS(app, 
     supports_credentials=True,
     origins=["http://localhost:5000", "http://127.0.0.1:5000", "http://0.0.0.0:5000", "http://10.63.0.102:5000", "http://10.63.0.200:11000", "https://cyberctf.tech:11000"],
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS"])

game_sessions = {}

def get_or_create_session(is_new):
    session_id = session.get('session_id')
    
    if not is_new and session_id and session_id in game_sessions:
        return game_sessions[session_id]
    
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    session.permanent = True

    try:
        response = requests.get(url=f"{MATRIX_SERVICE_URL}/generate/{session_id}")
        levels = []

        if response.status_code == 200:
            jr = response.json()

            if jr and 'status' in jr and jr['status'] == 'success':
                with open(f'/app/matrix-data/{session_id}.json', 'r') as file:
                    data = json.load(file)

                for i in range(LEVELS):
                    doors_count = data['levels'][i]
                    is_dark = random.random() < 0.2
                    has_runner = random.random() < 0.05
                    correct_door = random.randint(1, doors_count)
                    
                    levels.append({
                        'level': i + 1,
                        'doors_count': doors_count,
                        'is_dark': is_dark,
                        'has_runner': has_runner,
                        'correct_door': correct_door
                    })
        
        game_sessions[session_id] = {
            'current_game': levels,
            'player_level': 0,
            'alien_chance': 0
        }
    except Exception as e:
        print(f"ERROR: {e}")
        
    return game_sessions[session_id]

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/game/start', methods=['GET'])
def start_game():
    game_data = get_or_create_session(True)
    
    return jsonify({
        'message': 'Game started', 
        'total_levels': len(game_data['current_game']),
        'session_id': session.get('session_id')
    })

@app.route('/api/game/level/<int:level>', methods=['GET'])
def get_level(level):
    game_data = get_or_create_session(False)
    
    if level < 1 or level > len(game_data['current_game']):
        return jsonify({'error': 'Invalid level'}), 404
    
    level_data = game_data['current_game'][level-1].copy()
    del level_data['correct_door']
    return jsonify(level_data)

@app.route('/api/game/select_door/<int:level>/<int:door>', methods=['POST'])
def select_door(level, door):
    game_data = get_or_create_session(False)
    print(f"PLAYER_LVL: {game_data['player_level']}")
    
    if level != game_data['player_level'] + 1:
        print('Cheater!')
        return jsonify({'error': 'Cheater!'}), 400
    
    level_data = game_data['current_game'][level-1]
    is_correct = door == level_data['correct_door']
    
    if not is_correct:
        game_data['alien_chance'] = min(game_data['alien_chance'] + 0.05, 1.0)
    
    game_data['player_level'] += 1
    alien_encounter = False

    if game_data['alien_chance'] > 0 and random.random() < game_data['alien_chance']:
        alien_encounter = True
        game_data['alien_chance'] = 0
    
    game_completed = game_data['player_level'] == LEVELS
    response = {
        'correct': is_correct,
        'runner_appears': level_data['has_runner'],
        'alien_encounter': alien_encounter,
        'game_completed': game_completed,
        'alien_chance': game_data['alien_chance']
    }

    if game_completed:
        if game_data['alien_chance'] < 0.05:
            response['flag'] = f"flag{FLAG_TEXT}"
        else:
            response['flag'] = 'LUCKER!!!'
    
    return jsonify(response)

@app.route('/api/game/status', methods=['GET'])
def get_game_status():
    game_data = get_or_create_session(False)
    return jsonify({
        'current_level': game_data['player_level'],
        'total_levels': len(game_data['current_game']),
        'alien_chance': game_data['alien_chance']
    })

@app.route('/api/images/<path:filename>')
def get_image(filename):
    return send_file(f'/app/images/{filename}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)