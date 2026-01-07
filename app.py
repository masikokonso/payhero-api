from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow JavaScript to call this API

# PayHero Configuration
PAYHERO_BASE_URL = "https://backend.payhero.co.ke/api/v2"
AUTH_TOKEN = os.getenv('PAYHERO_AUTH_TOKEN')
CHANNEL_ID = int(os.getenv('PAYHERO_CHANNEL_ID', '4719'))

# Pre-build headers (avoid recreating on every request)
HEADERS = {
    'Authorization': AUTH_TOKEN,
    'Content-Type': 'application/json'
}


@app.route('/', methods=['GET'])
def home():
    """API Status Check"""
    return jsonify({
        'status': 'success',
        'message': 'PayHero STK Push API is running!',
        'endpoint': '/api/payment/initiate'
    })


@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    """
    Initiate M-Pesa STK Push
    
    Expected JSON body:
    {
        "phone": "254712345678",
        "amount": 100,
        "description": "Payment for Order #123"
    }
    """
    try:
        data = request.get_json()
        
        # Quick validation
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        phone = data.get('phone', '').strip()
        amount = data.get('amount')
        
        if not phone:
            return jsonify({'status': 'error', 'message': 'Phone number is required'}), 400
        
        # Optimized phone formatting (single pass)
        phone = phone.replace('+', '').replace(' ', '')
        if phone[0] == '0':
            phone = '254' + phone[1:]
        elif phone[0] in '71':
            phone = '254' + phone
        
        # Quick amount validation
        if not amount or float(amount) < 1:
            return jsonify({'status': 'error', 'message': 'Amount must be at least 1 KES'}), 400
        
        # Build payload
        payload = {
            "amount": int(float(amount)),
            "phone_number": phone,
            "channel_id": CHANNEL_ID,
            "provider": "m-pesa",
            "external_reference": data.get('description', 'Payment'),
            "callback_url": data.get('callback_url', '')
        }
        
        # Fast API call with reduced timeout
        response = requests.post(
            f"{PAYHERO_BASE_URL}/payments",
            headers=HEADERS,
            json=payload,
            timeout=12  # Reduced from 30 to 12 seconds for faster response
        )
        
        # Quick response handling
        if response.status_code in [200, 201]:
            return jsonify({
                'status': 'success',
                'message': 'STK Push sent successfully',
                'data': response.json()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'STK Push failed',
                'error': response.json() if response.text else {},
                'status_code': response.status_code
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'status': 'error', 'message': 'Request timeout - please try again'}), 408
        
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Network error: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    print(f"PayHero STK API | Channel: {CHANNEL_ID} | Auth: {'OK' if AUTH_TOKEN else 'MISSING'}")
    print("Server: http://localhost:5000")
    
    # Production-optimized settings
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
