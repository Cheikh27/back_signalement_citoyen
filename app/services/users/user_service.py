from app import db
from app.models import User, Admin, Authorite, Citoyen, Moderateur
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

# Initialiser Bcrypt
bcrypt = Bcrypt()

# Service de Création
def create_user(nom, adresse, password, role, username, image, telephone, user_type, **kwargs):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = None
    if user_type == 'admin':
        new_user = Admin(
            nom=nom, adresse=adresse, password=hashed_password, role=role,
            username=username, image=image, telephone=telephone,
            prenom=kwargs.get('prenom'),
            dateCreated=datetime.utcnow()
        )
    elif user_type == 'authorite':
        new_user = Authorite(
            nom=nom, adresse=adresse, password=hashed_password, role=role,
            username=username, image=image, telephone=telephone,
            typeAuthorite=kwargs.get('typeAuthorite'),
            description=kwargs.get('description'),
            dateCreated=datetime.utcnow()
        )
    elif user_type == 'citoyen':
        new_user = Citoyen(
            nom=nom, adresse=adresse, password=hashed_password, role=role,
            username=username, image=image, telephone=telephone,
            prenom=kwargs.get('prenom'),
            dateCreated=datetime.utcnow()
        )
    elif user_type == 'moderateur':
        new_user = Moderateur(
            nom=nom, adresse=adresse, password=hashed_password, role=role,
            username=username, image=image, telephone=telephone,
            prenom=kwargs.get('prenom'),
            dateCreated=datetime.utcnow()
        )
    if new_user:
        db.session.add(new_user)
        db.session.commit()
        # Ajouter des claims personnalisés au token JWT
        additional_claims = {
            'nom': new_user.nom,
            'adresse': new_user.adresse,
            'role': new_user.role,
            'username': new_user.username,
            'image': new_user.image,
            'telephone': new_user.telephone,
            'type_user': new_user.type_user
        }
        access_token = create_access_token(identity=new_user.IDuser, additional_claims=additional_claims)
        return new_user, access_token
    return None

# Service de Lecture
def get_user_by_id(user_id):
    return User.query.filter_by(IDuser=user_id, is_deleted=False).first()

def get_all_users():
    return User.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_user(user_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, **kwargs):
    user = User.query.filter_by(IDuser=user_id, is_deleted=False).first()
    if not user:
        return None

    if nom is not None:
        user.nom = nom
    if adresse is not None:
        user.adresse = adresse
    if password is not None:
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')
    if role is not None:
        user.role = role
    if username is not None:
        user.username = username
    if image is not None:
        user.image = image
    if telephone is not None:
        user.telephone = telephone

    if isinstance(user, Admin):
        if 'prenom' in kwargs:
            user.prenom = kwargs['prenom']
    elif isinstance(user, Authorite):
        if 'typeAuthorite' in kwargs:
            user.typeAuthorite = kwargs['typeAuthorite']
        if 'description' in kwargs:
            user.description = kwargs['description']
    elif isinstance(user, Citoyen):
        if 'prenom' in kwargs:
            user.prenom = kwargs['prenom']
    elif isinstance(user, Moderateur):
        if 'prenom' in kwargs:
            user.prenom = kwargs['prenom']

    db.session.commit()
    return user

# Service de Suppression Logique
def delete_user(user_id):
    user = User.query.filter_by(IDuser=user_id, is_deleted=False).first()
    if user:
        user.is_deleted = True
        user.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Service d'Authentification
def authenticate_user(username, password):
    user = User.query.filter_by(username=username, is_deleted=False).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return user
    return None
