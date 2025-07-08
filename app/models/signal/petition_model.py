import json
from app import db
from datetime import datetime

class Petition(db.Model):
    __tablename__ = 'petitions'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    IDpetition = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    nbSignature = db.Column(db.Integer, nullable=True)
    nbPartage = db.Column(db.Integer, nullable=True)
    nbCommentaire = db.Column(db.Integer, nullable=True)

    dateFin = db.Column(db.DateTime, nullable=True)
    statut = db.Column(db.String(20), nullable=False, default='en_attente')  # ← MODIFICATION: default='en_attente | rejeter | valider ==> en_cours | terminer'

    anonymat = db.Column(db.Boolean, default=False)
    elements = db.Column(db.Text, nullable=True)

    objectifSignature = db.Column(db.Integer, nullable=True)
    titre = db.Column(db.String(100), nullable=False)
    cible = db.Column(db.String(15), nullable=True)  


    IDmoderateur = db.Column(db.Integer, nullable=True)

    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    destinataire = db.Column(db.String(100), nullable=False)
    republierPar = db.Column(db.Integer, nullable=True)

    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)

    Signature = db.relationship('Signature', backref='petitions', lazy=True)
    PartagerPetition = db.relationship('PartagerPetition', backref='petitions', lazy=True)
    CommentairePetition = db.relationship('CommentairePetition', backref='petitions', lazy=True)

    def __repr__(self):
        return f"<Petition ID: {self.IDpetition}, description: {self.description}, nbPartage: {self.nbPartage}, dateFin: {self.dateFin}, objectifSignature: {self.objectifSignature}, titre: {self.titre}, IDmoderateur: {self.IDmoderateur}, dateCreated: {self.dateCreated}, is_deleted: {self.is_deleted}>"
    def set_elements(self, media_list):
        """Enregistre la liste des médias (métadonnées uniquement) en JSON"""
        self.elements = json.dumps(media_list)

    def get_elements(self):
        """Récupère la liste des médias depuis le JSON"""
        return json.loads(self.elements or "[]")
