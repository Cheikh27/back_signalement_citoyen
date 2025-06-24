# app/services/users/citoyen_service.py - VERSION CORRIGÉE
from app import db
from app.models import Citoyen
from datetime import datetime
from flask_bcrypt import Bcrypt
# ✅ CORRECTIF: Import explicite pour éviter les conflits
from flask_jwt_extended import create_access_token as jwt_create_access_token

# Initialiser Bcrypt
bcrypt = Bcrypt()

# Service de Création
def create_citoyen(nom, adresse, password, role, username, image, telephone, prenom):
    """Crée un nouveau citoyen avec validation."""
    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_citoyen = Citoyen(
            nom=nom, 
            adresse=adresse, 
            password=hashed_password, 
            role=role,
            username=username, 
            image=image, 
            telephone=telephone,
            prenom=prenom,
            dateCreated=datetime.utcnow(),
            type_user='citoyen'
        )
        db.session.add(new_citoyen)
        db.session.commit()
        return new_citoyen
    except Exception as e:
        db.session.rollback()
        print(f"Erreur création citoyen: {e}")
        return None

# Service de Lecture
def get_citoyen_by_id(citoyen_id):
    """Récupère un citoyen par son ID."""
    return Citoyen.query.filter_by(IDuser=citoyen_id, is_deleted=False).first()

def get_all_citoyens():
    """Récupère tous les citoyens actifs."""
    return Citoyen.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour par ID
def update_citoyen(citoyen_id, nom=None, adresse=None, password=None, role=None, username=None, image=None, telephone=None, prenom=None):
    """Met à jour un citoyen par son ID."""
    try:
        citoyen = Citoyen.query.filter_by(IDuser=citoyen_id, is_deleted=False).first()
        if not citoyen:
            return None

        if nom is not None:
            citoyen.nom = nom
        if adresse is not None:
            citoyen.adresse = adresse
        if password is not None:
            citoyen.password = bcrypt.generate_password_hash(password).decode('utf-8')
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
    except Exception as e:
        db.session.rollback()
        print(f"Erreur mise à jour citoyen: {e}")
        return None


# Service de Mise à Jour par téléphone
def update_citoyen_by_telephone(telephone, nom=None, adresse=None, password=None, role=None, username=None, image=None, prenom=None):
    """Met à jour un citoyen par son téléphone."""
    try:
        citoyen = Citoyen.query.filter_by(telephone=telephone, is_deleted=False).first()
        
        if not citoyen:
            return None

        if nom is not None:
            citoyen.nom = nom
        if adresse is not None:
            citoyen.adresse = adresse
        if password is not None:
            citoyen.password = bcrypt.generate_password_hash(password).decode('utf-8')
        if role is not None:
            citoyen.role = role
        if username is not None:
            citoyen.username = username
        if image is not None:
            citoyen.image = image
        if prenom is not None:
            citoyen.prenom = prenom

        db.session.commit()
        return citoyen
    except Exception as e:
        db.session.rollback()
        print(f"Erreur mise à jour citoyen par téléphone: {e}")
        return None

# Service de Suppression Logique
def delete_citoyen(citoyen_id):
    """Supprime logiquement un citoyen."""
    try:
        citoyen = Citoyen.query.filter_by(IDuser=citoyen_id, is_deleted=False).first()
        if citoyen:
            citoyen.is_deleted = True
            citoyen.dateDeleted = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Erreur suppression citoyen: {e}")
        return False

# Service d'Authentification
def authenticate_citoyen(username, password):
    """Authentifie un citoyen avec username et password."""
    try:
        citoyen = Citoyen.query.filter_by(username=username, is_deleted=False).first()
        if citoyen and bcrypt.check_password_hash(citoyen.password, password):
            return citoyen
        return None
    except Exception as e:
        print(f"Erreur authentification: {e}")
        return None

# Service de vérification mot de passe
def verify_current_password(citoyen_id, current_password):
    """Vérifie si l'ancien mot de passe est correct."""
    try:
        citoyen = Citoyen.query.filter_by(IDuser=citoyen_id, is_deleted=False).first()
        if citoyen and bcrypt.check_password_hash(citoyen.password, current_password):
            return True
        return False
    except Exception as e:
        print(f"Erreur vérification mot de passe: {e}")
        return False

# Service changement mot de passe sécurisé
def change_password_secure(citoyen_id, old_password, new_password):
    """Change le mot de passe après vérification de l'ancien."""
    try:
        if not verify_current_password(citoyen_id, old_password):
            return {'success': False, 'message': 'Ancien mot de passe incorrect'}
        
        citoyen = Citoyen.query.filter_by(IDuser=citoyen_id, is_deleted=False).first()
        if not citoyen:
            return {'success': False, 'message': 'Utilisateur non trouvé'}
        
        citoyen.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        return {'success': True, 'message': 'Mot de passe modifié avec succès'}
    except Exception as e:
        db.session.rollback()
        print(f"Erreur changement mot de passe: {e}")
        return {'success': False, 'message': 'Erreur interne'}

# ✅ NOUVEAUTÉ: Service JWT avec toutes les informations
def create_full_jwt_token(citoyen, expires_delta=None):
    """Crée un JWT avec toutes les informations du citoyen."""
    try:
        additional_claims = {
            'nom': citoyen.nom,
            'prenom': citoyen.prenom,
            'username': citoyen.username,
            'telephone': citoyen.telephone,
            'adresse': citoyen.adresse,
            'role': citoyen.role,
            'type_user': citoyen.type_user,
            'image': citoyen.image,
            'dateCreated': citoyen.dateCreated.isoformat() if citoyen.dateCreated else None
        }
        
        if expires_delta:
            token = jwt_create_access_token(
                identity=citoyen.IDuser,
                additional_claims=additional_claims,
                expires_delta=expires_delta
            )
        else:
            token = jwt_create_access_token(
                identity=citoyen.IDuser,
                additional_claims=additional_claims
            )
        
        return token
    except Exception as e:
        print(f"Erreur création JWT: {e}")
        return None

# ✅ NOUVEAUTÉ: Validation des données citoyen
def validate_citoyen_data(data):
    """Valide les données avant création/mise à jour."""
    required_fields = ['nom', 'prenom', 'username', 'telephone', 'password', 'adresse']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return {'valid': False, 'message': f'Champs manquants: {", ".join(missing_fields)}'}
    
    # Validation téléphone (exemple simple)
    if len(data['telephone']) < 8:
        return {'valid': False, 'message': 'Numéro de téléphone invalide'}
    
    # Validation mot de passe
    if len(data['password']) < 6:
        return {'valid': False, 'message': 'Mot de passe trop court (minimum 6 caractères)'}
    
    return {'valid': True, 'message': 'Données valides'}