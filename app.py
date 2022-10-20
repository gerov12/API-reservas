from flask import Flask, jsonify, request, make_response
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
from functools import wraps

# configuro app y db
app = Flask(__name__)
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"postgresql://grupo2:5XMC1oTou0vQwRYx4JSjQPLYLiN4h4Kb@dpg-cd88gopa6gds9o58r6ng-a.oregon-postgres.render.com/apireservas"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "super-secret"


db = SQLAlchemy(app)
ma = Marshmallow(app)

# MATERIAL
class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    stock = db.Column(db.Integer)
    producer = db.Column(db.String(50))
    delivery_time = db.Column(db.Integer)
    pedido = db.relationship("Pedido", backref="material", uselist=False)

    def __init__(self, name, stock, producer, delivery_time):
        self.name = name
        self.stock = stock
        self.producer = producer
        self.delivery_time = delivery_time


class MaterialSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "stock", "producer", "delivery_time")


# PEDIDO
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    colection_id = db.Column(db.Integer)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"))
    quantity = db.Column(db.Integer)

    def __init__(self, user_id, colection_id, material_id, quantity):
        self.user_id = user_id
        self.colection_id = colection_id
        self.material_id = material_id
        self.quantity = quantity


class PedidoSchema(ma.Schema):
    class Meta:
        fields = ("id", "user_id", "colection_id", "material_id", "quantity")


# USER
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


# creo las tablas
with app.app_context():
    db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get("token")

        if not token:
            return jsonify({"message": "El token no existe"}), 403
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
        except:
            return jsonify({"message": "El token ha expirado o es inválido"}), 403
        return f(*args, **kwargs)

    return decorated


@app.route("/login", methods=["GET"])
def login():
    username = request.json["username"]
    password = request.json["password"]
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        token = jwt.encode(
            {
                "user": username,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
        )
        return jsonify({"token": token.decode("UTF-8")})
    return make_response("Usuario o contraseña incorrectos", 401)


# defino las rutas
@app.route("/materiales", methods=["GET"])
@token_required
def get_materials():
    names = request.json["names"]
    materials = []
    for name in names:
        m = Material.query.filter_by(name=name).all()
        if m:
            for material in m:
                materials.append(material)
    return jsonify(MaterialSchema(many=True).dump(materials))


@app.route("/reservar_materiales", methods=["PUT"])
@token_required
def reserve_materials():
    reserva = request.json["materials"]
    user_id = request.json["user_id"]
    colection_id = request.json["colection_id"]
    pedidos = []
    for pedido in reserva:
        material = Material.query.get(pedido["id"])
        if material:
            if material.stock >= pedido["quantity"]:
                material.stock = material.stock - pedido["quantity"]
                nuevo_pedido = Pedido(
                    user_id, colection_id, material.id, pedido["quantity"]
                )
                db.session.add(nuevo_pedido)
                pedidos.append(nuevo_pedido)
    if pedidos:
        db.session.commit()
    return jsonify(PedidoSchema(many=True).dump(pedidos))


# corro la app con debug true para que se actualice dinamicamente
if __name__ == ("__main__"):
    app.run(debug=True)
