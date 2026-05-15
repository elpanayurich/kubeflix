from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import os
import csv
import jwt
from functools import wraps

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:kubeflix123@search-db-service:5432/search_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

SECRET_KEY = "kubeflix123" 

db = SQLAlchemy(app)

class Movie(db.Model):
    __tablename__ = 'movies_table'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.String(200))
    internal_id = db.Column(db.String(50))

def seed_from_csv():
    csv_path = '/app/data/movies.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and len(row) >= 2:
                    title, tags = row[0], row[1]
                    if not Movie.query.filter_by(title=title).first():
                        db.session.add(Movie(title=title, tags=tags))
        db.session.commit()

with app.app_context():
    db.create_all()
    if Movie.query.count() == 0:
        seed_from_csv()

# --- DECORADOR JWT PARA PROTEGER RUTAS ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Extraemos el token del header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"message": "Formato de token inválido"}), 401

        if not token:
            return jsonify({"message": "Token ausente, acceso denegado"}), 401

        # Validamos matemáticamente la firma del JWT
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "El token ha expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token inválido o corrupto"}), 401

        return f(*args, **kwargs)
    
    return decorated
# ----------------------------------------

@app.route('/search', methods=['GET'])
@token_required
def search():
    query = request.args.get('q', '')
    movies_found = Movie.query.filter(
        or_(
            Movie.title.ilike(f'%{query}%'),
            Movie.tags.ilike(f'%{query}%')
        )
    ).all()
    result = [m.title for m in movies_found]
    return jsonify(result)

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

@app.route('/add', methods=['POST'])
def add_movie():
    auth_key = request.headers.get('X-Admin-Token')
    if not ADMIN_PASSWORD or auth_key != ADMIN_PASSWORD:
        return jsonify({"error": "not authorized"}), 401
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "title missing"}), 400
    new_movie = Movie(title=data['title'], tags=data.get('tags', ''))
    db.session.add(new_movie)
    db.session.commit()
    return jsonify({"message": f"'{new_movie.title}' added correctly"}), 201

@app.route('/delete', methods=['DELETE'])
def delete_movie():
    auth_key = request.headers.get('X-Admin-Token')
    if not ADMIN_PASSWORD or auth_key != ADMIN_PASSWORD:
        return jsonify({"error": "not authorized"}), 401
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "title missing"}), 400
    title_to_delete = data['title']
    movie = Movie.query.filter_by(title=title_to_delete).first()
    if not movie:
        return jsonify({"error": "movie not found"}), 404
    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": f"'{title_to_delete}' deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)