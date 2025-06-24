from app import db


from datetime import datetime


class Suivre(db.Model):
    __tablename__ = 'suivres'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # Définir explicitement InnoDB


    IDsuivre = db.Column(db.Integer, primary_key=True)

    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
    dateDeleted = db.Column(db.DateTime, nullable=True)  # Date de suppression
    is_deleted = db.Column(db.Boolean, default=False)

    suiveurID = db.Column(db.Integer, db.ForeignKey('users.IDuser'), nullable=False)
    suivisID = db.Column(db.Integer, db.ForeignKey('users.IDuser'), nullable=False)

    

    def __repr__(self):
        return f"<Suivre =>ID :{self.IDsuivre},  date_created:{self.dateCreated}, date_deleted:{self.dateDeleted}, is_deleted:{self.is_deleted} , suivreID:{self.suivreID}, suivisID:{self.suivisID}>"