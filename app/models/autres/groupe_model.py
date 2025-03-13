from app import db


from datetime import datetime


class Groupe(db.Model):
    __tablename__ = 'groupes'

    IDgroupe = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)  
    description = db.Column(db.Text, nullable=False)  
    image = db.Column(db.String(255), nullable=True)  
    admin = db.Column(db.Integer, nullable=False)  
    

    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    dateDeleted = db.Column(db.DateTime, nullable=True)  # Date de suppression
    is_deleted = db.Column(db.Boolean, default=False)

    # Relations
    appartenances = db.relationship('Appartenir', backref='groupe', lazy=True)
    # signalements = db.relationship('Signalement', backref='groupe', lazy=True)
    # petitions = db.relationship('Petition', backref='groupe', lazy=True)

    def __repr__(self):
        return f"<Groupe =>ID :{self.IDgroupe}, NOM :{self.nom}, description : {self.description}, image:{self.image}, admin:{self.admin}, date_created:{self.dateCreated}, date_deleted:{self.dateDeleted}, is_deleted:{self.is_deleted}>"