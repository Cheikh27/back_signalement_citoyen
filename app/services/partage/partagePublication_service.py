# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import PartagerPublication
from datetime import datetime

# Service de Création
def create_partager_publication(citoyen_id, publication_id, nb_partage=0):
    nouveau_partage = PartagerPublication(
        citoyenID=citoyen_id,
        publicationID=publication_id,
        nbPartage=nb_partage,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_partage)
    db.session.commit()
    return nouveau_partage

# Service de Lecture
def get_partager_publication_by_id(partager_id):
    return PartagerPublication.query.get(partager_id)

def get_all_partager_publications():
    return PartagerPublication.query.all()

def get_partager_publications_by_citoyen(citoyen_id):
    return PartagerPublication.query.filter_by(citoyenID=citoyen_id).all()

def get_partager_publications_by_publication(publication_id):
    return PartagerPublication.query.filter_by(publicationID=publication_id).all()

# Service de Mise à Jour
def update_partager_publication(partager_id, nb_partage=None):
    partager = PartagerPublication.query.get(partager_id)
    if not partager:
        return None

    if nb_partage is not None:
        partager.nbPartage = nb_partage

    db.session.commit()
    return partager

# Service de Suppression
def delete_partager_publication(partager_id):
    partager = PartagerPublication.query.get(partager_id)
    if partager:
        db.session.delete(partager)
        db.session.commit()
        return True
    return False
