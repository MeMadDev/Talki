from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
import logging
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mock_secret_key'
logging.basicConfig(level=logging.INFO)

WEBHOOK_URL = 'http://localhost:8000/chatbridge/webhook/'
CHAT_DIR = 'mock_chats'

# Ensure chat directory exists
def ensure_chat_dir():
    if not os.path.exists(CHAT_DIR):
        os.makedirs(CHAT_DIR)

# List all phone numbers (files)
def list_numbers():
    ensure_chat_dir()
    numbers = []
    for f in os.listdir(CHAT_DIR):
        if f.endswith('.txt') and '__' in f:
            user, firm = f[:-4].split('__', 1)
            numbers.append({'user': user, 'firm': firm})
    return numbers

# Create a new number (file)
def create_number(user_number, firm_number):
    ensure_chat_dir()
    path = os.path.join(CHAT_DIR, f'{user_number}__{firm_number}.txt')
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write('')

# Append a message to a chat file
def append_message(user_number, firm_number, message, sent=True):
    ensure_chat_dir()
    path = os.path.join(CHAT_DIR, f'{user_number}__{firm_number}.txt')
    direction = 'SENT' if sent else 'RECEIVED'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'a') as f:
        f.write(f'{direction}: {message} [{timestamp}]\n')

# Get chat history for a number
def get_chat_history(user_number, firm_number):
    ensure_chat_dir()
    path = os.path.join(CHAT_DIR, f'{user_number}__{firm_number}.txt')
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return f.readlines()

# Find firm number for a user number (for /v1/messages)
def find_firm_number(user_number):
    ensure_chat_dir()
    for f in os.listdir(CHAT_DIR):
        if f.endswith('.txt') and f.startswith(f'{user_number}__'):
            return f[:-4].split('__', 1)[1]
    return None

# HTML template for the chat UI
HTML_CHAT = '''
<!doctype html>
<html lang="en">
<head>
<title>Mock WhatsApp Chat</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css?family=Roboto:400,500,700&display=swap" rel="stylesheet">
<style>
    body {
        font-family: 'Roboto', Arial, sans-serif;
        margin: 0;
        background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
        min-height: 100vh;
    }
    .header {
        background: linear-gradient(90deg, #075e54 60%, #25d366 100%);
        color: #fff;
        padding: 18px 32px;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: 1px;
        box-shadow: 0 2px 8px rgba(7,94,84,0.08);
        border-bottom-left-radius: 18px;
        border-bottom-right-radius: 18px;
        margin-bottom: 0;
    }
    .container {
        display: flex;
        max-width: 1100px;
        margin: 32px auto 0 auto;
        background: #fff;
        border-radius: 18px;
        box-shadow: 0 8px 32px rgba(7,94,84,0.10);
        overflow: hidden;
        min-height: 600px;
    }
    .sidebar {
        width: 270px;
        background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
        padding: 24px 0 24px 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        box-shadow: 2px 0 8px rgba(7,94,84,0.05);
    }
    .sidebar .number {
        width: 85%;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-radius: 8px;
        border: none;
        background: rgba(255,255,255,0.85);
        color: #075e54;
        font-weight: 500;
        font-size: 1.08rem;
        cursor: pointer;
        transition: background 0.2s, color 0.2s, box-shadow 0.2s;
        box-shadow: 0 2px 8px rgba(7,94,84,0.04);
        text-align: left;
        outline: none;
    }
    .sidebar .number.selected, .sidebar .number:hover {
        background: #075e54;
        color: #fff;
        box-shadow: 0 4px 16px rgba(7,94,84,0.10);
    }
    .sidebar .add-form {
        width: 85%;
        margin-top: 18px;
        display: flex;
        flex-direction: column;
        align-items: stretch;
    }
    .sidebar .add-form input {
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 6px;
        border: 1.5px solid #25d366;
        font-size: 1rem;
        outline: none;
        transition: border 0.2s;
    }
    .sidebar .add-form input:focus {
        border: 1.5px solid #075e54;
        background: #e0f7fa;
    }
    .sidebar .add-btn {
        background: linear-gradient(90deg, #25d366 60%, #075e54 100%);
        color: #fff;
        border: none;
        padding: 12px 0;
        border-radius: 6px;
        font-size: 1.08rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(7,94,84,0.08);
        transition: background 0.2s, box-shadow 0.2s;
    }
    .sidebar .add-btn:hover {
        background: linear-gradient(90deg, #075e54 60%, #25d366 100%);
        box-shadow: 0 4px 16px rgba(7,94,84,0.12);
    }
    .chat-area {
        flex: 1;
        padding: 0;
        display: flex;
        flex-direction: column;
        background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
    }
    .chat-box {
        flex: 1;
        padding: 32px 32px 16px 32px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 8px;
        background: transparent;
        min-height: 400px;
        max-height: 600px;
    }
    .chat-line {
        display: inline-block;
        max-width: 70%;
        padding: 12px 18px;
        border-radius: 18px;
        margin-bottom: 2px;
        font-size: 1.08rem;
        box-shadow: 0 2px 8px rgba(7,94,84,0.06);
        word-break: break-word;
        position: relative;
        animation: fadeIn 0.4s;
    }
    .chat-line.sent {
        align-self: flex-end;
        background: linear-gradient(90deg, #dcf8c6 60%, #b9f5d8 100%);
        color: #075e54;
        border-bottom-right-radius: 4px;
    }
    .chat-line.received {
        align-self: flex-start;
        background: linear-gradient(90deg, #fff 60%, #e0eafc 100%);
        color: #128c7e;
        border-bottom-left-radius: 4px;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .msg-form {
        display: flex;
        padding: 18px 32px 24px 32px;
        background: #fff;
        border-top: 1.5px solid #e0eafc;
        align-items: center;
        gap: 12px;
    }
    .msg-form input[type=text] {
        flex: 1;
        padding: 14px 16px;
        border: 2px solid #25d366;
        border-radius: 24px;
        font-size: 1.08rem;
        outline: none;
        transition: border 0.2s, background 0.2s;
        background: #f7f7f7;
    }
    .msg-form input[type=text]:focus {
        border: 2px solid #075e54;
        background: #e0f7fa;
    }
    .msg-form button {
        background: linear-gradient(90deg, #25d366 60%, #075e54 100%);
        color: #fff;
        border: none;
        padding: 12px 28px;
        border-radius: 24px;
        font-size: 1.08rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(7,94,84,0.10);
        transition: background 0.2s, box-shadow 0.2s, transform 0.1s;
        outline: none;
        position: relative;
        overflow: hidden;
    }
    .msg-form button:hover {
        background: linear-gradient(90deg, #075e54 60%, #25d366 100%);
        box-shadow: 0 4px 16px rgba(7,94,84,0.16);
        transform: translateY(-2px) scale(1.04);
    }
    ul { margin: 18px 0 0 0; padding: 0 32px; }
    li { color: #d32f2f; font-size: 1rem; margin-bottom: 4px; }
    @media (max-width: 900px) {
        .container { flex-direction: column; min-width: 0; }
        .sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; justify-content: flex-start; border-radius: 0; }
        .sidebar .number, .sidebar .add-form { width: 48%; margin: 1%; }
        .chat-area { padding: 0; }
        .chat-box { padding: 18px 8px 8px 8px; }
        .msg-form { padding: 12px 8px 16px 8px; }
    }
</style>
</head>
<body>
<div class="header">Mock WhatsApp Chat</div>
<div class="container">
    <div class="sidebar">
        {% for n in numbers %}
            <div class="number{% if n.user == selected_user and n.firm == selected_firm %} selected{% endif %}" onclick="window.location='/?user={{n.user}}&firm={{n.firm}}'">{{n.user}} ({{n.firm}})</div>
        {% endfor %}
        <form class="add-form" method="post" action="/add-number">
            <input type="text" name="new_user_number" placeholder="Enter user number" required>
            <input type="text" name="new_firm_number" placeholder="Enter firm number (display_phone_number)" required>
            <button class="add-btn" type="submit">+ Add Number</button>
        </form>
    </div>
    <div class="chat-area">
        <div class="chat-box" id="chat-box">
            {% if chat %}
                {% for line in chat %}
                    {% set direction = 'sent' if line.startswith('SENT:') else 'received' %}
                    {% set msg = line.split(':', 1)[1].rsplit('[', 1)[0].strip() if ':' in line and '[' in line else line %}
                    <div class="chat-line {{direction}}">{{msg}}</div>
                {% endfor %}
            {% else %}
                <div style="color:#aaa;">No chat yet.</div>
            {% endif %}
        </div>
        {% if selected_user and selected_firm %}
        <form class="msg-form" method="post" action="/send-message">
            <input type="hidden" name="user_number" value="{{selected_user}}">
            <input type="hidden" name="firm_number" value="{{selected_firm}}">
            <input type="text" name="message" placeholder="type message ......" required autocomplete="off">
            <button type="submit">Send</button>
        </form>
        {% endif %}
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>
            {% for message in messages %}
              <li>{{ message }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
    </div>
</div>
<script>
    // Auto-scroll chat to bottom
    window.onload = function() {
        var chatBox = document.getElementById('chat-box');
        if (chatBox) {
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    };
</script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def chat_ui():
    numbers = list_numbers()
    selected_user = request.args.get('user') or (numbers[0]['user'] if numbers else None)
    selected_firm = request.args.get('firm') or (numbers[0]['firm'] if numbers else None)
    chat = get_chat_history(selected_user, selected_firm) if selected_user and selected_firm else []
    return render_template_string(HTML_CHAT, numbers=numbers, selected_user=selected_user, selected_firm=selected_firm, chat=chat)

@app.route('/add-number', methods=['POST'])
def add_number():
    new_user_number = request.form.get('new_user_number')
    new_firm_number = request.form.get('new_firm_number')
    if new_user_number and new_firm_number:
        create_number(new_user_number, new_firm_number)
        flash(f'Number {new_user_number} ({new_firm_number}) added!')
    return redirect(url_for('chat_ui', user=new_user_number, firm=new_firm_number))

@app.route('/send-message', methods=['POST'])
def send_message():
    user_number = request.form.get('user_number')
    firm_number = request.form.get('firm_number')
    message = request.form.get('message')
    if not user_number or not firm_number or not message:
        flash('User number, firm number, and message required!')
        return redirect(url_for('chat_ui', user=user_number, firm=firm_number))
    append_message(user_number, firm_number, message, sent=True)
    # Send to webhook as if user sent it
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID_123",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": firm_number,
                                "phone_number_id": "123456789012345"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Mock User"
                                    },
                                    "wa_id": user_number
                                }
                            ],
                            "messages": [
                                {
                                    "from": user_number,
                                    "id": "wamid.mocked-id",
                                    "timestamp": str(int(datetime.now().timestamp())),
                                    "type": "text",
                                    "text": {
                                        "body": message
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=payload)
        if resp.status_code == 200:
            flash('Message sent to webhook successfully!')
        else:
            flash(f'Webhook error: {resp.status_code} {resp.text}')
    except Exception as e:
        flash(f'Error sending to webhook: {e}')
    return redirect(url_for('chat_ui', user=user_number, firm=firm_number))

@app.route('/v1/messages', methods=['POST'])
def api_send_message():
    data = request.get_json()
    app.logger.info(f"Received message send request: {data}")
    user_number = data.get('to')
    message = data.get('message')
    firm_number = find_firm_number(user_number)
    if user_number and message and firm_number:
        append_message(user_number, firm_number, message, sent=False)
    # Return a mock WhatsApp API response
    return jsonify({
        "messages": [
            {
                "id": "mocked-message-id",
                "status": "sent"
            }
        ]
    }), 200

if __name__ == '__main__':
    app.run(port=5005, debug=True) 