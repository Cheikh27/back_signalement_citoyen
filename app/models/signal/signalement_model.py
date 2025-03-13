from app import db

from datetime import datetime


class Signalement(db.Model):
    __tablename__ = 'signalements'
    IDsignalement = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    elements = db.Column(db.String(255), nullable=False)

    statut = db.Column(db.String(20), nullable=False , default='en_cours')
    nbVotePositif = db.Column(db.Integer, nullable=True)
    nbVoteNegatif = db.Column(db.Integer , nullable=True)

    cible = db.Column(db.String(50), nullable=False)
    IDmoderateur = db.Column(db.Integer, nullable=True)

    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    dateDeleted = db.Column(db.DateTime, nullable=True)  # Date de suppression
    is_deleted = db.Column(db.Boolean, default=False) 

    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)

    Vote = db.relationship('Vote', backref='signalements', lazy=True)
    PartagerSignalement = db.relationship('PartagerSignalement', backref='signalements', lazy=True)
    CommentaireSignalement = db.relationship('CommentaireSignalement', backref='signalements', lazy=True)
    Publication = db.relationship('Publication', backref='signalements', lazy=True)

    def __repr__(self):
        return f"<signalement ID: {self.IDsignalement}, description: {self.description},statut: {self.statut},element: {self.element},nbVotePositif: {self.nbVotePositif},nbVoteNegatif: {self.nbVoteNegatif}, dateCreated: {self.dateCreated}, dateDeleted: {self.dateDeleted}, is_deleted: {self.is_deleted} , cible: {self.cible} ,, IDmoderateur: {self.IDmoderateur}  >"

