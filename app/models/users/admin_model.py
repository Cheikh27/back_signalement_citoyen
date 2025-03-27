from .user_model import User
from app.models import db

class Admin(User):
    __tablename__ = 'admins'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB

    IDadmin = db.Column(db.Integer, db.ForeignKey('users.IDuser'), primary_key=True)
    prenom = db.Column(db.String(50), nullable=False)  # Augmenté à 50 pour plus de flexibilité
    # matricule = db.Column(db.String(20), unique=True, nullable=False)  # Décommenter si nécessaire

    # Configuration du polymorphisme
    __mapper_args__ = {
        'polymorphic_identity': 'admin'  # Identifiant pour la classe Admin
    }

    def __repr__(self):
        return (f"<Admin IDadmin={self.IDadmin}, nom={self.nom}, prenom={self.prenom}, "
                f"adresse={self.adresse}, role={self.role}, username={self.username}, "
                f"telephone={self.telephone}, dateCreated={self.dateCreated}, "
                f"dateDeleted={self.dateDeleted}, is_deleted={self.is_deleted}, "
                f"type_user={self.type_user}>")
