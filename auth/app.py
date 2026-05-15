from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
from flask import request, jsonify
import jwt
import datetime

app = Flask(__name__)

DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'kubeflix123')
DB_HOST = os.getenv('POSTGRES_HOST', 'auth-db-service')
DB_NAME = os.getenv('POSTGRES_DB', 'auth_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tier = db.Column(db.String(20), default='basic')

    def __repr__(self):
        return f'<User {self.username} - Tier: {self.tier}>'

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']
    tier = data.get('tier', 'basic')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, password_hash=hashed_password, tier=tier)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'tier': new_user.tier
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

SECRET_KEY = "kubeflix123"

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'tier': user.tier,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({
            "message": "Login exitoso",
            "token": token
        }), 200
    
    return jsonify({"message": "Credenciales inválidas"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)