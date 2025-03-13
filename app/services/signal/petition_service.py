# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Petition
from datetime import datetime

# Service de Création
def create_petition(description, nb_signature, nb_partage, date_fin, objectif_signature, titre, cible, id_moderateur, citoyen_id):
    nouvelle_petition = Petition(
        description=description,
        nbSignature=nb_signature,
        nbPartage=nb_partage,
        dateFin=date_fin,
        objectifSignature=objectif_signature,
        titre=titre,
        cible=cible,
        IDmoderateur=id_moderateur,
        citoyenID=citoyen_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouvelle_petition)
    db.session.commit()
    return nouvelle_petition

# Service de Lecture
def get_petition_by_id(petition_id):
    return Petition.query.get(petition_id)

def get_all_petitions():
    return Petition.query.filter_by(is_deleted=False).all()

def get_petitions_by_citoyen(citoyen_id):
    return Petition.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

# Service de Mise à Jour
def update_petition(petition_id, description=None, nb_signature=None, nb_partage=None, date_fin=None, objectif_signature=None, titre=None, cible=None, id_moderateur=None):
    petition = Petition.query.get(petition_id)
    if not petition:
        return None

    if description is not None:
        petition.description = description
    if nb_signature is not None:
        petition.nbSignature = nb_signature
    if nb_partage is not None:
        petition.nbPartage = nb_partage
    if date_fin is not None:
        petition.dateFin = date_fin
    if objectif_signature is not None:
        petition.objectifSignature = objectif_signature
    if titre is not None:
        petition.titre = titre
    if cible is not None:
        petition.cible = cible
    if id_moderateur is not None:
        petition.IDmoderateur = id_moderateur

    db.session.commit()
    return petition

# Service de Suppression Logique
def delete_petition(petition_id):
    petition = Petition.query.get(petition_id)
    if petition:
        petition.is_deleted = True
        db.session.commit()
        return True
    return False
