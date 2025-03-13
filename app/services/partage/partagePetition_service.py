# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import PartagerPetition
from datetime import datetime

# Service de Création
def create_partager_petition(citoyen_id, petition_id, nb_partage=0):
    nouveau_partage = PartagerPetition(
        citoyenID=citoyen_id,
        petitionID=petition_id,
        nbPartage=nb_partage,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_partage)
    db.session.commit()
    return nouveau_partage

# Service de Lecture
def get_partager_petition_by_id(partager_id):
    return PartagerPetition.query.get(partager_id)

def get_all_partager_petitions():
    return PartagerPetition.query.all()

def get_partager_petitions_by_citoyen(citoyen_id):
    return PartagerPetition.query.filter_by(citoyenID=citoyen_id).all()

def get_partager_petitions_by_petition(petition_id):
    return PartagerPetition.query.filter_by(petitionID=petition_id).all()

# Service de Mise à Jour
def update_partager_petition(partager_id, nb_partage=None):
    partager = PartagerPetition.query.get(partager_id)
    if not partager:
        return None

    if nb_partage is not None:
        partager.nbPartage = nb_partage

    db.session.commit()
    return partager

# Service de Suppression
def delete_partager_petition(partager_id):
    partager = PartagerPetition.query.get(partager_id)
    if partager:
        db.session.delete(partager)
        db.session.commit()
        return True
    return False
