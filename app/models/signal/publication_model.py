from app.models import db
from datetime import datetime
import zlib

class Publication(db.Model):
    __tablename__ = 'publications'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB

    IDpublication = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    _element = db.Column('element', db.LargeBinary, nullable=False)  # Utiliser LargeBinary pour stocker les données compressées
    nbAimePositif = db.Column(db.Integer, nullable=True)
    nbAimeNegatif = db.Column(db.Integer, nullable=True)

    dateDeleted = db.Column(db.DateTime, nullable=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    IDmoderateur = db.Column(db.Integer, nullable=True)

    # Clé étrangère vers Authorite
    autoriteID = db.Column(db.Integer, db.ForeignKey('authorites.IDauthorite'), nullable=False)
    signalementID = db.Column(db.Integer, db.ForeignKey('signalements.IDsignalement'), nullable=False)

    Appreciation = db.relationship('Appreciation', backref='publications', lazy=True)
    PartagerPublication = db.relationship('PartagerPublication', backref='publications', lazy=True)
    CommentairePublication = db.relationship('CommentairePublication', backref='publications', lazy=True)



    def __repr__(self):
        return (f"<Publication ID: {self.IDpublication}, description: {self.description}, "
                f"titre: {self.titre}, element: {self.element}, nbAimePositif: {self.nbAimePositif}, "
                f"nbAimeNegatif: {self.nbAimeNegatif}, dateCreated: {self.dateCreated}, "
                f"dateDeleted: {self.dateDeleted}, is_deleted: {self.is_deleted}>")
