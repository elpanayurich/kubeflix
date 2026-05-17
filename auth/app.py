import os
import jwt
import datetime
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from kafka import KafkaProducer

app = Flask(__name__)
CORS(app)

# --- Configuration ---
app.config['SECRET_KEY'] = "kubeflix123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:kubeflix123@auth-db-service:5432/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Kafka Producer Setup ---
producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=['kafka-service:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Connected to Kafka successfully.")
except Exception as e:
    print(f"Failed to connect to Kafka: {e}")

# --- Models ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    tier = db.Column(db.String(20), default='free')

with app.app_context():
    db.create_all()

# --- Auth Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({"message": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        try:
            # Decode JWT and find user
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(username=data['username']).first()
        except:
            return jsonify({"message": "Token is invalid or expired"}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# --- Public Endpoints ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Missing credentials"}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 400
    
    # Create new user and hash password
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], password=hashed_pw, tier=data.get('tier', 'free'))
    
    db.session.add(new_user)
    db.session.commit()

    # Publish event to Kafka topic 'new-users'
    if producer:
        try:
            event_data = {
                "user_id": new_user.id,
                "username": new_user.username
            }
            producer.send('new-users', value=event_data)
            producer.flush()
            print(f"Event sent to Kafka: {event_data}")
        except Exception as e:
            print(f"Failed to send to Kafka: {e}")

    return jsonify({"message": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    # Verify user and password
    if user and check_password_hash(user.password, data.get('password')):
        token = jwt.encode({
            'username': user.username,
            'tier': user.tier,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

# --- Internal Endpoints ---

@app.route('/internal/update-tier', methods=['PUT'])
@token_required
def update_user_tier(current_user):
    data = request.get_json()
    new_tier = data.get('new_tier')
    
    if not new_tier:
        return jsonify({"message": "New tier not provided"}), 400
    
    try:
        current_user.tier = new_tier
        db.session.commit()
        print(f"User {current_user.username} upgraded to {new_tier}")
        return jsonify({"message": f"Successfully updated to {new_tier}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating database", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)