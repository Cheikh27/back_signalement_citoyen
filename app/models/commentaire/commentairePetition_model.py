from datetime import datetime
from app import db


class CommentairePetition(db.Model):
    __tablename__ = 'commentairePetitions'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB
    IDcommentaire = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)


    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    dateDeleted = db.Column(db.DateTime, nullable=True)  # Date de suppression
    is_deleted = db.Column(db.Boolean, default=False)
    # Clé étrangère vers Citoyen
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)
    petitionID = db.Column(db.Integer, db.ForeignKey('petitions.IDpetition'), nullable=False)

    def __repr__(self):
        return f"<Groupe => ID :{self.IDcommentaire}, description : {self.description}, dateCreated:{self.dateCreated}, dateDeleted:{self.dateDeleted}, is_deleted:{self.is_deleted}  >"
