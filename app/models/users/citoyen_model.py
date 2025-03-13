from .user_model import User
from app.models import db

class Citoyen(User):
    __tablename__ = 'citoyens'

    IDcitoyen = db.Column(db.Integer, db.ForeignKey('users.IDuser'), primary_key=True)
    prenom = db.Column(db.String(50), nullable=False)  # Augmenté à 50 pour plus de flexibilité

    # Relations
    votes = db.relationship('Vote', backref='citoyen', lazy=True)
    signalements = db.relationship('Signalement', backref='citoyen', lazy=True)
    petitions = db.relationship('Petition', backref='citoyen', lazy=True)
    signatures = db.relationship('Signature', backref='citoyen', lazy=True)
    appreciations = db.relationship('Appreciation', backref='citoyen', lazy=True)
    partages_signalements = db.relationship('PartagerSignalement', backref='citoyen', lazy=True)
    partages_petitions = db.relationship('PartagerPetition', backref='citoyen', lazy=True)
    partages_publications = db.relationship('PartagerPublication', backref='citoyen', lazy=True)
    commentaires_signalements = db.relationship('CommentaireSignalement', backref='citoyen', lazy=True)
    commentaires_petitions = db.relationship('CommentairePetition', backref='citoyen', lazy=True)
    commentaires_publications = db.relationship('CommentairePublication', backref='citoyen', lazy=True)
    appartenances = db.relationship('Appartenir', backref='citoyen', lazy=True)

    # Configuration du polymorphisme
    __mapper_args__ = {
        'polymorphic_identity': 'citoyen'  # Identifiant pour la classe Citoyen
    }

    def __repr__(self):
        return (f"<Citoyen IDcitoyen={self.IDcitoyen}, nom={self.nom}, prenom={self.prenom}, "
                f"adresse={self.adresse}, role={self.role}, username={self.username}, "
                f"telephone={self.telephone}, dateCreated={self.dateCreated}, "
                f"dateDeleted={self.dateDeleted}, is_deleted={self.is_deleted}, "
                f"type_user={self.type_user}>")
