from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from tenacity import retry, wait_fixed, stop_after_attempt
import os 

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://admin:admin123@mysql-container:3306/catalog"  
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)


@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def initialize_database():
    try:
        db.create_all()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database not ready yet: {e}")
        raise e  # Needed for tenacity to retry
#

@app.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "GET":
        products = Products.query.all()
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price
        } for p in products])
    
    elif request.method == "POST":
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data or "price" not in data:
            return jsonify({"error": "Name and price are required"}), 400
        
        try:
            new_product = Products(
                name=data["name"],
                description=data.get("description", ""),
                price=float(data["price"])
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



@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Products.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')
if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(host='0.0.0.0', port=5000)