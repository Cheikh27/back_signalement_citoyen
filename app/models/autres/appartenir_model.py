from datetime import datetime

from app import db


class Appartenir(db.Model):
    __tablename__ = 'appartenirs'
    IDappartenir = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création


    # Clé étrangère vers Citoyen et Groupe
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    groupeID = db.Column(db.Integer, db.ForeignKey('groupes.IDgroupe'), nullable=False)

    # Relation avec Citoyen (une Publication appartient à un Citoyen)
    # La relation 'citoyen' est définie dans le modèle Citoyen via backref

    def __repr__(self):
        return f"<Appartenir {self.IDappartenir}>"