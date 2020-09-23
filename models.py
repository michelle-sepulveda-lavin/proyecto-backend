from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
import json

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    edificio_id = db.Column(db.Integer, db.ForeignKey('edificios.id'), nullable=True)
    departamentosUsuarios = db.relationship("DepartamentoUsuario", backref="user")
    conserje = db.relationship("Conserje", backref="users")

    def serialize(self):
        return{
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "rol": {
                "id": self.role.id,
                "name": self.role.rol
                },
            "edificio": self.edificio_id
        }


    def serialize_con_edificio(self):
        return{
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "rol": {
                "id": self.role.id,
                "name": self.role.rol
                },
            "edificio": {
                "id": self.edificio.id,
                "name": self.edificio.nombre_edificio
            }
        }       
        
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Plan(db.Model):
    __tablename__ = "planes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=True, default=None)
    price = db.Column(db.Integer, nullable=False)
    frecuencia = db.Column(db.String(150), nullable=False)
    edificios = db.relationship("Edificio", backref="plane")
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "body": json.loads(self.body),
            "price": self.price,
            "frecuencia": self.frecuencia
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    rol = db.Column(db.String(120), nullable=False, unique=True)
    users = db.relationship("User", backref="role")



    def serialize(self):
        return{
            "id": self.id,
            "rol": self.rol
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

""" TABLA DE CLIENTES A CONTACTAR """

class InfoContacto(db.Model):
    __tablename__ = "infoContacto"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.Integer, nullable=False)
    state = db.Column(db.Boolean, nullable=True, default=True)
    plan = db.Column(db.String(250), nullable=False)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "plan": self.plan,
            "state": self.state
        }
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

            
class Edificio(db.Model):
    __tablename__ = "edificios"
    id = db.Column(db.Integer, primary_key=True)
    nombre_edificio = db.Column(db.String(120), nullable=False)
    direccion = db.Column(db.String(120), nullable=False)
    """nombre_administrador = db.Column(db.String(120), nullable=True)"""
    telefono = db.Column(db.String(12), nullable=False)
    correo = db.Column(db.String(120), nullable=False)
    numero_pisos = db.Column(db.Integer, nullable=False)
    numero_departamentos = db.Column(db.Integer, nullable=False)
    total_bodegas = db.Column(db.Integer, nullable=False)
    total_estacionamientos = db.Column(db.Integer, nullable=False)
    inicio_contratacion = db.Column(db.String(120), nullable=False)
    termino_contrato = db.Column(db.String(120), nullable=False)
    dia_vencimiento = db.Column(db.String(120), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('planes.id'), nullable=False)
    archivoCSV = db.Column(db.String(100), default=None)
    users = db.relationship("User", backref="edificio")
    conserjes = db.relationship("Conserje", backref="edificio")
    departamentos = db.relationship("Departamento", backref="edificio")
    departamentosUsuarios = db.relationship("DepartamentoUsuario", backref="edificio")

    def serialize(self):
        return{
            "id": self.id,
            "nombre_edificio": self.nombre_edificio,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "correo": self.correo, 
            "numero_pisos": self.numero_pisos,
            "numero_departamentos": self.numero_departamentos,
            "total_bodegas": self.total_bodegas,
            "total_estacionamientos": self.total_estacionamientos,
            "inicio_contratacion": self.inicio_contratacion,
            "termino_contrato": self.termino_contrato,
            "dia_vencimiento": self.dia_vencimiento,
            "plan_id": self.plan_id,
            "archivoCSVv": self.archivoCSV
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class Conserje(db.Model):
    __tablename__ = "conserjes"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(120), nullable=False)
    turno = db.Column(db.String(120), nullable=False)
    avatar = db.Column(db.String(100), nullable=True, default="sin-imagen.png")
    edificio_id = db.Column(db.Integer, db.ForeignKey('edificios.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    state = db.Column(db.Boolean, nullable=True, default=False)



    def serialize(self):
        return {
            "id": self.id,
            "avatar": self.avatar,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "turno": self.turno,
            "edificio": {
                "id": self.edificio.id,
                },
            "estado": self.state,
            "usuario": {
                "username": self.users.username,
                "email": self.users.email,
                "usuario_id": self.users.rol_id
            }
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()        

        
class Departamento(db.Model):
    __tablename__ = "departamentos"
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(120), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    interior = db.Column(db.Integer, nullable=False)
    terraza = db.Column(db.Integer, nullable=False)
    cantidad_total = db.Column(db.Integer, nullable=False)
    edificio_id = db.Column(db.Integer, db.ForeignKey('edificios.id'), nullable=True)
    departamentosUsuarios = db.relationship("DepartamentoUsuario", backref="departamento")

    def serialize(self):
        return{
            "id": self.id,
            "modelo": self.modelo,
            "total": self.total,
            "interior": self.interior,
            "terraza": self.terraza, 
            "cantidad_total": self.cantidad_total,
            "edificio_id": self.edificio_id,
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()        

class DepartamentoUsuario(db.Model):
    __tablename__ = "departamentosUsuarios"
    id = db.Column(db.Integer, primary_key=True)
    numero_departamento = db.Column(db.String(120), nullable=False)
    estado = db.Column(db.String(120), nullable=False)    
    residente = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    bodega = db.Column(db.String(120), nullable=True) 
    estacionamiento = db.Column(db.String(120), nullable=True)
    piso = db.Column(db.Integer, nullable=True)
    edificio_id = db.Column(db.Integer, db.ForeignKey('edificios.id'), nullable=False)
    modelo_id = db.Column(db.Integer, db.ForeignKey('departamentos.id'), nullable=False) 

    def serialize(self):
        return{
            "id": self.id,
            "numero_departamento": self.numero_departamento,
            "estado": self.estado,
            "residente": {
                "id": self.user.id,
                "name": self.user.username,
                "email": self.user.email
            } if self.residente else {"id": self.residente},
            "bodega": self.bodega,
            "estacionamiento": self.estacionamiento,
            "piso": self.piso,
            "edificio": {
                "id": self.edificio.id,
                "name": self.edificio.nombre_edificio
            },
            "modelo": {
                "id": self.departamento.id,
                "name": self.departamento.modelo
            } 
        }
    def serialize_con_usuario(self):
        return{
            "id": self.id,
            "numero_departamento": self.numero_departamento,
            "estado": self.estado,
            "residente": {
                "id": self.user.id,
                "name": self.user.username
                }, 
            "bodega": self.bodega,
            "estacionamiento": self.estacionamiento,
            "edificio_id": self.edificio_id,
            "modelo_id": self.modelo_id,
        }
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()  
