from app import db

from datetime import datetime
import enum
from sqlalchemy import Enum


class CibleEnum(enum.Enum):
    groupe = "groupe"
    actualite = "actualite"

class Petition(db.Model):
    __tablename__ = 'petitions'
    IDpetition = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    nbSignature = db.Column(db.Integer, nullable=True)
    nbPartage = db.Column(db.Integer, nullable=True )
    dateFin = db.Column(db.DateTime, nullable=True)  

    objectifSignature = db.Column(db.Integer, nullable=True)
    titre = db.Column(db.String(100), nullable=False)
    cible = db.Column(Enum(CibleEnum), nullable=False, default=CibleEnum.actualite)  

    IDmoderateur = db.Column(db.Integer, nullable=True)

    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  
    is_deleted = db.Column(db.Boolean, default=False) 

    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)

    Signature = db.relationship('Signature', backref='petitions', lazy=True)
    PartagerPetition = db.relationship('PartagerPetition', backref='petitions', lazy=True)
    CommentairePetition = db.relationship('CommentairePetition', backref='petitions', lazy=True)
    # Publication = db.relationship('Publication', backref='petitions', lazy=True)

    def __repr__(self):
        return f"<Petition ID: {self.IDpetition}, description: {self.description},nbPartage: {self.nbPartage},dateFin: {self.dateFin},objectifSignature: {self.objectifSignature},titre: {self.titre}, cible: {self.cible}, IDmoderateur: {self.IDmoderateur}, dateCreated: {self.dateCreated}, is_deleted: {self.is_deleted},  >"

