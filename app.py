from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Your PayHero Credentials
AUTH_TOKEN = "Basic VUpXamp3ZENwcTRtbTdZcFY4MWc6MmRLakpqTkFueXpVdW1lZjUyRHFGdlJ4Snl3WGFpMVloZWRuanZmYg=="
CHANNEL_ID = 4719
BASE_URL = "https://backend.payhero.co.ke/api/v2"

@app.route('/')
def home():
    return jsonify({"status": "running", "till": "6253624"})

@app.route('/api/payment/initiate', methods=['POST'])
def initiate():
    data = request.get_json()
    
    phone = data.get('phone')
    amount = data.get('amount')
    
    # Format phone
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    # PayHero request
    response = requests.post(
        f"{BASE_URL}/payments",
        headers={'Authorization': AUTH_TOKEN, 'Content-Type': 'application/json'},
        json={
            "amount": int(amount),
            "phone_number": phone,
            "channel_id": CHANNEL_ID,
            "external_reference": data.get('description', 'Payment')
        },
        timeout=30
    )
    
    result = response.json()
    
    if response.status_code in [200, 201]:
        return jsonify({
            "status": "success",
            "data": result
        })
    else:
        return jsonify({
            "status": "error",
            "message": result.get('error_message', 'Failed')
        }), 400

@app.route('/api/payment/status/<code>')
def status(code):
    response = requests.get(
        f"{BASE_URL}/payment-requests/{code}",
        headers={'Authorization': AUTH_TOKEN},
        timeout=15
    )
    
    if response.status_code == 200:
        return jsonify({"status": "success", "data": response.json()})
    else:
        return jsonify({"status": "error", "message": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
