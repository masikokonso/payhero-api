from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# PayHero Configuration - YOUR CREDENTIALS
PAYHERO_BASE_URL = "https://backend.payhero.co.ke/api/v2"
AUTH_TOKEN = "Basic VUpXamp3ZENwcTRtbTdZcFY4MWc6MmRLakpqTkFueXpVdW1lZjUyRHFGdlJ4Snl3WGFpMVloZWRuanZmYg=="
CHANNEL_ID = 4719  # Your Till 6253624


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'success',
        'message': 'PayHero API is running!',
        'channel': CHANNEL_ID
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
        
        # Format phone number
        phone = phone.replace('+', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') or phone.startswith('1'):
            phone = '254' + phone
        
        if not amount or float(amount) < 1:
            return jsonify({'status': 'error', 'message': 'Amount must be at least 1 KES'}), 400
        
        # PayHero payload - NO PROVIDER FIELD!
        payload = {
            "amount": int(float(amount)),
            "phone_number": phone,
            "channel_id": int(CHANNEL_ID),
            "external_reference": description
        }
        
        headers = {
            'Authorization': AUTH_TOKEN,
            'Content-Type': 'application/json'
        }
        
        print(f"=== INITIATING PAYMENT ===")
        print(f"Phone: {phone}")
        print(f"Amount: {amount}")
        print(f"Channel: {CHANNEL_ID}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{PAYHERO_BASE_URL}/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"PayHero Response Status: {response.status_code}")
        print(f"PayHero Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            
            # Extract CheckoutRequestID
            checkout_id = result.get('CheckoutRequestID') or result.get('transaction_code') or result.get('reference')
            
            print(f"Transaction Code: {checkout_id}")
            
            return jsonify({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'data': {
                    'transaction_code': checkout_id,
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'reference': result.get('reference'),
                    'state': 'PENDING',
                    'amount': amount,
                    'phone_number': phone
                }
            }), 200
        else:
            error_data = response.json() if response.text else {}
            print(f"ERROR: {error_data}")
            return jsonify({
                'status': 'error',
                'message': error_data.get('error_message', 'Payment initiation failed'),
                'error': error_data
            }), response.status_code
            
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
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
        
        # Try payment-requests endpoint first
        response = requests.get(
            f"{PAYHERO_BASE_URL}/payment-requests/{transaction_code}",
            headers=headers,
            timeout=15
        )
        
        print(f"Status Response: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            state = result.get('state', 'PENDING')
            
            return jsonify({
                'status': 'success',
                'data': {
                    'transaction_code': transaction_code,
                    'state': state,
                    'amount': result.get('amount'),
                    'phone_number': result.get('phone_number'),
                    'paid': state == 'COMPLETED'
                }
            }), 200
        else:
            # Try alternative endpoint
            response2 = requests.get(
                f"{PAYHERO_BASE_URL}/payments/{transaction_code}",
                headers=headers,
                timeout=15
            )
            
            if response2.status_code == 200:
                result = response2.json()
                return jsonify({
                    'status': 'success',
                    'data': result
                }), 200
            
            return jsonify({
                'status': 'error',
                'message': 'Could not retrieve payment status',
                'error': response.json() if response.text else {}
            }), response.status_code
            
    except Exception as e:
        print(f"Status check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("PayHero API Server Starting...")
    print("=" * 50)
    print(f"Channel ID: {CHANNEL_ID}")
    print(f"Till Number: 6253624")
    print(f"Auth Token: Configured")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
