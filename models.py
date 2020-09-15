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
        db.session.commit(self)

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
        db.session.commit(self)

    def delete(self):
        db.session.delete(self)
        db.session.commit()