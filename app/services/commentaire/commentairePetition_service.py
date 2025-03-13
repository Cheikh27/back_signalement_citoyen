# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import CommentairePetition
from datetime import datetime

# Service de Création
def create_commentaire(description, citoyen_id, petition_id):
    nouveau_commentaire = CommentairePetition(
        description=description,
        citoyenID=citoyen_id,
        petitionID=petition_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_commentaire)
    db.session.commit()
    return nouveau_commentaire

# Service de Lecture
def get_commentaire_by_id(commentaire_id):
    return CommentairePetition.query.get(commentaire_id)

def get_all_commentaires():
    return CommentairePetition.query.filter_by(is_deleted=False).all()

def get_commentaires_by_citoyen(citoyen_id):
    return CommentairePetition.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def get_commentaires_by_petition(petition_id):
    return CommentairePetition.query.filter_by(petitionID=petition_id, is_deleted=False).all()

# Service de Mise à Jour
def update_commentaire(commentaire_id, description=None):
    commentaire = CommentairePetition.query.get(commentaire_id)
    if not commentaire:
        return None

    if description is not None:
        commentaire.description = description

    db.session.commit()
    return commentaire

# Service de Suppression Logique
def delete_commentaire(commentaire_id):
    commentaire = CommentairePetition.query.get(commentaire_id)
    if commentaire:
        commentaire.is_deleted = True
        commentaire.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False
