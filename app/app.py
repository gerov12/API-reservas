from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

# configuro app y db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://grupo41:123456@localhost:3306/apireservas'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

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
        fields = ('id', 'name', 'stock', 'producer', 'delivery_time')

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
        fields = ('id', 'user_id', 'colection_id', 'material_id', 'quantity')

# creo las tablas
with app.app_context():
    db.create_all()

# defino las rutas
@app.route('/materiales', methods=['GET'])
def get_materials():
    names = request.json['names']
    materials = []
    for name in names:
        m = Material.query.filter_by(name=name).all()
        if m:
            for material in m:
                material_dump = MaterialSchema.dump(material)
                materials.append(material_dump)
    return jsonify(materials)

@app.route('/reservar_materiales', methods=['PUT'])
def reserve_materials():
    reserva = request.json['materials']
    user_id = request.json['user_id']
    colection_id = request.json['colection_id']
    pedidos = []
    for pedido in reserva:
        material = Material.query.get(pedido['id'])
        if material:
            if material.stock >= pedido['quantity']:
                material.stock = material.stock - pedido['quantity']
                nuevo_pedido = Pedido(user_id, colection_id, material.id, pedido['quantity'])
                db.session.add(nuevo_pedido)
                pedidos.append(nuevo_pedido)
    if pedidos:
        db.session.commit()
    return jsonify(PedidoSchema(many=True).dump(pedidos))

# corro la app con debug true para que se actualice dinamicamente
if __name__ == ("__main__"):
    app.run(debug=True)