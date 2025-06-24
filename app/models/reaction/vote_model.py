from app import db

from datetime import datetime


class Vote(db.Model):
    __tablename__ = 'votes'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB
    IDvote = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    types = db.Column(db.String(15), nullable=True)

    is_deleted = db.Column(db.Boolean, default=False)
    dateDeleted = db.Column(db.DateTime)

    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    signalementID = db.Column(db.Integer, db.ForeignKey('signalements.IDsignalement'), nullable=False)

    def __repr__(self):
        return f"<reaction signature => ID :{self.IDvote}, dateCreated:{self.dateCreated}, types:{self.types} >"

    