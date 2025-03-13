# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db

from app.models import Appartenir
from datetime import datetime

# Service de Création
def create_appartenir(citoyen_id, groupe_id):
    nouvel_appartenir = Appartenir(
        citoyenID=citoyen_id,
        groupeID=groupe_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouvel_appartenir)
    db.session.commit()
    return nouvel_appartenir

# Service de Lecture
def get_appartenir_by_id(appartenir_id):
    return Appartenir.query.get(appartenir_id)

def get_all_appartenirs():
    return Appartenir.query.all()

def get_appartenirs_by_citoyen(citoyen_id):
    return Appartenir.query.filter_by(citoyenID=citoyen_id).all()

def get_appartenirs_by_groupe(groupe_id):
    return Appartenir.query.filter_by(groupeID=groupe_id).all()

# Service de Mise à Jour
def update_appartenir(appartenir_id, citoyen_id=None, groupe_id=None):
    appartenir = Appartenir.query.get(appartenir_id)
    if not appartenir:
        return None

    if citoyen_id is not None:
        appartenir.citoyenID = citoyen_id
    if groupe_id is not None:
        appartenir.groupeID = groupe_id

    db.session.commit()
    return appartenir

# Service de Suppression
def delete_appartenir(appartenir_id):
    appartenir = Appartenir.query.get(appartenir_id)
    if appartenir:
        db.session.delete(appartenir)
        db.session.commit()
        return True
    return False
