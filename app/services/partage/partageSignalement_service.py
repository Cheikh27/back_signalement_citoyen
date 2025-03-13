# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import PartagerSignalement
from datetime import datetime

# Service de Création
def create_partager_signalement(citoyen_id, signalement_id, nb_partage=0):
    nouveau_partage = PartagerSignalement(
        citoyenID=citoyen_id,
        SignalementID=signalement_id,
        nbPartage=nb_partage,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_partage)
    db.session.commit()
    return nouveau_partage

# Service de Lecture
def get_partager_signalement_by_id(partager_id):
    return PartagerSignalement.query.get(partager_id)

def get_all_partager_signalements():
    return PartagerSignalement.query.all()

def get_partager_signalements_by_citoyen(citoyen_id):
    return PartagerSignalement.query.filter_by(citoyenID=citoyen_id).all()

def get_partager_signalements_by_signalement(signalement_id):
    return PartagerSignalement.query.filter_by(SignalementID=signalement_id).all()

# Service de Mise à Jour
def update_partager_signalement(partager_id, nb_partage=None):
    partager = PartagerSignalement.query.get(partager_id)
    if not partager:
        return None

    if nb_partage is not None:
        partager.nbPartage = nb_partage

    db.session.commit()
    return partager

# Service de Suppression
def delete_partager_signalement(partager_id):
    partager = PartagerSignalement.query.get(partager_id)
    if partager:
        db.session.delete(partager)
        db.session.commit()
        return True
    return False
