from app.models import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB

    IDuser = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    adresse = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    image = db.Column(db.String(255), nullable=True)
    telephone = db.Column(db.String(20), nullable=False, unique=True)

    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)
    dateDeleted = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)

    type_user = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_on': type_user,
        'polymorphic_identity': 'user'
    }

    def __repr__(self):
        return (f"<User IDuser={self.IDuser}, nom={self.nom}, adresse={self.adresse}, "
                f"role={self.role}, username={self.username}, telephone={self.telephone}, "
                f"dateCreated={self.dateCreated}, dateDeleted={self.dateDeleted}, "
                f"is_deleted={self.is_deleted}, type_user={self.type_user}>")
