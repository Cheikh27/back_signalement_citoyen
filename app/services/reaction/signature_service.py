# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Signature
from datetime import datetime

# Service de Création
def create_signature(citoyen_id, petition_id, nb_signature=1):
    nouvelle_signature = Signature(
        citoyenID=citoyen_id,
        petitionID=petition_id,
        nbSignature=nb_signature,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouvelle_signature)
    db.session.commit()
    return nouvelle_signature

# Service de Lecture
def get_signature_by_id(signature_id):
    return Signature.query.get(signature_id)

def get_all_signatures():
    return Signature.query.all()

def get_signatures_by_citoyen(citoyen_id):
    return Signature.query.filter_by(citoyenID=citoyen_id).all()

def get_signatures_by_petition(petition_id):
    return Signature.query.filter_by(petitionID=petition_id).all()

# Service de Mise à Jour
def update_signature(signature_id, nb_signature=None):
    signature = Signature.query.get(signature_id)
    if not signature:
        return None

    if nb_signature is not None:
        signature.nbSignature = nb_signature

    db.session.commit()
    return signature

# Service de Suppression
def delete_signature(signature_id):
    signature = Signature.query.get(signature_id)
    if signature:
        db.session.delete(signature)
        db.session.commit()
        return True
    return False
