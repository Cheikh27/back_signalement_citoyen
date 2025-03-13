# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Appreciation
from datetime import datetime

# Service de Création
def create_appreciation(citoyen_id, publication_id):
    nouvelle_appreciation = Appreciation(
        citoyenID=citoyen_id,
        PublicationID=publication_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouvelle_appreciation)
    db.session.commit()
    return nouvelle_appreciation

# Service de Lecture
def get_appreciation_by_id(appreciation_id):
    return Appreciation.query.get(appreciation_id)

def get_all_appreciations():
    return Appreciation.query.all()

def get_appreciations_by_citoyen(citoyen_id):
    return Appreciation.query.filter_by(citoyenID=citoyen_id).all()

def get_appreciations_by_publication(publication_id):
    return Appreciation.query.filter_by(PublicationID=publication_id).all()

# Service de Suppression
def delete_appreciation(appreciation_id):
    appreciation = Appreciation.query.get(appreciation_id)
    if appreciation:
        db.session.delete(appreciation)
        db.session.commit()
        return True
    return False
