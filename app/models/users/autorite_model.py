from enum import Enum
from app.models import db
from .user_model import User

class TypeAuthorite(Enum):
    PREFET = 'prefet'
    MAIRE = 'maire'
    ETAT = 'etat'

class Authorite(User):
    __tablename__ = 'authorites'

    IDauthorite = db.Column(db.Integer, db.ForeignKey('users.IDuser'), primary_key=True)
    typeAuthorite = db.Column(db.Enum(TypeAuthorite), nullable=False)
    description = db.Column(db.Text, nullable=False)

    publications = db.relationship('Publication', backref='authorite', lazy=True)
    # commentaires = db.relationship('CommentairePublication', backref='authorite', lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': 'authorite'
    }

    def __repr__(self):
        return (f"<Authorite IDauthorite={self.IDauthorite}, nom={self.nom}, "
                f"typeAuthorite={self.typeAuthorite}, description={self.description}, "
                f"adresse={self.adresse}, role={self.role}, username={self.username}, "
                f"telephone={self.telephone}, dateCreated={self.dateCreated}, "
                f"dateDeleted={self.dateDeleted}, is_deleted={self.is_deleted}, "
                f"type_user={self.type_user}>")

    