from datetime import datetime
from app import db



class Signature(db.Model):
    __tablename__ = 'signatures'
    IDsignature = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    nbSignature = db.Column(db.Integer, nullable=True)  # Date de création


    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    petitionID = db.Column(db.Integer, db.ForeignKey('petitions.IDpetition'), nullable=False)

    # Relation avec Citoyen (une Publication appartient à un Citoyen)
    # La relation 'citoyen' est définie dans le modèle Citoyen via backref

    def __repr__(self):
        return f"<reaction signature => ID :{self.IDsignature}, dateCreated:{self.dateCreated}, nbSignature:{self.nbSignature} >"

