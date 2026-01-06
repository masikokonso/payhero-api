from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

PAYHERO_BASE_URL = "https://backend.payhero.co.ke/api/v2"
AUTH_TOKEN = "Basic VUpXamp3ZENwcTRtbTdZcFY4MWc6MmRLakpqTkFueXpVdW1lZjUyRHFGdlJ4Snl3WGFpMVloZWRuanZmYg=="
CHANNEL_ID = '4719'


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'success',
        'message': 'PayHero API is running!',
        'endpoints': {
            'initiate_payment': '/api/payment/initiate',
            'check_status': '/api/payment/status/<transaction_code>'
        }
    })


@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        phone = data.get('phone', '').strip()
        amount = data.get('amount')
        description = data.get('description', 'Payment')
        
        if not phone:
            return jsonify({'status': 'error', 'message': 'Phone number is required'}), 400
        
        phone = phone.replace('+', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') or phone.startswith('1'):
            phone = '254' + phone
        
        if not amount or float(amount) < 1:
            return jsonify({'status': 'error', 'message': 'Amount must be at least 1 KES'}), 400
        
        payload = {
            "amount": int(float(amount)),
            "phone_number": phone,
            "channel_id": int(CHANNEL_ID),
            "provider": "m-pesa",
            "external_reference": description,
            "callback_url": data.get('callback_url', '')
        }
        
        headers = {
            'Authorization': AUTH_TOKEN,
            'Content-Type': 'application/json'
        }
        
        print(f"=== INITIATING PAYMENT ===")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{PAYHERO_BASE_URL}/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            transaction_code = result.get('CheckoutRequestID')
            
            print(f"Transaction Code: {transaction_code}")
            
            return jsonify({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'data': {
                    'transaction_code': transaction_code,
                    'CheckoutRequestID': transaction_code,
                    'phone_number': phone,
                    'amount': amount
                }
            }), 200
        else:
            error_data = response.json() if response.text else {}
            return jsonify({
                'status': 'error',
                'message': error_data.get('error_message', 'Payment initiation failed'),
                'error': error_data
            }), response.status_code
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/payment/status/<transaction_code>', methods=['GET'])
def check_payment_status(transaction_code):
    try:
        headers = {
            'Authorization': AUTH_TOKEN,
            'Content-Type': 'application/json'
        }
        
        print(f"=== CHECKING STATUS ===")
        print(f"Transaction Code: {transaction_code}")
        
        response = requests.get(
            f"{PAYHERO_BASE_URL}/payment-requests/{transaction_code}",
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Status Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            state = result.get('state', 'PENDING')
            
            print(f"Payment State: {state}")
            
            return jsonify({
                'status': 'success',
                'data': {
                    'transaction_code': transaction_code,
                    'state': state,
                    'amount': result.get('amount'),
                    'phone_number': result.get('phone_number'),
                    'paid': state == 'COMPLETED',
                    'complete': state == 'COMPLETED'
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Could not retrieve payment status',
                'error': response.json() if response.text else {}
            }), response.status_code
            
    except Exception as e:
        print(f"Status check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/payment/webhook', methods=['POST'])
def payment_webhook():
    try:
        data = request.get_json()
        print("=" * 50)
        print("WEBHOOK RECEIVED")
        print(json.dumps(data, indent=2))
        print("=" * 50)
        
        return jsonify({
            'status': 'success',
            'message': 'Webhook received'
        }), 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("PayHero API Server Starting...")
    print(f"Channel ID: {CHANNEL_ID}")
    print(f"Till: 6253624")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
