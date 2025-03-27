from app import db
from app.models import Moderateur
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

# Initialiser Bcrypt
bcrypt = Bcrypt()

# Service de Création
def create_moderateur(nom, adresse, password, role, username, image, telephone, prenom):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_moderateur = Moderateur(
        nom=nom, adresse=adresse, password=hashed_password, role=role,
        username=username, image=image, telephone=telephone,
        prenom=prenom,
        dateCreated=datetime.utcnow()
    )
    db.session.add(new_moderateur)
    db.session.commit()
    return new_moderateur

# Service de Lecture
def get_moderateur_by_id(moderateur_id):
    return Moderateur.query.filter_by(IDmoderateur=moderateur_id, is_deleted=False).first()

def get_all_moderateurs():
    return Moderateur.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_moderateur(moderateur_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, prenom=None):
    moderateur = Moderateur.query.filter_by(IDmoderateur=moderateur_id, is_deleted=False).first()
    if not moderateur:
        return None

    if nom is not None:
        moderateur.nom = nom
    if adresse is not None:
        moderateur.adresse = adresse
    if password is not None:
        moderateur.password = bcrypt.generate_password_hash(password).decode('utf-8')
    if role is not None:
        moderateur.role = role
    if username is not None:
        moderateur.username = username
    if image is not None:
        moderateur.image = image
    if telephone is not None:
        moderateur.telephone = telephone
    if prenom is not None:
        moderateur.prenom = prenom

    db.session.commit()
    return moderateur

# Service de Suppression Logique
def delete_moderateur(moderateur_id):
    moderateur = Moderateur.query.filter_by(IDmoderateur=moderateur_id, is_deleted=False).first()
    if moderateur:
        moderateur.is_deleted = True
        moderateur.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_moderateur(username, password):
    moderateur = Moderateur.query.filter_by(username=username, is_deleted=False).first()
    if moderateur and bcrypt.check_password_hash(moderateur.password, password):
        return moderateur
    return None
