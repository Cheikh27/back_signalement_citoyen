from .user_model import User
from app.models import db

class Moderateur(User):
    __tablename__ = 'moderateurs'

    IDmoderateur = db.Column(db.Integer, db.ForeignKey('users.IDuser'), primary_key=True)
    prenom = db.Column(db.String(50), nullable=False)  

    # Configuration du polymorphisme
    __mapper_args__ = {
        'polymorphic_identity': 'moderateur'  # Identifiant pour la classe Moderateur
    }

    def __repr__(self):
        return (f"<Moderateur IDmoderateur={self.IDmoderateur}, nom={self.nom}, prenom={self.prenom}, "
                f"adresse={self.adresse}, role={self.role}, username={self.username}, "
                f"telephone={self.telephone}, dateCreated={self.dateCreated}, "
                f"dateDeleted={self.dateDeleted}, is_deleted={self.is_deleted}, "
                f"type_user={self.type_user}>")
