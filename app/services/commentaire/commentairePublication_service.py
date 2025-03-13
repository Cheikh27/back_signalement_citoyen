# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import CommentairePublication
from datetime import datetime

# Service de Création
def create_commentaire_publication(description, citoyen_id, publication_id):
    nouveau_commentaire = CommentairePublication(
        description=description,
        citoyenID=citoyen_id,
        publicationID=publication_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_commentaire)
    db.session.commit()
    return nouveau_commentaire

# Service de Lecture
def get_commentaire_publication_by_id(commentaire_id):
    return CommentairePublication.query.get(commentaire_id)

def get_all_commentaires_publication():
    return CommentairePublication.query.filter_by(is_deleted=False).all()

def get_commentaires_publication_by_citoyen(citoyen_id):
    return CommentairePublication.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def get_commentaires_publication_by_publication(publication_id):
    return CommentairePublication.query.filter_by(publicationID=publication_id, is_deleted=False).all()

# Service de Mise à Jour
def update_commentaire_publication(commentaire_id, description=None):
    commentaire = CommentairePublication.query.get(commentaire_id)
    if not commentaire:
        return None

    if description is not None:
        commentaire.description = description

    db.session.commit()
    return commentaire

# Service de Suppression Logique
def delete_commentaire_publication(commentaire_id):
    commentaire = CommentairePublication.query.get(commentaire_id)
    if commentaire:
        commentaire.is_deleted = True
        commentaire.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False
