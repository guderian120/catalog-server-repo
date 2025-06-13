

from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, create_refresh_token
)
from werkzeug.security import generate_password_hash, check_password_hash
from tenacity import retry, wait_fixed, stop_after_attempt
import os
from datetime import timedelta

app = Flask(__name__)

# Configuration
# app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
#     "DATABASE_URL",
#     "mysql+pymysql://admin:admin123@mysql-container:3306/catalog"  
# )

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///catalog.db"
)
# For production, you can use MySQL or PostgreSQL by changing the URI accordingly
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "_EOmNZKe-bnKWeP6qsL4z7F58Mt0QO3VA-VlaaowkwA")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    products = db.relationship('Product', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Database initialization
@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def initialize_database():
    try:
        db.create_all()
        # Create admin user if not exists
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database not ready yet: {e}")
        raise e

# Authentication routes



@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    
    if not data or "username" not in data or "email" not in data or "password" not in data:
        return jsonify({"error": "Username, email and password are required"}), 400
    
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
    
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400
    
    try:
        user = User(username=data["username"], email=data["email"])
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            "message": "User created successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = User.query.filter_by(username=data["username"]).first()
    
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401
    
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })

@app.route("/api/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({"access_token": new_token})

# Product routes
@app.route("/api/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "owner": p.owner.username if p.owner else None
    } for p in products])

@app.route("/api/products/my", methods=["GET"])
@jwt_required()
def get_my_products():
    user_id = get_jwt_identity()
    products = Product.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price
    } for p in products])

@app.route("/api/products", methods=["POST"])
@jwt_required()
def create_product():
    print("data received in create_product")
    print(request.get_json())
    data = request.get_json()
    user_id = get_jwt_identity()
    
    if not data or "name" not in data or "price" not in data:
        return jsonify({"error": "Name and price are required"}), 400
    
    try:
        new_product = Product(
            name=data["name"],
            description=data.get("description", ""),
            price=float(data["price"]),
            user_id=user_id
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({
            "id": new_product.id,
            "name": new_product.name,
            "description": new_product.description,
            "price": new_product.price
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid price format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product.user_id != user_id:
        return jsonify({"error": "You can only delete your own products"}), 403
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200

# Serve frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(f"static/{path}"):
        return send_from_directory('static', path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(host='0.0.0.0', port=5000)