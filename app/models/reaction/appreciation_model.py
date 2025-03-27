from datetime import datetime
from app import db



class Appreciation(db.Model):
    __tablename__ = 'appreciations'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB
    IDappreciation = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création


    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    PublicationID = db.Column(db.Integer, db.ForeignKey('publications.IDpublication'), nullable=False)

    def __repr__(self):
        return f"<reaction appreciation => ID :{self.IDappreciation}, dateCreated:{self.dateCreated} >"

