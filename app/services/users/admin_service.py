# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Admin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Service de Création
def create_admin(nom, adresse, password, role, username, image, telephone, prenom):
    hashed_password = generate_password_hash(password)
    new_admin = Admin(
        nom=nom, adresse=adresse, password=hashed_password, role=role,
        username=username, image=image, telephone=telephone,
        prenom=prenom,
        dateCreated=datetime.utcnow()
    )
    db.session.add(new_admin)
    db.session.commit()
    # Ajouter des claims personnalisés au token JWT
    # additional_claims = {
    #     'nom': new_admin.nom,
    #     'adresse': new_admin.adresse,
    #     'role': new_admin.role,
    #     'username': new_admin.username,
    #     'image': new_admin.image,
    #     'telephone': new_admin.telephone,
    #     'prenom': new_admin.prenom,
    #     'type_user': new_admin.type_user
    # }
    # access_token = create_access_token(identity=new_admin.IDuser, additional_claims=additional_claims)
    return new_admin

# Service de Lecture
def get_admin_by_id(admin_id):
    return Admin.query.get(admin_id)

def get_all_admins():
    return Admin.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_admin(admin_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, prenom=None):
    admin = Admin.query.get(admin_id)
    if not admin:
        return None

    if nom is not None:
        admin.nom = nom
    if adresse is not None:
        admin.adresse = adresse
    if password is not None:
        admin.password = generate_password_hash(password)
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
    admin = Admin.query.get(admin_id)
    if admin:
        admin.is_deleted = True
        admin.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_admin(username, password):
    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password, password):
        return admin
    return None
