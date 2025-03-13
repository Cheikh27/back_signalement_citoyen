# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Publication
from datetime import datetime

# Service de Création
def create_publication(titre, description, element, nb_aime_positif, nb_aime_negatif, autorite_id, signalement_id,IDmoderateur):
    nouvelle_publication = Publication(
        titre=titre,
        description=description,
        element=element,
        nbAimePositif=nb_aime_positif,
        nbAimeNegatif=nb_aime_negatif,
        autoriteID=autorite_id,
        signalementID=signalement_id,
        dateCreated=datetime.utcnow(),
        IDmoderateur=IDmoderateur
    )
    db.session.add(nouvelle_publication)
    db.session.commit()
    return nouvelle_publication

# Service de Lecture
def get_publication_by_id(publication_id):
    return Publication.query.get(publication_id)

def get_all_publications():
    return Publication.query.filter_by(is_deleted=False).all()

def get_publications_by_autorite(autorite_id):
    return Publication.query.filter_by(autoriteID=autorite_id, is_deleted=False).all()

def get_publications_by_signalement(signalement_id):
    return Publication.query.filter_by(signalementID=signalement_id, is_deleted=False).all()

# Service de Mise à Jour
def update_publication(publication_id, titre=None, description=None, element=None, nb_aime_positif=None, nb_aime_negatif=None):
    publication = Publication.query.get(publication_id)
    if not publication:
        return None

    if titre is not None:
        publication.titre = titre
    if description is not None:
        publication.description = description
    if element is not None:
        publication.element = element
    if nb_aime_positif is not None:
        publication.nbAimePositif = nb_aime_positif
    if nb_aime_negatif is not None:
        publication.nbAimeNegatif = nb_aime_negatif

    db.session.commit()
    return publication

# Service de Suppression Logique
def delete_publication(publication_id):
    publication = Publication.query.get(publication_id)
    if publication:
        publication.is_deleted = True
        publication.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False
