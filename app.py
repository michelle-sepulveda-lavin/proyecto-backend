import datetime
from flask import Flask, jsonify, request, render_template
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from config import Development
from models import db, User, Role, Plan
import json

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config.from_object(Development)

db.init_app(app)
jwt = JWTManager(app)
Migrate(app, db)
CORS(app)
manager = Manager(app)
manager.add_command("db", MigrateCommand)

CORS(app)


@app.route("/")
def main():
    return render_template('index.html')

@app.route("/login", methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username:
        return jsonify({"msg": "username is required"}), 400
    if not password:
        return jsonify({"msg": "password is required"}), 400
    
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"msg": "username/password is incorrect"}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"msg": "username/password is incorrect"}), 401

    expire_in = datetime.timedelta(days=3)
    data = {
        "access_token": create_access_token(identity=user.id, expires_delta=expire_in),
        "user": user.serialize()
    }
    return jsonify(data), 200

@app.route("/register", methods=['POST'])
def register():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username:
        return jsonify({"msg": "username is required"}), 400
    if not password:
        return jsonify({"msg": "password is required"}), 400
    
    user = User.query.filter_by(username=username).first()

    if user:
        return jsonify({"msg": "user already exists"}), 400

    user = User()
    user.username = username
    user.password = generate_password_hash(password)
    user.save()

    expire_in = datetime.timedelta(days=3)
    data = {
        "access_token": create_access_token(identity=user.id, expires_delta=expire_in),
        "user": user.serialize()
    }
    return jsonify(data), 200

@app.route("/administrador")
@jwt_required
def administrador():
    id = get_jwt_identity()
    user = User.query.get(id)

    return jsonify(user.serialize()), 200

@app.route("/roles", methods=['POST', 'GET'])
@app.route("/roles/<int:id>", methods=['DELETE'])
def roles(id=None):
    if request.method == 'GET':
        roles = Role.query.all()

        if not roles:
            return jsonify({"msg": "empty list"}), 404
        else:
            roles = list(map(lambda rol: rol.serialize(), roles))
            return jsonify(roles), 200

    if request.method == 'POST':
        rol = request.json.get("rol")

        if not rol:
            return jsonify({"msg": "rol is required"}), 400
        else:
            role = Role.query.filter_by(rol=rol).first()
            if role:
                return jsonify({"msg": "rol already exists"}), 400
            else:
                new_rol = Role()
                new_rol.rol = rol
                new_rol.save()

                return jsonify({"msg": "role created successfully"}), 200

    if request.method == 'DELETE':
        rol = Role.query.filter_by(id=id).first()
        if not rol:
            return jsonify({"msg": "id does not exists"}), 404
        else:
            rol.delete()
            return jsonify(rol.serialize()), 200


@app.route("/api/planes", methods=['GET'])
def get_planes():
    planes = Plan.query.all()
    if len(planes) > 0:
        return_plan = list(map(lambda plan: plan.serialize(), planes))
        return jsonify(return_plan)
    else:
        return jsonify({"msg": "No hay planes, por favor hacer método POST"})
    
    return return_plan

@app.route("/api/planes", methods=['POST'])  
def plan_post():

    plan_name = request.json.get("name", None)
    plan_body = request.json.get("body", None)
    plan_price = request.json.get("price", None)
    plan_frecuencia = request.json.get("frecuencia", None)


    if not plan_name:
        return jsonify({"msg": "El nombre es necesario"}), 404
    if not plan_body:
        return jsonify({"msg": "El body es necesario"}), 404
    if type(plan_body) != list:
        return jsonify({"msg": "El body debe ser un array"})
    if not plan_price:
        return jsonify({"msg": "El precio es necesario"}), 404
    if not plan_frecuencia:
        return jsonify({"msg": "La frecuencia es necesaria"}), 404
    
    plan = Plan()
    plan.name = plan_name
    plan.body = json.dumps(plan_body)
    plan.price = plan_price
    plan.frecuencia = plan_frecuencia
    plan.save()
    return jsonify({"Msg": "Plan Añadido"})

@app.route("/api/planes/<id>", methods=['DELETE'])  
def plan_delete(id):
    plan = Plan.query.filter_by(id=id).first()
    if not plan:
        return jsonify({"msg": "Este plan no existe"}), 404
    else:
        plan.delete()
        return jsonify({"msg": "Plan borrado"})

@app.route("/api/planes/<id>", methods=['PUT'])  
def plan_put(id):
    plan = Plan.query.filter_by(id=id).first()

    plan_name = request.json.get("name", None)
    plan_body = request.json.get("body", None)
    plan_price = request.json.get("price", None)
    plan_frecuencia = request.json.get("frecuencia", None)

    if plan_name:
        plan.name = plan_name
    if plan_body:
        if type(plan_body) == list:
            plan.body = json.dumps(plan_body)
        else:
            return jsonify({"Msg": "El body debe ser un array"})
    if plan_price:
        plan.price = plan_price
    if plan_frecuencia:
        plan.frecuencia = plan_frecuencia
    
    plan.update()

    return jsonify({"Msg": "Plan Actualizado"})
   

if __name__ == "__main__":
    manager.run()