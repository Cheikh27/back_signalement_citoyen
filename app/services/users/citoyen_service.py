# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Citoyen
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Service de Création
def create_citoyen(nom, adresse, password, role, username, image, telephone, prenom):
    hashed_password = generate_password_hash(password)
    new_citoyen = Citoyen(
        nom=nom, adresse=adresse, password=hashed_password, role=role,
        username=username, image=image, telephone=telephone,
        prenom=prenom,
        dateCreated=datetime.utcnow()
    )
    db.session.add(new_citoyen)
    db.session.commit()
    # Ajouter des claims personnalisés au token JWT
    # additional_claims = {
    #     'nom': new_citoyen.nom,
    #     'adresse': new_citoyen.adresse,
    #     'role': new_citoyen.role,
    #     'username': new_citoyen.username,
    #     'image': new_citoyen.image,
    #     'telephone': new_citoyen.telephone,
    #     'prenom': new_citoyen.prenom,
    #     'type_user': new_citoyen.type_user
    # }
    # access_token = create_access_token(identity=new_citoyen.IDuser, additional_claims=additional_claims)
    return new_citoyen

# Service de Lecture
def get_citoyen_by_id(citoyen_id):
    return Citoyen.query.get(citoyen_id)

def get_all_citoyens():
    return Citoyen.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_citoyen(citoyen_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, prenom=None):
    citoyen = Citoyen.query.get(citoyen_id)
    if not citoyen:
        return None

    if nom is not None:
        citoyen.nom = nom
    if adresse is not None:
        citoyen.adresse = adresse
    if password is not None:
        citoyen.password = generate_password_hash(password)
    if role is not None:
        citoyen.role = role
    if username is not None:
        citoyen.username = username
    if image is not None:
        citoyen.image = image
    if telephone is not None:
        citoyen.telephone = telephone
    if prenom is not None:
        citoyen.prenom = prenom

    db.session.commit()
    return citoyen

# Service de Suppression Logique
def delete_citoyen(citoyen_id):
    citoyen = Citoyen.query.get(citoyen_id)
    if citoyen:
        citoyen.is_deleted = True
        citoyen.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_citoyen(username, password):
    citoyen = Citoyen.query.filter_by(username=username).first()
    if citoyen and check_password_hash(citoyen.password, password):
        return citoyen
    return None
