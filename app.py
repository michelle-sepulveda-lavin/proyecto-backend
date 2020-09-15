from flask import Flask, jsonify, request, render_template
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from config import Development
from models import db, Plan
import json

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config.from_object(Development)

db.init_app(app)
Migrate(app, db)
manager = Manager(app)
manager.add_command("db", MigrateCommand)

CORS(app)


@app.route("/")
def main():
    return render_template('index.html')

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