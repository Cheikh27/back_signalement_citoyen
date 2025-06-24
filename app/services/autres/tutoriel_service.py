# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db

from app.models import Tutoriel
from datetime import datetime

# Service de Création
def create_tutoriel(citoyen_id, groupe_id):
    nouvel_tutoriel = Tutoriel(
        citoyenID=citoyen_id,
        #suivis=suivis, # type: ignore
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouvel_tutoriel)
    db.session.commit()
    return nouvel_tutoriel

# Service de Lecture
def get_tutoriel_by_id(tutoriel_id):
    return Tutoriel.query.get(tutoriel_id)

def get_all_tutoriels():
    return Tutoriel.query.all()

def get_tutoriels_by_citoyen(citoyen_id):
    return Tutoriel.query.filter_by(citoyenID=citoyen_id).all()

# def get_tutoriels_by_groupe(groupe_id):
#     return Tutoriel.query.filter_by(groupeID=groupe_id).all()

# Service de Mise à Jour
def update_tutoriel(tutoriel_id, citoyen_id=None, suivis=None):
    tutoriel = Tutoriel.query.get(tutoriel_id)
    if not tutoriel:
        return None

    if citoyen_id is not None:
        tutoriel.citoyenID = citoyen_id
    if suivis is not None:
        tutoriel.suivis = suivis

    db.session.commit()
    return tutoriel

# Service de Suppression
def delete_tutoriel(tutoriel_id):
    tutoriel = Tutoriel.query.get(tutoriel_id)
    if tutoriel:
        db.session.delete(tutoriel)
        db.session.commit()
        return True
    return False
