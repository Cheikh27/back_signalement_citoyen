from datetime import datetime
from app import db


class PartagerPublication(db.Model):
    __tablename__ = 'partagerPublications'
    IDpartager = db.Column(db.Integer, primary_key=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    nbPartage = db.Column(db.Integer , nullable=True)

    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    publicationID = db.Column(db.Integer, db.ForeignKey('publications.IDpublication'), nullable=False)

    def __repr__(self):
        return f"<partage petition => ID :{self.IDpartager}, dateCreated:{self.dateCreated}, nbPartage:{self.nbPartage}  >"

