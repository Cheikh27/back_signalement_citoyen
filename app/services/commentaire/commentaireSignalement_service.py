# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import CommentaireSignalement
from datetime import datetime

# Service de Création
def create_commentaire_signalement(description, citoyen_id, signalement_id):
    nouveau_commentaire = CommentaireSignalement(
        description=description,
        citoyenID=citoyen_id,
        signalementID=signalement_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_commentaire)
    db.session.commit()
    return nouveau_commentaire

# Service de Lecture
def get_commentaire_signalement_by_id(commentaire_id):
    return CommentaireSignalement.query.get(commentaire_id)

def get_all_commentaires_signalement():
    return CommentaireSignalement.query.filter_by(is_deleted=False).all()

def get_commentaires_signalement_by_citoyen(citoyen_id):
    return CommentaireSignalement.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def get_commentaires_signalement_by_signalement(signalement_id):
    return CommentaireSignalement.query.filter_by(signalementID=signalement_id, is_deleted=False).all()

# Service de Mise à Jour
def update_commentaire_signalement(commentaire_id, description=None):
    commentaire = CommentaireSignalement.query.get(commentaire_id)
    if not commentaire:
        return None

    if description is not None:
        commentaire.description = description

    db.session.commit()
    return commentaire

# Service de Suppression Logique
def delete_commentaire_signalement(commentaire_id):
    commentaire = CommentaireSignalement.query.get(commentaire_id)
    if commentaire:
        commentaire.is_deleted = True
        commentaire.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False
