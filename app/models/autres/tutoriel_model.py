from datetime import datetime

from app import db


class Tutoriel(db.Model):
    __tablename__ = 'tutoriels'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB

    IDtutoriel = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    suivis = db.Column(db.Boolean, default=False)


    # Clé étrangère vers Citoyen et Groupe
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)

    # Relation avec Citoyen (une Publication appartient à un Citoyen)
    # La relation 'citoyen' est définie dans le modèle Citoyen via backref

    def __repr__(self):
        return f"<Tutoriel : {self.IDtutoriel,self.suivis,self.dateCreated}>"