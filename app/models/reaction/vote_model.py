from app import db

from datetime import datetime


class Vote(db.Model):
    __tablename__ = 'votes'
    IDvote = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    
    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    signalementID = db.Column(db.Integer, db.ForeignKey('signalements.IDsignalement'), nullable=False)

    def __repr__(self):
        return f"<reaction signature => ID :{self.IDvote}, dateCreated:{self.dateCreated}>"

