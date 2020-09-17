import datetime
from flask import Flask, jsonify, request, render_template
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from config import Development
from models import db, User, Role, Plan, Edificio, InfoContacto
import json
import os
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

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
        return jsonify({"msg": "El usuario es requerido"}), 400
    if not password:
        return jsonify({"msg": "La contraseña es requerida"}), 400
    
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"msg": "El usuario/contraseña es incorrecta"}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"msg": "El usuario/contraseña es incorrecta"}), 401

    expire_in = datetime.timedelta(days=1)
    data = {
        "access_token": create_access_token(identity=user.id, expires_delta=expire_in),
        "user": user.serialize()
    }
    return jsonify(data), 200

@app.route("/register", methods=['POST', 'GET', 'PUT'])
@app.route("/register/<int:id>", methods=['DELETE'])
def register(id=None):
    if request.method == 'POST':
        username = request.json.get("username", None)
        password = request.json.get("password", None)
        rol_id = request.json.get("rol_id", None)
        email = request.json.get("email", None)

        if not username:
            return jsonify({"msg": "username is required"}), 400
        if not password:
            return jsonify({"msg": "password is required"}), 400
        if not rol_id:
            return jsonify({"msg": "rol_id is required"})
        if not email:
            return jsonify({"msg": "email is required"})
        
        user = User.query.filter_by(username=username).first()

        if user:
            return jsonify({"msg": "user already exists"}), 400

        user = User()
        user.username = username
        user.password = generate_password_hash(password)
        user.rol_id = rol_id
        user.email = email
        user.save()

        expire_in = datetime.timedelta(days=1)
        data = {
            "access_token": create_access_token(identity=user.id, expires_delta=expire_in),
            "user": user.serialize()
        }
        return jsonify(data), 200
    if request.method == 'GET':
        usuarios = User.query.all()
        if not usuarios:
            return jsonify({"msg": "Lista vacia, usar metodo POST"}), 404
        else:
            usuarios = list(map(lambda usuario: usuario.serialize(), usuarios))
            return jsonify(usuarios), 200

    if request.method == 'PUT':


        password = request.json.get("password", None)
        username = request.json.get("username")
        email = request.json.get("email", None)

      
        if not password:
            return jsonify({"msg": "password is required"}), 400

        if not email:
            return jsonify({"msg": "email is required"}), 400
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"msg": "el email no existe"}), 400
        
        
  
        user.password = generate_password_hash(password)
        user.username = username
        user.update()
        return jsonify({"msg": "usuario actualizado correctamente"}), 200

    if request.method == 'DELETE':
        user = User.query.filter_by(id=id).first()
        if not user:
            return jsonify({"msg": "el usuario no existe"}), 400
        else:
            user.delete()
            return jsonify({"msg": "usuario eliminado correctamente"}), 200

@app.route("/recuperar-password", methods=['POST'])
def recuperacion():
    email = request.json.get("email")
    if not email:
        return jsonify({"msg": "email es requerido"}), 400
    else:
        correo = User.query.filter_by(email=email).first()
        if not correo:
            return jsonify({"msg": "email no existe"}), 404
        else:
            sg = sendgrid.SendGridAPIClient(api_key="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")
            from_email = Email("edificios.felices.cl@gmail.com")
            to_email = To("edificios.felices.cl@gmail.com")
            subject = "Email Recuperacion"
            expire_in = datetime.timedelta(days=1)
            data = {
            "access_token": create_access_token(identity=correo.id, expires_delta=expire_in),
            }
            mensaje = "Para recuperar tu contraseña, usa el siguiente"
            content = Content("text/plain", data["access_token"]  )
            mail = Mail(from_email, to_email, subject, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            print(response.status_code)
            print(response.body)
            print(response.headers)
            return jsonify({"msg": "Se ha enviado un email para reestablecer la contraseña"}), 200

@app.route("/administrador")
@jwt_required
def administrador():
    id = get_jwt_identity()
    user = User.query.get(id)

    return jsonify(user.serialize()), 200

@app.route("/roles", methods=['POST', 'GET', 'PUT'])
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
    
    if request.method == 'PUT':
        rol = request.json.get("rol")
        id = request.json.get("id")

        if not rol:
            return jsonify({"msg": "rol is required"}), 400
        if not id:
            return jsonify({"msg": "id is required"}), 400
        
        id_role = Role.query.filter_by(id=id).first()

        if not id_role:
            return jsonify({"msg": "id does not exists"}), 404
        else:
            id_role.rol = rol
            id_role.update()
            return jsonify({"msg": "rol updated successfully"}), 404 

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

@app.route("/api/planes/<int:id>", methods=['DELETE'])  
def plan_delete(id):
    plan = Plan.query.filter_by(id=id).first()
    if not plan:
        return jsonify({"msg": "Este plan no existe"}), 404
    else:
        plan.delete()
        return jsonify({"msg": "Plan borrado"})

@app.route("/api/planes/<int:id>", methods=['PUT'])  
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

@app.route("/api/info-contacto", methods=['POST', 'GET'])
@app.route("/api/info-contacto/<email>", methods=['DELETE', "PUT", "PATCH"])
def info_Contacto(email=None):
    if request.method == 'GET':
        contactos = InfoContacto.query.all()

        if not contactos:
            return jsonify({"msg": "empty list"}), 404
        else:
            info = list(map(lambda contacto: contacto.serialize(), contactos))
            return jsonify(info), 200

    if request.method == 'POST':

        contact_name = request.json.get("name", None)
        contact_email = request.json.get("email", None)
        contact_phone = request.json.get("phone", None)
        contact_plan = request.json.get("plan", None)

        if not contact_name:
            return jsonify({"msg": "El nombre es necesario"}), 404
        if not contact_email:
            return jsonify({"msg": "El email es necesario"}), 404
        if not contact_phone:
            return jsonify({"msg": "El teléfono es necesario"}), 404
        if not contact_plan:
            return jsonify({"msg": "El plan es necesario"}), 404

        contacto_existente = InfoContacto.query.filter_by(email = contact_email).first()
        if contacto_existente:
            return jsonify({"msg": "Contacto ya existe"}), 400
        else:
            contacto = InfoContacto()
            contacto.name = contact_name
            contacto.email = contact_email
            contacto.phone = contact_phone
            contacto.plan = contact_plan
            contacto.save()

        return jsonify({"Msg": "Contacto Añadido"})

    if request.method == 'DELETE':
        contacto_existente = InfoContacto.query.filter(InfoContacto.email==email).first()
        if contacto_existente:
            contacto_existente.delete()
            return jsonify({"msg": "Plan borrado"})
        else:
            return jsonify({"msg": "Contacto no existe"})

    if request.method == 'PATCH':
        contact = InfoContacto.query.filter(InfoContacto.email==email).first()

        contact_state = request.json.get("state", None)

        if not contact:
            print(type(contact_state))
            return jsonify({"msg": "No existe ese email"})
        
        if type(contact_state) == bool:
            contact.state = contact_state
            contact.update()
            return jsonify({"Msg": "Plan Actualizado"})
        else:
            return jsonify({"msg": "El state debe ser True o False"})

       
        

   
@app.route("/crearedificio/<int:id>", methods=['DELETE', 'PUT'])
@app.route("/crearedificio", methods=['POST', 'GET'])
def crearEdificio(id=None):
    if request.method == 'GET':
        edificios = Edificio.query.all()
        if not edificios:
            return jsonify({"msg": "No hay edificios, usar metodo POST"}), 200
        else:
            edificios = list(map(lambda edificio: edificio.serialize(), edificios))
            return jsonify(edificios), 200
    if request.method == 'POST':
        nombre_edificio = request.json.get("nombre_edificio")
        direccion = request.json.get("direccion")
        nombre_administrador = request.json.get("nombre_administrador")
        telefono = request.json.get("telefono")
        correo = request.json.get("correo")
        numero_pisos = request.json.get("numero_pisos")
        numero_departamentos = request.json.get("numero_departamentos")
        total_bodegas = request.json.get("total_bodegas")
        total_estacionamientos = request.json.get("total_estacionamientos")
        inicio_contratacion = request.json.get("inicio_contratacion")
        termino_contrato = request.json.get("termino_contrato")
        dia_vencimiento = request.json.get("dia_vencimiento")
        plan_id = request.json.get("plan_id")
        username_id = request.json.get("username_id")

        plan = Edificio.query.filter_by(plan_id=plan_id).first()
        username = Edificio.query.filter_by(username_id=username_id).first()

        if not nombre_edificio:
            return ({"msg": "nombre_edificio es requerido"}), 404
        if not nombre_administrador:
            return ({"msg": "nombre_administrador es requerido"}), 404
        if not direccion:
            return ({"msg": "direccion es requerido"}), 404
        if not telefono:
            return ({"msg": "telefono es requerido"}), 404
        if not correo:
            return ({"msg": "correo es requerido"}), 404
        if not numero_pisos:
            return ({"msg": "numero_pisos es requerido"}), 404
        if not numero_departamentos:
            return ({"msg": "numero_departamentos es requerido"}), 404
        if not total_bodegas:
            return ({"msg": "total_bodegas es requerido"}), 404
        if not total_estacionamientos:
            return ({"msg": "total_estacionamientos es requerido"}), 404
        if not inicio_contratacion:
            return ({"msg": "inicio_contratacion es requerido"}), 404
        if not termino_contrato:
            return ({"msg": "termino_contrato es requerido"}), 404
        if not dia_vencimiento:
            return ({"msg": "dia_vencimiento es requerido"}), 404
        if int(dia_vencimiento) > 31:
            return jsonify({"msg": "el dia vencimiento no es valido"}), 400
        if not plan_id:
            return ({"msg": "plan_id es requerido"}), 404
        if not plan:
            return jsonify({"msg": "plan id incorrecto"}), 400 
        if not username_id:
            return ({"msg": "username_id es requerido"}), 404
        if not username:
            return jsonify({"msg": "usuario id incorrecto"}), 400

        
        edificio = Edificio()
        edificio.nombre_edificio = nombre_edificio
        edificio.nombre_administrador = nombre_administrador
        edificio.direccion = direccion
        edificio.telefono = telefono
        edificio.correo = correo
        edificio.numero_pisos = int(numero_pisos)
        edificio.numero_departamentos = int(numero_departamentos)
        edificio.total_bodegas = int(total_bodegas)
        edificio.total_estacionamientos = int(total_estacionamientos)
        edificio.inicio_contratacion = inicio_contratacion
        edificio.termino_contrato = termino_contrato
        edificio.dia_vencimiento = dia_vencimiento
        edificio.plan_id = int(plan_id)
        edificio.username_id = int(username_id)
        edificio.save()

        return jsonify({"msg": "Edificio creado"}), 200

    if request.method == 'DELETE':
        edificio = Edificio.query.filter_by(id=id).first()

        if not edificio:
            return jsonify({"msg": "El edificio no existe"}), 404
        else:
            edificio.delete()
            return jsonify({"msg": "El edificio ha sido eliminado exitosamente"}), 200

    if request.method == 'PUT':
        edificio = Edificio.query.filter_by(id=id).first()

        if not edificio:
            return jsonify({"msg": "El edificio no existe"}), 404
        
        else:
            nombre_edificio = request.json.get("nombre_edificio")
            direccion = request.json.get("direccion")
            nombre_administrador = request.json.get("nombre_administrador")
            telefono = request.json.get("telefono")
            correo = request.json.get("correo")
            numero_pisos = request.json.get("numero_pisos")
            numero_departamentos = request.json.get("numero_departamentos")
            total_bodegas = request.json.get("total_bodegas")
            total_estacionamientos = request.json.get("total_estacionamientos")
            inicio_contratacion = request.json.get("inicio_contratacion")
            termino_contrato = request.json.get("termino_contrato")
            dia_vencimiento = request.json.get("dia_vencimiento")
            plan_id = request.json.get("plan_id")
            username_id = request.json.get("username_id")

            if not nombre_edificio:
                return ({"msg": "nombre_edificio es requerido"})
            if not nombre_administrador:
                return ({"msg": "nombre_administrador es requerido"})
            if not direccion:
                return ({"msg": "direccion es requerido"})
            if not telefono:
                return ({"msg": "telefono es requerido"})
            if not correo:
                return ({"msg": "correo es requerido"})
            if not numero_pisos:
                return ({"msg": "numero_pisos es requerido"})
            if not numero_departamentos:
                return ({"msg": "numero_departamentos es requerido"})
            if not total_bodegas:
                return ({"msg": "total_bodegas es requerido"})
            if not total_estacionamientos:
                return ({"msg": "total_estacionamientos es requerido"})
            if not inicio_contratacion:
                return ({"msg": "inicio_contratacion es requerido"})
            if not termino_contrato:
                return ({"msg": "termino_contrato es requerido"})
            if not dia_vencimiento:
                return ({"msg": "dia_vencimiento es requerido"})
            if not plan_id:
                return ({"msg": "plan_id es requerido"})
            if not username_id:
                return ({"msg": "username_id es requerido"})
        
            edificio.nombre_edificio = nombre_edificio
            edificio.nombre_administrador = nombre_administrador
            edificio.direccion = direccion
            edificio.telefono = telefono
            edificio.correo = correo
            edificio.numero_pisos = int(numero_pisos)
            edificio.numero_departamentos = int(numero_departamentos)
            edificio.total_bodegas = int(total_bodegas)
            edificio.total_estacionamientos = int(total_estacionamientos)
            edificio.inicio_contratacion = inicio_contratacion
            edificio.termino_contrato = termino_contrato
            edificio.dia_vencimiento = dia_vencimiento
            edificio.plan_id = int(plan_id)
            edificio.username_id = int(username_id)
            edificio.update()

            return jsonify({"msg": "Edificio actualizado correctamente"}), 200



if __name__ == "__main__":
    manager.run()

