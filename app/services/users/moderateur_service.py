# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Moderateur
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Service de Création
def create_moderateur(nom, adresse, password, role, username, image, telephone, prenom):
    hashed_password = generate_password_hash(password)
    new_moderateur = Moderateur(
        nom=nom, adresse=adresse, password=hashed_password, role=role,
        username=username, image=image, telephone=telephone,
        prenom=prenom,
        dateCreated=datetime.utcnow()
    )
    db.session.add(new_moderateur)
    db.session.commit()
    # Ajouter des claims personnalisés au token JWT
    # additional_claims = {
    #     'nom': new_moderateur.nom,
    #     'adresse': new_moderateur.adresse,
    #     'role': new_moderateur.role,
    #     'username': new_moderateur.username,
    #     'image': new_moderateur.image,
    #     'telephone': new_moderateur.telephone,
    #     'prenom': new_moderateur.prenom,
    #     'type_user': new_moderateur.type_user
    # }
    # access_token = create_access_token(identity=new_moderateur.IDuser, additional_claims=additional_claims)
    return new_moderateur

# Service de Lecture
def get_moderateur_by_id(moderateur_id):
    return Moderateur.query.get(moderateur_id)

def get_all_moderateurs():
    return Moderateur.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_moderateur(moderateur_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, prenom=None):
    moderateur = Moderateur.query.get(moderateur_id)
    if not moderateur:
        return None

    if nom is not None:
        moderateur.nom = nom
    if adresse is not None:
        moderateur.adresse = adresse
    if password is not None:
        moderateur.password = generate_password_hash(password)
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
    moderateur = Moderateur.query.get(moderateur_id)
    if moderateur:
        moderateur.is_deleted = True
        moderateur.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_moderateur(username, password):
    moderateur = Moderateur.query.filter_by(username=username).first()
    if moderateur and check_password_hash(moderateur.password, password):
        return moderateur
    return None
