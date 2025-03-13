# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Authorite
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Service de Création
def create_authorite(nom, adresse, password, role, username, image, telephone, typeAuthorite, description):
    hashed_password = generate_password_hash(password)
    new_authorite = Authorite(
        nom=nom, adresse=adresse, password=hashed_password, role=role,
        username=username, image=image, telephone=telephone,
        typeAuthorite=typeAuthorite,
        description=description,
        dateCreated=datetime.utcnow()
    )
    db.session.add(new_authorite)
    db.session.commit()
    
    return new_authorite

# Service de Lecture
def get_authorite_by_id(authorite_id):
    return Authorite.query.get(authorite_id)

def get_all_authorites():
    return Authorite.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_authorite(authorite_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, typeAuthorite=None, description=None):
    authorite = Authorite.query.get(authorite_id)
    if not authorite:
        return None

    if nom is not None:
        authorite.nom = nom
    if adresse is not None:
        authorite.adresse = adresse
    if password is not None:
        authorite.password = generate_password_hash(password)
    if role is not None:
        authorite.role = role
    if username is not None:
        authorite.username = username
    if image is not None:
        authorite.image = image
    if telephone is not None:
        authorite.telephone = telephone
    if typeAuthorite is not None:
        authorite.typeAuthorite = typeAuthorite
    if description is not None:
        authorite.description = description

    db.session.commit()
    return authorite

# Service de Suppression Logique
def delete_authorite(authorite_id):
    authorite = Authorite.query.get(authorite_id)
    if authorite:
        authorite.is_deleted = True
        authorite.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_authorite(username, password):
    authorite = Authorite.query.filter_by(username=username).first()
    if authorite and check_password_hash(authorite.password, password):
        return authorite
    return None
