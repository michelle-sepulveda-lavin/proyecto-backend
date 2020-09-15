from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
import json

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)


    def serialize(self):
        return{
            "id": self.id,
            "username": self.username,
            "rol_id": self.rol_id
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