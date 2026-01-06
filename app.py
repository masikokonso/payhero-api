import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# PayHero Configuration
AUTH_TOKEN = os.getenv('PAYHERO_AUTH_TOKEN')
BASE_URL = "https://backend.payhero.co.ke/api/v2"

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "PayHero API is running!",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    try:
        data = request.get_json()
        
        phone = data.get('phone')
        amount = data.get('amount')
        description = data.get('description', 'Payment')
        channel_id = data.get('channel_id', 4719)  # Default channel
        
        if not phone or not amount:
            return jsonify({
                "status": "error",
                "message": "Phone and amount are required"
            }), 400
        
        # Format phone number
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone
        
        # PayHero API request
        payload = {
            "amount": int(amount),
            "phone_number": phone,
            "channel_id": int(channel_id),
            "provider": "mpesa",
            "external_reference": description,
            "callback_url": request.host_url + "api/payment/webhook"
        }
        
        headers = {
            'Authorization': AUTH_TOKEN,
            'Content-Type': 'application/json'
        }
        
        print(f"=== INITIATING PAYMENT ===")
        print(f"Phone: {phone}, Amount: {amount}, Channel: {channel_id}")
        
        response = requests.post(
            f"{BASE_URL}/payments",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response_data = response.json()
        print(f"PayHero Response: {response_data}")
        
        if response.status_code in [200, 201]:
            # Extract CheckoutRequestID from PayHero response
            checkout_request_id = response_data.get('CheckoutRequestID')
            
            return jsonify({
                "status": "success",
                "message": "Payment initiated successfully",
                "data": {
                    "transaction_code": checkout_request_id,  # ← Use CheckoutRequestID
                    "amount": amount,
                    "phone_number": phone,
                    "state": "PENDING"
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": response_data.get('message', 'Payment initiation failed'),
                "details": response_data
            }), response.status_code
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/payment/status/<checkout_request_id>', methods=['GET'])
def check_status(checkout_request_id):
    try:
        headers = {
            'Authorization': AUTH_TOKEN,
            'Content-Type': 'application/json'
        }
        
        print(f"=== CHECKING STATUS ===")
        print(f"CheckoutRequestID: {checkout_request_id}")
        
        # PayHero status check endpoint
        response = requests.get(
            f"{BASE_URL}/payment-requests/{checkout_request_id}",  # ← Correct endpoint!
            headers=headers,
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            
            # PayHero returns different status values
            state = data.get('state', 'PENDING')
            
            return jsonify({
                "status": "success",
                "data": {
                    "transaction_code": checkout_request_id,
                    "state": state,
                    "amount": data.get('amount'),
                    "phone_number": data.get('phone_number'),
                    "paid": state == 'COMPLETED'
                }
            })
        else:
            error_data = response.json()
            return jsonify({
                "status": "error",
                "message": "Could not retrieve payment status",
                "error": error_data
            }), response.status_code
            
    except Exception as e:
        print(f"Status check error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
