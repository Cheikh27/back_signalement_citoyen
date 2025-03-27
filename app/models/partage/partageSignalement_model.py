from datetime import datetime
from app import db



class PartagerSignalement(db.Model):
    __tablename__ = 'partagerSignalements'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB
    IDpartager = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    nbPartage = db.Column(db.Integer , nullable=True)

    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    SignalementID = db.Column(db.Integer, db.ForeignKey('signalements.IDsignalement'), nullable=False)

    def __repr__(self):
        return f"<partage signalement => ID :{self.IDpartager}, dateCreated:{self.dateCreated}, nbPartage:{self.nbPartage}>"

