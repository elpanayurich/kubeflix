import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import jwt
from functools import wraps
import random

app = Flask(__name__)
CORS(app)

# Must match exactly what's in auth/app.py
SECRET_KEY = "kubeflix123" 

# --- JWT DECORATOR ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Extract token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Invalid token format"}), 401

        if not token:
            return jsonify({"message": "Token is missing, access denied"}), 401

        # Mathematically validate the JWT signature
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid or corrupted token"}), 401

        return f(*args, **kwargs)
    
    return decorated
# ----------------------------------------

# Internal DNS for the Auth Service in Kubernetes
AUTH_SERVICE_URL = "http://auth-service/internal/update-tier"

@app.route('/upgrade', methods=['POST'])
@token_required
def upgrade():
    # 1. Simulate payment processing here (e.g., Stripe, PayPal)
    print("Processing payment for Premium tier...")
    if random.randint(1, 10) == 7:
        return jsonify({"message": "Payment denied, you are poor, try again when you get more money"}), 402

    # 2. Get the token from the current request to pass it along
    token = request.headers.get('Authorization')
    
    # 3. Make the internal East-West call to Auth Service
    try:
        response = requests.put(
            AUTH_SERVICE_URL,
            headers={'Authorization': token},
            json={'new_tier': 'premium'}
        )
        
        if response.status_code == 200:
            return jsonify({"message": "Payment successful. Account upgraded to Premium!"}), 200
        else:
            # If payment worked but auth failed to update DB
            return jsonify({"message": "Payment successful, but failed to update user tier"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"message": "Auth service is currently unreachable", "error": str(e)}), 503


@app.route('/downgrade', methods=['POST'])
@token_required
def downgrade():
    # Get the token from the current request
    token = request.headers.get('Authorization')
    
    # Make the internal call to downgrade the user
    try:
        response = requests.put(
            AUTH_SERVICE_URL,
            headers={'Authorization': token},
            json={'new_tier': 'free'}
        )
        
        if response.status_code == 200:
            return jsonify({"message": "Account downgraded to Free tier"}), 200
        else:
            return jsonify({"message": "Failed to downgrade user tier"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"message": "Auth service is currently unreachable", "error": str(e)}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)