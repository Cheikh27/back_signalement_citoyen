
from app import db
from app.models import Admin, User
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

from flask_caching import logger # type: ignore

# Initialiser Bcrypt
bcrypt = Bcrypt()

# Service de Création
def create_admin(nom, adresse, password, role, username, image, telephone, prenom):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_admin = Admin(
        nom=nom, adresse=adresse, password=hashed_password, role=role,
        username=username, image=image, telephone=telephone,
        prenom=prenom,
        dateCreated=datetime.utcnow()
    )
    db.session.add(new_admin)
    db.session.commit()
    return new_admin

# Service de Lecture
def get_admin_by_id(admin_id):
    return Admin.query.filter_by(IDadmin=admin_id, is_deleted=False).first()

def get_all_admins():
    return Admin.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_admin(admin_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, prenom=None):
    admin = Admin.query.filter_by(IDadmin=admin_id, is_deleted=False).first()
    if not admin:
        return None

    if nom is not None:
        admin.nom = nom
    if adresse is not None:
        admin.adresse = adresse
    if password is not None:
        admin.password = bcrypt.generate_password_hash(password).decode('utf-8')
    if role is not None:
        admin.role = role
    if username is not None:
        admin.username = username
    if image is not None:
        admin.image = image
    if telephone is not None:
        admin.telephone = telephone
    if prenom is not None:
        admin.prenom = prenom

    db.session.commit()
    return admin

# Service de Suppression Logique
def delete_admin(admin_id):
    admin = Admin.query.filter_by(IDadmin=admin_id, is_deleted=False).first()
    if admin:
        admin.is_deleted = True
        admin.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_admin(username, password):
    admin = Admin.query.filter_by(username=username, is_deleted=False).first()
    if admin and bcrypt.check_password_hash(admin.password, password):
        return admin
    return None
