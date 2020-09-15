from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
import json

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