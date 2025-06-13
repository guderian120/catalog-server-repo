"""
ShopSphere E-Commerce API
-------------------------
A complete e-commerce solution with:
- JWT authentication (user/admin roles)
- Product catalog management
- Shopping cart functionality
- Interactive API documentation

Key Features:
- SQLite for development (easy to switch to PostgreSQL/MySQL)
- Automatic admin user creation
- Role-based access control
- Token refresh functionality
- Comprehensive error handling
"""

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
from flask_restx import Api, Resource, fields, Namespace

# Initialize Flask application
# ---------------------------
# This creates the main Flask application instance that will handle all requests
app = Flask(__name__, static_folder='static', static_url_path='')
# Configuration Setup
# ------------------
# These settings control the behavior of our application
# In production, you should use environment variables for sensitive data

# Database configuration - uses SQLite by default for easy development
# For production, set DATABASE_URL environment variable to your PostgreSQL/MySQL connection string
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///catalog.db"  # Default SQLite database file
)

# Disable Flask-SQLAlchemy event system as it's not needed and wastes resources
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JWT Configuration - IMPORTANT: In production, use a proper secret from environment variables
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-dev-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)  # Access tokens expire in 1 hour
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)  # Refresh tokens expire in 30 days

# Initialize extensions
# --------------------
# These integrate additional functionality with our Flask app
db = SQLAlchemy(app)  # Handles database operations
jwt = JWTManager(app)  # Manages JWT authentication

# Swagger API Documentation Setup
# ------------------------------
# This creates interactive API documentation available at /api-docs
api = Api(
    app,
    version='1.0',
    title='ShopSphere API',
    description='A complete e-commerce API with JWT authentication',
    doc='/api-docs',  # Endpoint for Swagger UI
    base_path='/api',  # T  # Endpoint for Swagger UI
    authorizations={
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type "Bearer {token}" in the value input'
        }
    },
    security='Bearer Auth'  # Default security scheme
)

# API Namespaces
# --------------
# These help organize related endpoints in the documentation
auth_ns = api.namespace('auth', description='User authentication and registration')
products_ns = api.namespace('products', description='Product management operations')
cart_ns = api.namespace('cart', description='Shopping cart operations')

# Data Models for Swagger Documentation
# ------------------------------------
# These define the structure of our request/response data for automatic documentation

# User model for API documentation
user_model = api.model('User', {
    'id': fields.Integer(readOnly=True, description='User identifier'),
    'username': fields.String(required=True, description='Username'),
    'email': fields.String(required=True, description='Email address'),
    'role': fields.String(description='User role (admin/user)')
})

# Login request model
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username', example='john_doe'),
    'password': fields.String(required=True, description='Password', example='securepassword123')
})

# Signup request model (extends login model)
signup_model = api.inherit('SignUp', login_model, {
    'email': fields.String(required=True, description='Email address', example='john@example.com')
})

# Product model
product_model = api.model('Product', {
    'id': fields.Integer(readOnly=True, description='Product identifier'),
    'name': fields.String(required=True, description='Product name', example='Premium Coffee'),
    'description': fields.String(description='Product description', example='Arabica beans from Colombia'),
    'price': fields.Float(required=True, description='Product price', example=12.99),
    'owner': fields.String(attribute='owner.username', description='Product owner')
})

# Shopping cart item model
cart_item_model = api.model('CartItem', {
    'id': fields.Integer(readOnly=True, description='Cart item identifier'),
    'product_id': fields.Integer(required=True, description='Product ID'),
    'name': fields.String(attribute='product.name', description='Product name'),
    'price': fields.Float(attribute='product.price', description='Product price'),
    'quantity': fields.Integer(description='Item quantity', example=1)
})

# Database Models
# --------------
# These define the structure of our database tables

class User(db.Model):
    """
    User model representing registered users in the system
    - Stores authentication credentials
    - Tracks user role (admin or regular user)
    - Maintains relationships with products and cart items
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    products = db.relationship('Product', backref='owner', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

    def set_password(self, password):
        """Securely hash and store the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    """
    Product model for items available in the store
    - Contains product details
    - Linked to the user who created it
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class CartItem(db.Model):
    """
    Shopping cart item model
    - Links users to products they've added to cart
    - Tracks quantity of each product
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product', backref='cart_items')

# Database Initialization
# ----------------------
# This ensures our database tables are created and populated with initial data

@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def initialize_database():
    """
    Initialize the database with required tables and default admin user
    - Automatically retries if database isn't ready (useful for Docker containers)
    - Creates admin user if one doesn't exist
    - Creates test user for development
    """
    try:
        # Create all database tables
        db.create_all()
        
        # Create default admin user if it doesn't exist
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", email="admin@example.com", role='admin')
            admin.set_password("admin123")  # IMPORTANT: Change this in production!
            db.session.add(admin)
            
            # Create test user for development
            test_user = User(username="test", email="test@example.com", role='user')
            test_user.set_password("test123")  # Change in production
            db.session.add(test_user)
            
            db.session.commit()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise e  # This allows the retry decorator to work

# Authentication Endpoints
# -----------------------

@auth_ns.route('/signup')
class SignUp(Resource):
    @auth_ns.expect(signup_model)
    @auth_ns.response(201, 'User created successfully', user_model)
    @auth_ns.response(400, 'Validation error')
    def post(self):
        """
        Register a new user
        - Requires username, email and password
        - Returns JWT tokens for immediate authentication
        """
        data = request.get_json()
        
        # Validate required fields
        if not data or "username" not in data or "email" not in data or "password" not in data:
            return {"error": "Username, email and password are required"}, 400
        
        # Check for existing username
        if User.query.filter_by(username=data["username"]).first():
            return {"error": "Username already exists"}, 400
        
        # Check for existing email
        if User.query.filter_by(email=data["email"]).first():
            return {"error": "Email already exists"}, 400
        
        try:
            # Create and save new user
            user = User(username=data["username"], email=data["email"])
            user.set_password(data["password"])
            db.session.add(user)
            db.session.commit()
            
            # Generate JWT tokens
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            return {
                "message": "User created successfully",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, 201
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """
        Authenticate user and return JWT tokens
        - Requires username and password
        - Returns access and refresh tokens
        - Includes user role in token claims
        """
        data = request.get_json()
        
        # Validate required fields
        if not data or "username" not in data or "password" not in data:
            return {"error": "Username and password are required"}, 400
        
        # Find user and verify password
        user = User.query.filter_by(username=data["username"]).first()
        if not user or not user.check_password(data["password"]):
            return {"error": "Invalid username or password"}, 401
        
        # Include user role in JWT claims
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }


@auth_ns.route('/refresh')
class Refresh(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @auth_ns.response(200, 'Token refreshed')
    @jwt_required(refresh=True)
    def post(self):
        """
        Refresh access token
        - Requires valid refresh token
        - Returns new access token
        """
        try:
            current_user = get_jwt_identity()
            new_token = create_access_token(identity=current_user)
        except Exception as e:
            return {"error": str(e)}, 500
        return {"access_token": new_token}

# Product Endpoints
# ----------------

@products_ns.route('/products')
class ProductList(Resource):
    @products_ns.marshal_list_with(product_model)
    def get(self):
        """
        Get list of all available products
        - No authentication required
        - Returns array of product objects
        """
        products = Product.query.all()
        return [{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "owner": p.owner.username if p.owner else None
        } for p in products]

    @products_ns.doc(security='Bearer Auth')
    @products_ns.expect(product_model)
    @products_ns.response(201, 'Product created', product_model)
    @products_ns.response(403, 'Admin access required')
    @jwt_required()
    def post(self):
        """
        Create new product (Admin only)
        - Requires admin privileges
        - Accepts product details in request body
        - Returns created product
        """
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
        except Exception as e:
            return {"error": str(e)}, 500
        # Verify admin role
        if user.role != 'admin':
            return {"error": "Only admins can create products"}, 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data or "price" not in data:
            return {"error": "Name and price are required"}, 400
        
        try:
            # Create and save new product
            new_product = Product(
                name=data["name"],
                description=data.get("description", ""),
                price=float(data["price"]),
                user_id=user_id
            )
            db.session.add(new_product)
            db.session.commit()
            return {
                "id": new_product.id,
                "name": new_product.name,
                "description": new_product.description,
                "price": new_product.price
            }, 201
        except ValueError:
            return {"error": "Invalid price format"}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500


@products_ns.route('/my')
class MyProducts(Resource):
    @products_ns.doc(security='Bearer Auth')
    @products_ns.marshal_list_with(product_model)
    @jwt_required()
    def get(self):
        """
        Get products created by current user
        - Requires authentication
        - Returns array of user's products
        """
        try:
            user_id = get_jwt_identity()
            products = Product.query.filter_by(user_id=user_id).all()
        except Exception as e:
            return {"error": str(e)}, 500
        return [{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price
        } for p in products]


@products_ns.route('/products/<int:product_id>')
@products_ns.param('product_id', 'Product identifier')
class ProductResource(Resource):
    @products_ns.doc(security='Bearer Auth')
    @products_ns.response(200, 'Product deleted')
    @products_ns.response(403, 'Not product owner')
    @products_ns.response(404, 'Product not found')
    @jwt_required()
    def delete(self, product_id):
        """
        Delete a product
        - Requires authentication
        - Only product owner can delete
        """
        try:
            user_id = get_jwt_identity()
            product = Product.query.get(product_id)
        except Exception as e:      
            return {"error": str(e)}, 500
            
        # Verify product exists
        if not product:
            return {"error": "Product not found"}, 404
        
        # Verify ownership
        if str(product.user_id) != user_id:
            return {"error": "You can only delete your own products"}, 403
        
        # Delete product
        db.session.delete(product)
        db.session.commit()
        return {"message": "Product deleted"}, 200

# Shopping Cart Endpoints
# ----------------------

@cart_ns.route('/cart')
class CartResource(Resource):
    @cart_ns.doc(security=['Bearer'])
    @cart_ns.marshal_list_with(cart_item_model)
    @cart_ns.response(401, 'Unauthorized')
    @jwt_required()
    def get(self):
        """
        Get current user's shopping cart
        - Requires authentication
        - Returns array of cart items with product details
        """
        try:
            user_id = get_jwt_identity()
            cart_items = CartItem.query.filter_by(user_id=user_id).all()
            return [{
                "id": item.id,
                "product_id": item.product_id,
                "name": item.product.name,
                "price": item.product.price,
                "quantity": item.quantity
            } for item in cart_items]
        except Exception as e:
            api.abort(500, str(e))
    @cart_ns.doc(security='Bearer Auth')
    @cart_ns.expect(api.model('CartItemRequest', {
        'product_id': fields.Integer(required=True),
        'quantity': fields.Integer(default=1)
    }))
    @cart_ns.response(200, 'Product added to cart')
    @cart_ns.response(400, 'Product ID required')
    @cart_ns.response(404, 'Product not found')
    @jwt_required()
    def post(self):
        """
        Add item to cart
        - Requires authentication
        - If product already in cart, increments quantity
        - Accepts product_id and optional quantity
        """
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
        except Exception as e:
            return {"error": str(e)}, 500
        
        # Validate required field
        if not data or "product_id" not in data:
            return {"error": "Product ID is required"}, 400
        
        # Verify product exists
        product = Product.query.get(data["product_id"])
        if not product:
            return {"error": "Product not found"}, 404
        
        # Check if product already in cart
        cart_item = CartItem.query.filter_by(
            user_id=user_id, 
            product_id=data["product_id"]
        ).first()
        
        if cart_item:
            # Increment quantity if exists
            cart_item.quantity += 1
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user_id,
                product_id=data["product_id"],
                quantity=data.get("quantity", 1)
            )
            db.session.add(cart_item)
        
        db.session.commit()
        return {"message": "Product added to cart"}, 200


@cart_ns.route('/cart/<int:item_id>')
@cart_ns.param('item_id', 'Cart item identifier')
class CartItemResource(Resource):
    @cart_ns.doc(security='Bearer Auth')
    @cart_ns.response(200, 'Item removed from cart')
    @cart_ns.response(403, 'Unauthorized')
    @cart_ns.response(404, 'Cart item not found')
    @jwt_required()
    def delete(self, item_id):
        """
        Remove item from cart
        - Requires authentication
        - Only cart owner can remove items
        """
        try:
            user_id = get_jwt_identity()
            cart_item = CartItem.query.get(item_id)
        except Exception as e:
            return {"error": str(e)}, 500
        # Verify item exists
        if not cart_item:
            return {"error": "Cart item not found"}, 404
        
        # Verify ownership
        if str(cart_item.user_id) != user_id:
            return {"error": "Unauthorized"}, 403
        
        # Remove item
        db.session.delete(cart_item)
        db.session.commit()
        return {"message": "Item removed from cart"}, 200

# Frontend Serving
# ---------------

# Frontend Serving
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'static/index.html')

@app.route('/<path:path>')
def serve_static(path):
    # First try to serve from static folder
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # If file not found in static, serve index.html (for SPA routing)
        return send_from_directory(app.static_folder, 'index.html')

# Application Startup
# ------------------

if __name__ == '__main__':
    # Initialize database before starting the app
    with app.app_context():
        initialize_database()
    
    # Start the Flask development server
    app.run(host='0.0.0.0', port=5000 ,debug=True)