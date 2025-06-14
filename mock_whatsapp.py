from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
import logging
import requests

app = Flask(__name__)
app.secret_key = 'mock_secret_key'
logging.basicConfig(level=logging.INFO)

WEBHOOK_URL = 'http://localhost:8000/chatbridge/webhook/'

HTML_FORM = '''
<!doctype html>
<title>Mock WhatsApp UI</title>
<h2>Send WhatsApp Message (Mock)</h2>
<form method="post" action="/send-ui">
  <label>Phone Number:</label><br>
  <input type="text" name="phone_number" required><br><br>
  <label>Message:</label><br>
  <textarea name="message" required></textarea><br><br>
  <input type="submit" value="Send">
</form>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul>
    {% for message in messages %}
      <li>{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
'''

@app.route('/', methods=['GET'])
def ui():
    return render_template_string(HTML_FORM)

@app.route('/send-ui', methods=['POST'])
def send_ui():
    phone_number = request.form.get('phone_number')
    message = request.form.get('message')
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
                                "display_phone_number": "1234567890",
                                "phone_number_id": "123456789012345"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Mock User"
                                    },
                                    "wa_id": phone_number
                                }
                            ],
                            "messages": [
                                {
                                    "from": phone_number,
                                    "id": "wamid.mocked-id",
                                    "timestamp": "1689763840",
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
    return redirect(url_for('ui'))

@app.route('/v1/messages', methods=['POST'])
def send_message():
    data = request.get_json()
    app.logger.info(f"Received message send request: {data}")
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