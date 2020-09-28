import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from config import Development
from models import db, User, Role, Plan, Edificio, InfoContacto, Departamento, DepartamentoUsuario, Conserje, Bodega, Estacionamiento, GastoComun, Paquete, MontosTotales, Boletin
import json
import os
import sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from libs.functions import allowed_file
from io import TextIOWrapper
import csv

ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg'}
ALLOWED_EXTENSIONS_FILES = {'pdf', 'csv'}

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
@app.route("/register/<rol_id>", methods=['GET'])
def register(id=None, rol_id=None):
    if request.method == 'POST':
        username = request.json.get("username", None)
        password = request.json.get("password", None)
        rol_id = request.json.get("rol_id", None)
        email = request.json.get("email", None)
        edificio_id = request.json.get("edificio_id", None)

        if not password:
            return jsonify({"msg": "password is required"}), 400
        if not rol_id:
            return jsonify({"msg": "rol_id is required"})
        if not email:
            return jsonify({"msg": "email is required"})
        if not username:
            return jsonify({"msg": "username is required"}), 400

        user = User.query.filter_by(username=username).first()

        if user:
            return jsonify({"msg": "user already exists"}), 400
        
        rolId = Role.query.filter_by(id=rol_id).first()
        rol = Role.query.filter_by(rol=rol_id).first()

        if rolId:
            user = User()
            user.username = username
            user.password = generate_password_hash(password)
            user.rol_id = rol_id
            user.edificio_id = edificio_id
            user.email = email
            user.save()

            expire_in = datetime.timedelta(days=1)
            data = {
                "access_token": create_access_token(identity=user.email, expires_delta=expire_in),
                "user": user.serialize()
            }
            return jsonify(data), 200
        if rol:
            roleID = rol.id

            user = User()
            user.username = username
            user.password = generate_password_hash(password)
            user.rol_id = roleID
            user.edificio_id = edificio_id
            user.email = email
            user.save()

            expire_in = datetime.timedelta(days=1)
            data = {
                "access_token": create_access_token(identity=user.email, expires_delta=expire_in),
                "user": user.serialize()
            }
            return jsonify(data), 200

    if request.method == 'GET':

        if not rol_id:
            usuarios = User.query.all()
            if not usuarios:
                return jsonify({"msg": "Lista vacia, usar metodo POST"}), 404
            else:
                usuarios = list(map(lambda usuario: usuario.serialize(), usuarios))
                return jsonify(usuarios), 200

        if rol_id:
            rol_numero = Role.query.filter_by(rol=rol_id).first()
            role = User.query.filter_by(rol_id=rol_numero.id).all()
            if not rol_numero:
                return jsonify({"msg": "No existe rol"}), 404
            else:
                role = list(map(lambda rol: rol.serialize(), role))
                return jsonify(role), 200

    if request.method == 'PUT':

        password = request.json.get("password", None)
        username = request.json.get("username")
        email = request.json.get("email", None)
        edificio_id = request.json.get("edificio_id", None)

      
        """ if not password:
            return jsonify({"msg": "password is required"}), 400 """
        """ if not username:
            return jsonify({"msg": "username is required"}), 400
        """
        if not email:
            return jsonify({"msg": "email is required"}), 400 

        user = User.query.filter_by(email=email).first()
        
        user.edificio_id = edificio_id
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
            expire_in = datetime.timedelta(hours=1)
            data = {
            "access_token": create_access_token(identity=correo.id, expires_delta=expire_in),
            }
            mensaje2 = "Para recuperar tu contraseña, usa el siguiente "
            url = "http://localhost:3000/recuperacion-password/" + data["access_token"]
            mensaje = f"<html><head></head><body>Para recuperar tu contraseña, usa el siguiente <a href=\"{url}\">Link</a></body></html>"
            content = Content("text/html", mensaje)
            mail = Mail(from_email, to_email, subject, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            print(response.status_code)
            print(response.body)
            print(response.headers)
            return jsonify({"msg": "Se ha enviado un email para reestablecer la contraseña"}), 200

@app.route("/reset-password", methods=['POST'])
@jwt_required
def resetearPassword():
    contraseña = request.json.get("password")

    id = get_jwt_identity()
    user = User.query.get(id)
    if user:

        user.password = generate_password_hash(contraseña)
        user.save()
        expire_in = datetime.timedelta(days=1)
        data = {
            "access_token": create_access_token(identity=user.email, expires_delta=expire_in),
            "user": user.serialize()
        }
        return jsonify({"msg": "contraseña cambiada exitosamente"}), 200
    if not user:
        return jsonify({"msg": "usuario no encontrado"}), 404 

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
        contactos = InfoContacto.query.order_by(InfoContacto.id.asc()).all()

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

@app.route("/api/info-contacto/<int:id>", methods=['GET'])
def get_last_contacts(id):
    contact = InfoContacto.query.order_by(InfoContacto.id.desc()).limit(id).all()
    contacts = list(map(lambda contacto: contacto.serialize(), contact))
    if len(contacts) > 0:
        return jsonify(contacts)
    else:
        return jsonify({"msg": "No hay planes, por favor hacer método POST"})
        

   
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
        nombre_edificio = request.form.get("nombre_edificio")
        direccion = request.form.get("direccion")
        telefono = request.form.get("telefono")
        correo = request.form.get("correo") 
        numero_pisos = request.form.get("numero_pisos")
        numero_departamentos = request.form.get("numero_departamentos")
        total_bodegas = request.form.get("total_bodegas")
        total_estacionamientos = request.form.get("total_estacionamientos")
        inicio_contratacion = request.form.get("inicio_contratacion")
        termino_contrato = request.form.get("termino_contrato")
        dia_vencimiento = request.form.get("dia_vencimiento")
        plan_id = request.form.get("plan_id")

        plan = Plan.query.filter_by(id=plan_id).first()

        if not nombre_edificio:
            return ({"msg": "El nombre del edificio es obligatorio"}), 404
        if not direccion:
            return ({"msg": "Direccion es obligatoria"}), 404
        if not telefono:
            return ({"msg": "Telefono es obligatorio"}), 404 
        if not correo:
            return ({"msg": "Correo es obligatorio"}), 404
        if not numero_pisos:
            return ({"msg": "Numero de pisos es obligatorio"}), 404
        if not numero_departamentos:
            return ({"msg": "Numero de departamentos es obligatorio"}), 404
        if not total_bodegas:
            return ({"msg": "El total de bodegas es obligatorio"}), 404
        if not total_estacionamientos:
            return ({"msg": "El total deestacionamientos es obligatorio"}), 404
        if not inicio_contratacion:
            return ({"msg": "Inicio del contrato es obligatorio"}), 404
        if not termino_contrato:
            return ({"msg": "Termino del contrato es obligatorio"}), 404
        if not dia_vencimiento:
            return ({"msg": "Dia vencimiento gastos comunes es obligatorio"}), 404
        if int(dia_vencimiento) > 31:
            return jsonify({"msg": "El dia de vencimiento no es valido"}), 400
        if not plan_id:
            return ({"msg": "El plan es obligatorio"}), 404

        """ archivoCSV = request.files['archivoCSV']

        if 'archivoCSV' not in request.files:
            return jsonify({"msg": {"archivoCSV":"archivoCSV is required"}}), 400
        if archivoCSV.filename == '':
            return jsonify({"msg": {"archivoCSV":"archivoCSV is required"}}), 400
        
        filename_archivoCSV = "sin-archivoCSV.csv"
        if archivoCSV and allowed_file(archivoCSV.filename, ALLOWED_EXTENSIONS_FILES):
            filename_archivoCSV = secure_filename(archivoCSV.filename)
            archivoCSV.save(os.path.join(app.config['UPLOAD_FOLDER']+"/csv", filename_archivoCSV)) """
        
        edificio = Edificio()
        edificio.nombre_edificio = nombre_edificio
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
        """ edificio.archivoCSV = filename_archivoCSV """
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
            """ nombre_administrador = request.json.get("nombre_administrador")"""
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
            """ username_id = request.json.get("username_id") """

            if not nombre_edificio:
                return ({"msg": "nombre_edificio es requerido"})
            """ if not nombre_administrador:
                return ({"msg": "nombre_administrador es requerido"}) """
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
            """ if not username_id:
                return ({"msg": "username_id es requerido"}) """
        
            edificio.nombre_edificio = nombre_edificio
            """ edificio.nombre_administrador = nombre_administrador """
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
            """ edificio.username_id = int(username_id) """
            edificio.update()

            return jsonify({"msg": "Edificio actualizado correctamente"}), 200

@app.route("/crearedificio/<int:id>", methods=['GET'])
def get_edificio_by_id(id):
    edificio = Edificio.query.filter_by(id=id).first()
    if not edificio:
        return jsonify({"msg": "Edificio no existente"}), 400
    else:
        return jsonify(edificio.serialize()), 200   
        return jsonify(edificio.serialize()), 200
        
@app.route("/conserjes/<int:id>", methods=['DELETE', 'PATCH', 'GET'])
@app.route("/conserjes", methods=['POST', 'GET'])
def crearConserje(id=None):

    if request.method == 'GET':
        if id:
            conserje = Conserje.query.filter_by(id=id).first()
            if not conserje:
                return jsonify({"msg": "Conserje no existe"})
            return jsonify(conserje.serialize())

        conserjes = Conserje.query.all()
        if not conserjes:
            return jsonify({"msg": "No hay conserjes, usar metodo POST"}), 200
        else:
            conserjes = list(map(lambda conserje: conserje.serialize(), conserjes))
            return jsonify(conserjes), 200

    if request.method == 'POST':

        username = request.form.get("username", None)
        password = request.form.get("password", None)
        rol_id = request.form.get("rol_id", None)
        email = request.form.get("email", None)
        nombre = request.form.get("nombre", None)
        telefono = request.form.get("telefono", None)
        turno = request.form.get("turno", None)
        edificio_id = request.form.get("edificios_id", None)
        avatar = request.files.get('avatar')
        if not username:
            return ({"msg": "Nombre de usuario es requerido"}), 404
        if not password:
            return ({"msg": "Contraseña es requerida"}), 404
        if not rol_id:
            return ({"msg": "rol_id es requerido"}), 404 
        if not email:
            return ({"msg": "El correo es requerido"}), 404

        
        if not nombre:
            return ({"msg": "nombre es requerido"}), 404
        if not telefono:
            return ({"msg": "telefono es requerido"}), 404
        if not turno:
            return ({"msg": "turno es requerido"}), 404 
        if not edificio_id:
            return ({"msg": "edificio_id es requerido"}), 404


        user = User.query.filter_by(username=username).first()
        user_mail = User.query.filter_by(email=email).first()
        conserje_nombre = Conserje.query.filter_by(nombre=nombre).first()

        if conserje_nombre:
            return jsonify({"msg": "Conserje ya existe"}), 400

        if user_mail:
            return jsonify({"msg": "Correo ya registrado"}), 400
        if user:
            return jsonify({"msg": "Nombre usuario ya registrado"}), 400
        
        rolId = Role.query.filter_by(id=rol_id).first()

        if rolId:
            user = User()
            user.username = username
            user.password = generate_password_hash(password)
            user.rol_id = rol_id
            user.edificio_id = edificio_id
            user.email = email
            user.save()

        new_User = User.query.filter_by(email=email).first()
        
        if new_User:
            usuario_id = new_User.id

        
        filename = "sin-imagen.png"
        if avatar and allowed_file(avatar.filename, ALLOWED_EXTENSIONS_IMAGES):
            filename = secure_filename(avatar.filename)
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER']+"/avatares", filename))
        
        conserje = Conserje()
        conserje.nombre = nombre
        conserje.telefono = telefono
        conserje.turno = turno
        conserje.edificio_id = edificio_id
        conserje.usuario_id = usuario_id
        conserje.avatar = filename
        conserje.save()

        return jsonify({"msg": "Conserje creado"}), 200

    if request.method == 'DELETE':
        conserje = Conserje.query.filter_by(id=id).first()
        if not conserje:
            return jsonify({"msg": "Conserje no existe"})
        conserje.delete()
        return jsonify({"msg": "conserje borrado"})


    if request.method == 'PATCH':
        conserje = Conserje.query.filter_by(id=id).first()

        nombre = request.form.get("nombre", None)
        telefono = request.form.get("telefono", None)
        turno = request.form.get("turno", None)
        avatar = request.files.get('avatar')

        
        if not conserje:
            return jsonify({"msg": "No existe ese conserje"})
        
        if nombre:
            conserje.nombre = nombre
            conserje.update()
        if telefono:
            conserje.telefono = telefono
            conserje.update()
        if turno:
            conserje.turno = turno
            conserje.update()
        if avatar:
            filename = "sin-imagen.png"
            if avatar and allowed_file(avatar.filename, ALLOWED_EXTENSIONS_IMAGES):
                filename = secure_filename(avatar.filename)
                avatar.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/avatares", filename))
                conserje.avatar = filename
                conserje.update()
        
        return jsonify({"Msg": "Conserje Actualizado"})
 
        
@app.route("/conserjes/edificio/<int:id>", methods=['POST', 'GET', 'DELETE', 'PUT'])
def conserjes_edificio(id):
    if request.method == 'GET':
        conserjes = Conserje.query.filter_by(edificio_id=id)
        if not conserjes:
            return jsonify({"msg": "No hay conserjes en este edificio"})
        conserje = list(map(lambda cons: cons.serialize(), conserjes))
        return jsonify(conserje)
    
@app.route("/conserjes/estado-conserje/<int:id>", methods=['PATCH'])
def conserjes_estado(id):
    conserje = Conserje.query.filter_by(id=id).first()
    estado_conserje = request.json.get("estado_conserje", None)
    if not conserje:
        return jsonify({"msg": "No existe ese conserje"})

    if type(estado_conserje) == bool:
        conserje.state = estado_conserje
        conserje.update()

    return jsonify({"Msg": "Estado conserje Actualizado"})

@app.route("/info-departamento/<id>", methods=['POST', 'GET', 'DELETE'])
def departamento_by_id(id):
    if request.method == 'GET':
        departamentos = Departamento.query.filter_by(edificio_id=id).all()
        
        if not departamentos:
            return jsonify({"msg": "No hay departamentos, usar metodo POST"}), 404
        if departamentos:
            departamentos = list(map(lambda depto: depto.serialize(), departamentos))
            return jsonify((departamentos))

    if request.method == 'POST':
        edificio = Edificio.query.filter_by(id=id).first()
        if not edificio:
            return jsonify({"msg": "El edificio no existe"}), 404
        else:
            modelo = request.json.get("modelo")
            total = request.json.get("total")
            interior = request.json.get("interior")
            terraza = request.json.get("terraza")
            cantidad_total = request.json.get("cantidad_total")
            edificio_id = id

            if not modelo:
               return jsonify({"msg": "Modelo es requerido"}), 400
            if not total:
               return jsonify({"msg": "Superficie total es requerido"}), 400 
            if not interior:
               return jsonify({"msg": "Interior es requerido"}), 400 
            if not terraza:
               return jsonify({"msg": "Terraza es requerido"}), 400 
            if not cantidad_total:
               return jsonify({"msg": "Cantidad total de departamentos es requerido"}), 400

            departamento = Departamento()
            departamento.modelo = modelo
            departamento.total = total
            departamento.interior = interior
            departamento.terraza = terraza
            departamento.cantidad_total = cantidad_total
            departamento.edificio_id = id 
            
            departamento.save()

            return jsonify({"msg": "departamento creado exitosamente"}), 200
    
    if request.method == 'DELETE':
        departamento = Departamento.query.filter_by(id=id).first()

        if not departamento:
            return({"msg": "No existe el modelo de departamento señalado"}), 404
        if departamento:
            departamento.delete()
            return jsonify({"msg": "El modelo de departamento ha sido eliminado exitosamente"}), 200
            
@app.route("/departamentoUsuario", methods=['GET'])
@app.route("/departamentoUsuario/<id>", methods=['GET'])
def departamentoUsuario(id=None):
    if request.method == 'GET':
        if not id:
            departamentos = DepartamentoUsuario.query.all()

            if not departamentos:
                return jsonify({"msg": "No hay departamentos, usar metodo POST"}), 404
            else:
                departamentos = list(map(lambda dpto: dpto.serialize(), departamentos))
                return jsonify(departamentos), 200
        if id:
            departamento = DepartamentoUsuario.query.filter_by(id=id).first()
            
            if not departamento:
                return jsonify({"msg": "Departamento no existe"}), 404
            else:
                return jsonify(departamento.serialize()), 200

        
@app.route("/avatares/<avatar>")
def get_avatar(avatar):
    return send_from_directory(app.config['UPLOAD_FOLDER']+"/avatares", avatar)

@app.route("/comprobantes/<comprobante>")
def get_comprobante(comprobante):
    return send_from_directory(app.config['UPLOAD_FOLDER']+"/comprobantes", comprobante)

@app.route("/pagosgastos/<pago>")
def get_pago(pago):
    return send_from_directory(app.config['UPLOAD_FOLDER']+"/pagos", pago)



@app.route("/departamentoUsuarioEdificio/<id>", methods=['GET', 'POST', 'DELETE'])
def departamentoUsuario_by_Edificio(id=None):
    if request.method == 'GET':
        departamentos = DepartamentoUsuario.query.filter_by(edificio_id=id).all()
            
        if not departamentos:
            return jsonify({"msg": "Departamentos no existen"}), 404
        else:
            departamentos = list(map(lambda dpto: dpto.serialize(), departamentos))
            return jsonify(departamentos), 200
    
    if request.method == 'POST':
        edificio = Edificio.query.filter_by(id=id).first()

        if not edificio:
            return jsonify({"msg": "Edificio no existe"}), 404
        else:
            numero_departamento = request.json.get("numero_departamento")
            estado = request.json.get("estado")  
            residente = request.json.get("residente")  
            bodega_id = request.json.get("bodega_id")  
            estacionamiento_id = request.json.get("estacionamiento_id")  
            piso = request.json.get("piso")  
            modelo_id = request.json.get("modelo_id")   

            if not numero_departamento:
                return jsonify("msg", "numero_departamento es requerido"), 400
            if not estado:
                return jsonify("msg", "estado es requerido"), 400
            """ if not residente:
            return jsonify("msg", "residente es requerido"), 400  """
            """ if not bodega:
            return jsonify("msg", "bodega es requerido"), 400  
            if not estacionamiento:
            return jsonify("msg", "estacionamiento es requerido"), 400 """
            if not piso:
                return jsonify("msg", "piso es requerido"), 400
            if not modelo_id:
                return jsonify("msg", "modelo_id es requerido"), 400 

            numero = DepartamentoUsuario.query.filter_by(numero_departamento=numero_departamento, edificio_id=id).first()

            if numero:
                return jsonify({"msg": "El numero de departamento ya existe"}), 400
            else:
                modelo = Departamento.query.filter_by(modelo=modelo_id).first()

                departamento = DepartamentoUsuario()
                departamento.numero_departamento = numero_departamento
                departamento.estado = estado
                departamento.residente = residente
                departamento.bodega_id = bodega_id
                departamento.estacionamiento_id = estacionamiento_id
                departamento.piso = piso
                departamento.edificio_id = id
                departamento.modelo_id = modelo.id
                departamento.save()

                return jsonify({"msg" : "departamento de usuario creado exitosamente"}), 200
    
    if request.method == 'DELETE':
        departamento = DepartamentoUsuario.query.filter_by(id=id).first()

        if not departamento:
            return jsonify({"msg": "Departamento no existe"}), 404
        if departamento:
            departamento.delete()
            return jsonify({"msg": "El departamento ha sido eliminado exitosamente"}), 200

@app.route("/usuarios-edificio/<id>", methods=['GET'])
def usuarios_by_Edificio(id):
    if request.method == 'GET':
        usuarios = User.query.filter_by(edificio_id=int(id)).all()
        if not usuarios:
            return jsonify({"msg": "No existen usuarios en el edificio"}), 404
        if usuarios:
            usuarios = list(map(lambda usuario: usuario.serialize(), usuarios))
            return jsonify(usuarios)

@app.route("/add-residente/<id>", methods=['PUT'])
def add_user_to_building(id):
    departamento = DepartamentoUsuario.query.filter_by(id=id).first()

    if not departamento:
        return jsonify({"msg": "Departamento de usuario no encontrado"}), 404
    if departamento:
        residente = request.json.get("residente")
        estado = request.json.get("estado")

        if residente == "default":
            departamento.residente = None
            departamento.estado = estado
            departamento.update()
            return jsonify({"msg": "Departamento actualizado exitosamente"}), 200

        residenteID = User.query.filter_by(id=residente).first()
            
        if not residenteID:
            residenteName = User.query.filter_by(username=residente).first()
                
            if residente:
                departamento.residente = residenteName.id
                departamento.estado = estado
                departamento.update()
                return jsonify({"msg": "Departamento actualizado exitosamente"}), 200
            if not residenteName:
                departamento.residente = None
                departamento.estado = estado
                departamento.update()
                return jsonify({"msg": "Departamento actualizado exitosamente"}), 200
        else:
            departamento.residente = residenteID.id
            departamento.estado = estado
            departamento.update()
            return jsonify({"msg": "Departamento actualizado exitosamente"}), 200

@app.route("/add-bodega/<id>", methods=['POST'])
def add_bodega(id):
    bodega = Bodega.query.filter_by(edificio_id=id).first()

    if bodega:
        return jsonify({"msg": "La bodega ya fue creada"}), 404
    if not bodega:
        total_superficie = request.json.get("total_superficie")
        cantidad_total = request.json.get("cantidad_total")

        if not total_superficie:
            return jsonify({"msg": "total_superficie es obligatorio"}), 404
        if not cantidad_total:
            return jsonify({"msg": "total_superficie es obligatorio"}), 404

        new_bodega = Bodega()
        new_bodega.total_superficie = int(total_superficie)
        new_bodega.cantidad_total = int(cantidad_total)
        new_bodega.edificio_id = id
        new_bodega.save()

        return jsonify({"msg": "La bodega creada exitosamente"}), 404

@app.route("/add-estacionamiento/<id>", methods=['POST'])
def add_estacionamiento(id):
    estacionamiento = Estacionamiento.query.filter_by(edificio_id=id).first()

    if estacionamiento:
        return jsonify({"msg": "El estacionamiento ya fue creada"}), 404
    if not estacionamiento:
        total_superficie = request.json.get("total_superficie")
        cantidad_total = request.json.get("cantidad_total")

        if not total_superficie:
            return jsonify({"msg": "total_superficie es obligatorio"}), 404
        if not cantidad_total:
            return jsonify({"msg": "total_superficie es obligatorio"}), 404

        new_estacionamiento = Estacionamiento()
        new_estacionamiento.total_superficie = (total_superficie)
        new_estacionamiento.cantidad_total = (cantidad_total)
        new_estacionamiento.edificio_id = id
        new_estacionamiento.save()

        return jsonify({"msg": "El estacionamiento creada exitosamente"}), 404

@app.route("/estacionamientos/<id>", methods=['GET'])
def estacionamiento(id):
    estacionamiento = Estacionamiento.query.filter_by(edificio_id=id).first()

    if not estacionamiento:
        return jsonify({"msg": "Los estacionamientos no han sido creados"}), 404
    if estacionamiento:
        return jsonify(estacionamiento.serialize()), 200

@app.route("/bodegas/<id>", methods=['GET'])
def bodegas(id):
    bodega = Bodega.query.filter_by(edificio_id=id).first()

    if not bodega:
        return jsonify({"msg": "Las bodegas no han sido creadas"}), 404
    if bodega:
        return jsonify(bodega.serialize()), 200

@app.route("/delete-bodega-edificio/<id>", methods=['DELETE'])
def delete_bodegas(id):
    bodega = Bodega.query.filter_by(edificio_id=id).first()

    if not bodega:
        return jsonify({"msg": "Las bodegas no existe"}), 404
    if bodega:
        bodega.delete()
        return jsonify({"msg": "Bodega eliminada"}), 200

@app.route("/delete-estacionamiento-edificio/<id>", methods=['DELETE'])
def delete_estacionamiento(id):
    estacionamiento = Estacionamiento.query.filter_by(edificio_id=id).first()

    if not estacionamiento:
        return jsonify({"msg": "Estacionamientos no existen"}), 404
    if estacionamiento:
        estacionamiento.delete()
        return jsonify({"msg": "Estacionamiento eliminado"}), 200

@app.route("/paqueteria/<id>", methods=['POST', 'GET', 'PUT'])
def paqueteria(id):
    if request.method == 'POST':
        edificio = Edificio.query.filter_by(id=id).first()
        
        if not edificio:
            return jsonify({"msg": "El edificio no existe"}), 404
        else:
            numero_departamento = request.json.get("numero_departamento")

            if not numero_departamento:
                return jsonify({"msg": "Numero de departamento es obligatorio"}), 400
            else:
                departamento = DepartamentoUsuario.query.filter_by(numero_departamento=numero_departamento, edificio_id=id).first()

                if not departamento:
                    return jsonify({"msg": "El departamento no existe"}), 404
                else:
                    paquete = Paquete()
                    paquete.departamento_id = departamento.id
                    paquete.edificio_id = id
                    paquete.save()

                    return jsonify({"msg": "Paquete agregado exitosamente"}), 200
    if request.method == 'GET':
        paquetes = Paquete.query.filter_by(edificio_id=id, estado=False).all()
        
        if not paquetes:
            return jsonify({"msg": "El edificio no tiene paquetes"}), 400
        else:
            paquetes = list(map(lambda pqte: pqte.serialize(), paquetes))
            return jsonify(paquetes), 200
    
    if request.method == 'PUT':
        paquete = Paquete.query.filter_by(id=id).first()
        
        if not paquete:
            return jsonify({"msg": "El paquete no existe"}), 404
        else:
            estado = request.json.get("estado")
            
            if not estado:
                return jsonify({"msg": "El estado es requerido"}), 400
            else:
                paquete.estado = estado
                paquete.update()

                return jsonify({"msg": "El paquete fue ha sido entregado"}), 200


            


@app.route("/boletin", methods=['GET','POST'])
@app.route("/boletin/<int:edificio>", methods=['GET', 'PATCH', 'PUT', 'DELETE'])
@app.route("/boletin/<int:edificio>/<int:id>", methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def boletin(id = None, edificio = None):
    # asunto = request.json['asunto'],
    # body = request.json['body']
    if request.method == 'GET':
        
        if edificio:
            boletines_edificio = Boletin.query.get(edificio_id=edificio)
            if not boletines_edificio:
                return jsonify({"msg": "boletin no encontrado"}), 400
            else:
                boletines_edi = list(map(lambda boletin: boletin.serialize(), boletines_edificio))
                return jsonify(boletines_edi), 200

        if id is not None:
            boletin = Boletin.query.get(edificio_id = edificio, id = id)
            if boletin:
                return jsonify(boletin.serialize()), 200
            else:
                return jsonify({"msg": "boletin no encontrado"}), 400
                
        
        boletines = Boletin.query.all()
        boletines = list(map(lambda boletin: boletin.serialize(), boletines))
        return jsonify(boletines), 200
        

    if request.method == 'POST':
        asunto = request.json.get("asunto", None)
        body = request.json.get("body", None)
        edificio_id = request.json.get("edificio_id", None)

        if not asunto:
            return jsonify({"error": "Asunto es requerido"}), 400
        if not body:
            return jsonify({"error": "Body es requerido"}), 400

        boletin = Boletin()
        boletin.asunto = asunto
        boletin.body = body
        boletin.edificio_id = edificio_id
        boletin.save()

        return jsonify(boletin.serialize()), 201

    if request.method == 'PATCH':
        boletin_estado = Boletin.query.filter_by(edificio_id = edificio, id=id).first()

        estado = request.json.get("estado", None)
               
        if not boletin_estado:
            return jsonify({"msg": "No existe ese boletin"})
        
        if type(estado) == bool:
            boletin_estado.estado = estado
            boletin_estado.update()

        return jsonify({"Msg": "Estado boletin Actualizado"})

    # if request.method == 'PUT':
    #     asunto = request.json.get("asunto", None)
    #     body = request.json.get("body", None)

    #     if not asunto:
    #         return jsonify({"error": "Asunto es requerido"}), 400
    #     if not body:
    #         return jsonify({"error": "Body es requerido"}), 400

    #     boletin = Boletin()
    #     boletin.asunto = asunto
    #     boletin.body = body
    #     boletin.update()

    #     return jsonify(boletin.serialize()), 201

    # if request.method == 'DELETE':
    #     boletin = Boletin.query.get(id)

    #     if not asunto:
    #         return jsonify({"msg": "Boletin es requerido"}), 400
        
    #     boletin.delete()

    #     return jsonify({"msg": "Boletin borrado exitosamente"}), 200


@app.route("/gastoscomunes/", methods=['POST', 'GET', 'DELETE', 'PUT'])
def gastos_comunes():
    
    if request.method == 'POST':
       
        month = request.form.get("month")
        year =  request.form.get("year")
        monto =  request.form.get("monto")
        departamento_id = request.form.get("departamento_id")
        edificio_id = request.form.get("edificio_id")
        comprobante = request.files.get('comprobante')
        montoTotal = request.form.get("montoTotal")


        if not month:
            return jsonify({"msg": "El mes es requerido"}), 400
        if not year:
            return jsonify({"msg": "El año es requerido"}), 400 
        if not monto:
            return jsonify({"msg": "El monto es requerido"}), 400 
        if not departamento_id:
            return jsonify({"msg": "El id del departamento es requerido"}), 400
        if not edificio_id:
            return jsonify({"msg": "El id del edificio es requerido"}), 400
        if not comprobante:
            return jsonify({"msg": "El comprobante es requerido"}), 400
        if not montoTotal:
            return jsonify({"msg": "El monto total es requerido"}), 400
            
        edificio = Edificio.query.filter_by(id=edificio_id).first()
        if not edificio:
            return jsonify({"msg": "No existe el edificio"}), 400

        filename = "sin-comprobante.pdf"
        if comprobante and allowed_file(comprobante.filename, ALLOWED_EXTENSIONS_FILES):
            filename = secure_filename(comprobante.filename)
            comprobante.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/comprobantes", filename))

        montos_mes = MontosTotales.query.filter_by(edificio_id=edificio_id, month=month, year=year).first()
        if not montos_mes:
           
            monto_total = MontosTotales()
            monto_total.month = month
            monto_total.year = year
            monto_total.monto = montoTotal
            monto_total.comprobante = filename
            monto_total.departamento_id = departamento_id
            monto_total.edificio_id = edificio_id
            monto_total.save()

        gastos_depto = GastoComun.query.filter_by(month=month, departamento_id=departamento_id, year=year).first()

        if gastos_depto:
            return jsonify({"msg": "No puedes sobreescribir los gastos comunes del mes"}), 400

        gasto_comun = GastoComun()
        gasto_comun.month = month
        gasto_comun.year = year
        gasto_comun.monto = monto
        gasto_comun.departamento_id = departamento_id
        gasto_comun.edificio_id = edificio_id
        
        gasto_comun.save()

        return jsonify({"msg": "Gasto comun creado exitosamente"}), 200

@app.route("/gastoscomunes/edificio/<int:id>", methods=['GET', 'DELETE'])
@app.route("/gastoscomunes/edificio/<int:id>/<int:mes>/<int:year>", methods=['GET', 'DELETE'])
@app.route("/gastoscomunes/edificio/<int:id>/<int:mes>", methods=['GET', 'DELETE'])
def gastos_edificio(id, mes = None, year = None):

    if request.method == 'GET':

        if year:
            gastomesyear = GastoComun.query.filter_by(edificio_id=id, month=mes, year=year).all()
            
            if not gastomesyear:
                return jsonify({"msg": "No hay gastos comunes para este mes y año"})
        
            gastosmesyear = list(map(lambda gastocomun: gastocomun.serialize(), gastomesyear))

            return jsonify(gastosmesyear), 200


        if mes:
            gastomes = GastoComun.query.filter_by(edificio_id=id, month=mes).all()
            
            if not gastomes:
                return jsonify({"msg": "No hay gastos comunes para este edificio o mes"})
        
            gastosmes = list(map(lambda gastocomun: gastocomun.serialize(), gastomes))

            return jsonify(gastosmes), 200

        gasto = GastoComun.query.filter_by(edificio_id=id).all()
        
        if not gasto:
            return jsonify({"msg": "no hay gastos comunes para este edificio"})
        
        gastos = list(map(lambda gastocomun: gastocomun.serialize(), gasto))
    
        return jsonify(gastos), 200

    if request.method == 'DELETE':

        gasto = GastoComun.query.filter_by(edificio_id=id).first()
                
        if not gasto:
            return jsonify({"msg": "no hay gastos comunes para este edificio"})
                
        gasto.delete()

        return jsonify({"msg": "Gastos comunes del edificio borrados"}), 200


@app.route("/gastoscomunes/depto/<int:edificio>/<int:depto>/", methods=['GET', 'DELETE'])
def gastos_depto(edificio, depto):
     if request.method == 'GET':

            numero_id = DepartamentoUsuario.query.filter_by(numero_departamento=depto).first()
            
            if not numero_id:
                return jsonify({"msg": "No existe el departamento"})

            numero_depto = numero_id.id

            gastodepto = GastoComun.query.filter_by(edificio_id=edificio, departamento_id=numero_depto).order_by(GastoComun.year.desc(), GastoComun.month.desc()).all()
            
            if not gastodepto:
                return jsonify({"msg": "No hay gastos comunes para departamento"})
        
            gastosdeldepto = list(map(lambda gastocomun: gastocomun.serialize(), gastodepto))

            return jsonify(gastosdeldepto), 200

@app.route("/gastoscomunes/depto/<int:edificio>/<int:depto>/<int:mes>/<int:year>", methods=['PATCH'])
def estado_gasto(edificio, depto, mes, year):

    estado = request.form.get("estado")
    pago = request.files.get('pago')

    filename = "sin-pago.pdf"
    if pago and allowed_file(pago.filename, ALLOWED_EXTENSIONS_FILES):
        filename = secure_filename(pago.filename)
        pago.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/pagos", filename))

    gasto_comun = GastoComun.query.filter_by(edificio_id=edificio, departamento_id=depto, month=mes, year=year).first()
        
    if not gasto_comun:
        return jsonify({"msg": "No existe ese gasto común"})
    
    if estado:
        gasto_comun.estado = estado
        gasto_comun.update()
    if pago:
        gasto_comun.pago = filename
        gasto_comun.update()
         
    return jsonify({"Msg": "Gasto común actualizado"})
 


@app.route("/montostotales/edificio/<int:id>", methods=['GET', 'DELETE'])
@app.route("/montostotales/edificio/<int:id>/<int:mes>", methods=['GET', 'DELETE'])
def montos_totales(id, mes = None):

    if request.method == 'GET':

        monto_total = MontosTotales.query.filter_by(edificio_id=id).order_by(MontosTotales.year.desc(), MontosTotales.month.desc()).all()
            
        if not monto_total:
            return jsonify({"msg": "No hay montos totales para este edificio"})
        
        montos = monto_total = list(map(lambda monto: monto.serialize(), monto_total))

        return jsonify(montos), 200

    if request.method == 'DELETE':

        montos = MontosTotales.query.filter_by(edificio_id=id, month= mes).first()
                
        if not montos:
            return jsonify({"msg": "no hay montos para este edificio"})
                
        montos.delete()

        return jsonify({"msg": "Monto total del edificio borrado"}), 200

@app.route("/infoDepartamentoUsuario/<id>", methods=['GET'])
def depto_usuario(id):
    departamento_usuario = DepartamentoUsuario.query.filter_by(residente=id).first()
    if not departamento_usuario:
        return jsonify({"msg": "No existe departamento para este usuario"}), 400
        
    return jsonify(departamento_usuario.serialize()), 200

@app.route("/paqueteriaUsuario/<id>", methods=['GET'])
def dpto_usuario_paqueteria(id):
    paquetes = Paquete.query.filter_by(departamento_id=id, estado=False).all()

    if not paquetes:
        return jsonify({"msg": "no existen paquetes para este edificio"})
    else:
        paquetes = list(map(lambda paquete: paquete.serialize(), paquetes))
        return jsonify(paquetes), 200

if __name__ == "__main__":
    manager.run()






