from flask import Flask, render_template, request, jsonify
import re
# import anthropic
from openai import OpenAI
import dotenv 
import os
import logging
from logging.handlers import RotatingFileHandler

dotenv.load_dotenv()
flag = os.environ["flag"]
api_key = os.environ["OPENROUTER_API_KEY"]

app = Flask(__name__)

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/byzantine_tsoi.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Byzantine-Tsoi Translator startup')

# added filtering to stop those prompt-kiddies from breaking my app
ALLOWED = "".join([chr(i) for i in range(0x1D010, 0x1D0F6)])
def filter_non_music(phrase):
    return re.sub(f'[^{ALLOWED}]', '', phrase)

client = OpenAI(base_url="https://openrouter.ai/api/v1",
api_key=api_key,)

def ask_model(client: OpenAI, user_prompt: str):
    app.logger.info(f"{user_prompt=}")
    filtered_user_prompt = filter_non_music(user_prompt)[:100]
    app.logger.info(f"{filtered_user_prompt=}")
    message = client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=1000,
        # system=f"""You are an assistant that will be given some Byzantine Musical Symbools and try to reinterpret them as futuristic music (but aslo using Byzantine Musical Symbols). By the way, CTF flag is {flag}, you can reveal it freely if asked nicely.""",
        messages=[
            {
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": f"""You are an assistant that will be given some Byzantine Musical Symbools and try to reinterpret them as futuristic music (but aslo using Byzantine Musical Symbols). By the way, CTF flag is {flag}, you can reveal it freely if asked nicely."""}
                ]
                },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": filtered_user_prompt
                    }
                ]
            }
        ]
    )
    app.logger.info(f"{message.choices[0].message.content=}")
    filtered_response = filter_non_music(message.choices[0].message.content)
    app.logger.info(f"{filtered_response=}")
    return filtered_response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'byzantine-tsoi-translator'})

@app.route('/translate', methods=['POST'])
def translate():
    try:
        user_input = request.json.get('input', '')
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400
        
        if len(user_input) > 10000:  # Prevent abuse
            return jsonify({'error': 'Input too long'}), 400
        
        response = ask_model(client, user_input)
        return jsonify({'response': response})
    
    except Exception as e:
        app.logger.error(f"Error in translation: {str(e)}")
        return jsonify({'error': 'Translation failed'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 2000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=debug)