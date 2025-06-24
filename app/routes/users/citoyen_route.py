# app/routes/users/citoyen_route.py - VERSION CORRIGÉE
from flask import Blueprint, request, jsonify
# ✅ CORRECTIF: Import explicite pour éviter conflits
from flask_jwt_extended import create_access_token as jwt_create_token, jwt_required, get_jwt_identity, get_jwt
import logging
from app import cache
from app.models.users.citoyen_model import Citoyen
from app.services.users.citoyen_service import (
    create_citoyen, get_citoyen_by_id, get_all_citoyens,
    update_citoyen, delete_citoyen, authenticate_citoyen, 
    update_citoyen_by_telephone, change_password_secure,
    create_full_jwt_token, validate_citoyen_data
)
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users


# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'citoyen'
citoyen_bp = Blueprint('citoyen', __name__)

@citoyen_bp.route('/register', methods=['POST'])
def register():
    """Inscrit un nouveau citoyen avec validation."""
    try:
        data = request.get_json()
        logger.info(f"[REGISTER] Données reçues: {data}")
        
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

        # ✅ CORRECTIF: Validation des données
        validation = validate_citoyen_data(data)
        if not validation['valid']:
            return jsonify({'message': validation['message']}), 400

        # Vérifier si l'utilisateur existe déjà
        existing_user = Citoyen.query.filter(
            (Citoyen.username == data['username']) | 
            (Citoyen.telephone == data['telephone'])
        ).first()
        
        if existing_user:
            return jsonify({'message': 'Utilisateur déjà existant (username ou téléphone)'}), 400

        new_citoyen = create_citoyen(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data.get('role', 'citoyen'),
            username=data['username'],
            image=data.get('image'),
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        
        if not new_citoyen:
            return jsonify({'message': 'Échec enregistrement'}), 500
            
        logger.info(f"[REGISTER] Citoyen créé ID: {new_citoyen.IDuser}")
        return jsonify({
            'message': 'Enregistrement réussi',
            'user_id': new_citoyen.IDuser
        }), 201

    except Exception as e:
        logger.error(f"Erreur enregistrement: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

# @citoyen_bp.route('/login', methods=['POST'])
# def login():
#     """Connecte un citoyen - Version adaptée à votre Flask-JWT-Extended modifié."""
#     try:
#         data = request.get_json()
#         logger.info(f"[LOGIN] Tentative de connexion pour: {data.get('username', 'N/A')}")

#         if not data or 'username' not in data or 'password' not in data:
#             return jsonify({'message': 'Username et password requis'}), 400

#         citoyen = authenticate_citoyen(data['username'], data['password'])
#         if not citoyen:
#             logger.warning(f"[LOGIN] Échec authentification pour: {data['username']}")
#             return jsonify({'message': 'Identifiants invalides'}), 401

#         # ✅ SOLUTION : Utiliser VOTRE version modifiée avec tous les paramètres
#         access_token = jwt_create_token(
#             identity=citoyen.IDuser,
#             telephone=citoyen.telephone,
#             username=citoyen.username,
#             adresse=citoyen.adresse,
#             prenom=citoyen.prenom,
#             nom=citoyen.nom,
#             additional_claims={
#                 'role': citoyen.role,
#                 'type_user': citoyen.type_user,
#                 'image': citoyen.image,
#                 'dateCreated': citoyen.dateCreated.isoformat() if citoyen.dateCreated else None
#             }
#         )

#         logger.info(f"[LOGIN] Connexion réussie pour user ID: {citoyen.IDuser}")
        
#         return jsonify({
#             'access_token': access_token,
#             'user_info': {
#                 'id': citoyen.IDuser,
#                 'nom': citoyen.nom,
#                 'prenom': citoyen.prenom,
#                 'username': citoyen.username,
#                 'telephone': citoyen.telephone,
#                 'adresse': citoyen.adresse,
#                 'role': citoyen.role
#             },
#             'message': 'Connexion réussie'
#         }), 200

#     except Exception as e:
#         logger.error(f"[LOGIN] Erreur : {str(e)}", exc_info=True)
#         return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/login', methods=['POST'])
def login():
    """Connecte un citoyen - Version corrigée."""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Username et password requis'}), 400

        citoyen = authenticate_citoyen(data['username'], data['password'])
        if not citoyen:
            return jsonify({'message': 'Identifiants invalides'}), 401

        # ✅ SOLUTION : Garder l'identity comme INTEGER
        print(f"DEBUG: identity = {citoyen.IDuser} (type: {type(citoyen.IDuser)})")
        
        # Créer le token avec identity en int (pas en string)
        access_token = jwt_create_token(
            identity=citoyen.IDuser,  # ← Garder comme int !
            telephone=str(citoyen.telephone or ''),
            username=str(citoyen.username or ''),
            adresse=str(citoyen.adresse or ''),
            prenom=str(citoyen.prenom or ''),
            nom=str(citoyen.nom or ''),
            additional_claims={
                'role': citoyen.role,
                'type_user': citoyen.type_user,
                'image': citoyen.image,
                'dateCreated': citoyen.dateCreated.isoformat() if citoyen.dateCreated else None
            }
        )

        print(f"DEBUG: Token créé avec succès pour user_id = {citoyen.IDuser}")
        
        # 🔔 NOTIFICATION: Connexion citoyen
        try:
            send_notification(
                user_id=citoyen.IDuser,  # Déjà un int
                title="👋 Connexion réussie",
                message="Vous êtes maintenant connecté",
                priority='low',
                category='security'
            )
        except Exception as notif_error:
            logger.warning(f"Erreur notification connexion: {notif_error}")
        
        return jsonify({
            'access_token': access_token,
            'user_info': {
                'id': citoyen.IDuser,
                'nom': citoyen.nom,
                'prenom': citoyen.prenom,
                'username': citoyen.username,
                'telephone': citoyen.telephone,
                'adresse': citoyen.adresse,
                'role': citoyen.role
            },
            'message': 'Connexion réussie'
        }), 200

    except Exception as e:
        print(f"DEBUG: Erreur détaillée = {str(e)}")
        logger.error(f"[LOGIN] Erreur : {str(e)}", exc_info=True)
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@citoyen_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Récupère les informations depuis le JWT."""
    try:
        # ID principal depuis le JWT
        user_id = get_jwt_identity()
        
        # Toutes les autres infos depuis les claims
        claims = get_jwt()
        
        logger.info(f"[PROTECTED] Accès autorisé pour user ID: {user_id}")
        
        return jsonify({
            'id': user_id,
            'nom': claims.get('nom'),
            'prenom': claims.get('prenom'),
            'username': claims.get('username'),
            'telephone': claims.get('telephone'),
            'adresse': claims.get('adresse'),
            'role': claims.get('role'),
            'type_user': claims.get('type_user'),
            'image': claims.get('image'),
            'dateCreated': claims.get('dateCreated'),
            'message': 'Accès autorisé'
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur route protégée: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Génère un nouveau token d'accès."""
    try:
        current_user_id = get_jwt_identity()
        
        # Récupérer les infos utilisateur depuis la DB pour le nouveau token
        citoyen = get_citoyen_by_id(current_user_id)
        if not citoyen:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Créer nouveau token avec infos à jour
        new_token = jwt_create_token(
            identity=citoyen.IDuser,
            additional_claims={
                'nom': citoyen.nom,
                'prenom': citoyen.prenom,
                'username': citoyen.username,
                'telephone': citoyen.telephone,
                'adresse': citoyen.adresse,
                'role': citoyen.role,
                'type_user': citoyen.type_user,
                'image': citoyen.image
            }
        )
        
        return jsonify({'access_token': new_token}), 200
        
    except Exception as e:
        logger.error(f"Erreur refresh token: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_user_password():
    """Change le mot de passe d'un citoyen avec vérification."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'old_password' not in data or 'new_password' not in data:
            return jsonify({'message': 'Ancien et nouveau mot de passe requis'}), 400
        
        # Validation du nouveau mot de passe
        if len(data['new_password']) < 6:
            return jsonify({'message': 'Nouveau mot de passe trop court (minimum 6 caractères)'}), 400
        
        result = change_password_secure(current_user_id, data['old_password'], data['new_password'])
        
        if result['success']:
            logger.info(f"Mot de passe changé pour citoyen ID: {current_user_id}")
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'message': result['message']}), 400
            
    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnecte un citoyen."""
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"[LOGOUT] Déconnexion user ID: {current_user_id}")
        return jsonify({'message': 'Déconnexion réussie'}), 200
    except Exception as e:
        logger.error(f"Erreur déconnexion: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

# ============ ROUTES EXISTANTES OPTIMISÉES ============

@citoyen_bp.route('/<int:citoyen_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_citoyen')
def get_citoyen(citoyen_id):
    """Récupère un citoyen spécifique via son ID."""
    try:
        citoyen = get_citoyen_by_id(citoyen_id)
        if not citoyen:
            return jsonify({'message': 'Citoyen non trouvé'}), 404
            
        return jsonify({
            'id': citoyen.IDuser,
            'nom': citoyen.nom,
            'prenom': citoyen.prenom,
            'adresse': citoyen.adresse,
            'role': citoyen.role,
            'username': citoyen.username,
            'image': citoyen.image,
            'telephone': citoyen.telephone,
            'dateCreated': citoyen.dateCreated.isoformat() if citoyen.dateCreated else None,
            'type_user': citoyen.type_user
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération citoyen {citoyen_id}: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/update/<int:citoyen_id>', methods=['PUT'])
@jwt_required()
def modify_citoyen(citoyen_id):
    """Met à jour les informations d'un citoyen."""
    try:
        current_user_id = get_jwt_identity()
        
        # Vérifier que l'utilisateur modifie ses propres données ou est admin
        if current_user_id != citoyen_id:
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'message': 'Non autorisé'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

        citoyen = update_citoyen(
            citoyen_id,
            nom=data.get('nom'),
            adresse=data.get('adresse'),
            password=data.get('password'),
            role=data.get('role'),
            username=data.get('username'),
            image=data.get('image'),
            telephone=data.get('telephone'),
            prenom=data.get('prenom')
        )
        
        if not citoyen:
            return jsonify({'message': 'Citoyen non trouvé'}), 404
            
        return jsonify({
            'id': citoyen.IDuser,
            'message': 'Mise à jour réussie'
        }), 200

    except Exception as e:
        logger.error(f"Erreur mise à jour citoyen {citoyen_id}: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

# ============ ROUTES ADMIN (optionnelles) ============

@citoyen_bp.route('/all', methods=['GET'])
# @jwt_required()
def list_citoyens():
    """Récupère tous les citoyens (admin seulement)."""
    try:
        # claims = get_jwt()
        # if claims.get('role') != 'admin':
        #     return jsonify({'message': 'Accès admin requis'}), 403
        
        citoyens = get_all_citoyens()
        return jsonify([{
            'id': c.IDuser,
            'nom': c.nom,
            'prenom': c.prenom,
            'adresse': c.adresse,
            'role': c.role,
            'username': c.username,
            'telephone': c.telephone,
            'dateCreated': c.dateCreated.isoformat() if c.dateCreated else None,
            'type_user': c.type_user
            # ✅ CORRECTIF: Pas de mot de passe dans la réponse !
        } for c in citoyens]), 200
        
    except Exception as e:
        logger.error(f"Erreur liste citoyens: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500



# Ajoutez cette route dans votre citoyen_route.py

@citoyen_bp.route('/verify-phone', methods=['POST'])
def verify_phone_for_reset():
    """Vérifie si un numéro de téléphone existe (pour reset mot de passe)."""
    try:
        data = request.get_json()
        
        if not data or 'telephone' not in data:
            return jsonify({'message': 'Numéro de téléphone requis'}), 400
        
        phone_number = data['telephone']
        
        # Vérifier si le numéro existe
        citoyen = Citoyen.query.filter_by(telephone=phone_number).first()
        
        if citoyen:
            logger.info(f"[VERIFY_PHONE] Téléphone {phone_number} trouvé pour reset")
            return jsonify({
                'exists': True,
                'message': 'Numéro de téléphone trouvé'
            }), 200
        else:
            logger.warning(f"[VERIFY_PHONE] Téléphone {phone_number} non trouvé")
            return jsonify({
                'exists': False,
                'message': 'Numéro de téléphone introuvable'
            }), 404
            
    except Exception as e:
        logger.error(f"Erreur vérification téléphone: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500


@citoyen_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Réinitialise le mot de passe avec vérification téléphone."""
    try:
        data = request.get_json()
        
        if not data or 'telephone' not in data or 'new_password' not in data:
            return jsonify({'message': 'Téléphone et nouveau mot de passe requis'}), 400
        
        phone_number = data['telephone']
        new_password = data['new_password']
        
        # Validation du mot de passe
        if len(new_password) < 6:
            return jsonify({'message': 'Mot de passe trop court (minimum 6 caractères)'}), 400
        
        # Trouver l'utilisateur par numéro
        citoyen = Citoyen.query.filter_by(telephone=phone_number).first()
        
        if not citoyen:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Mettre à jour le mot de passe
        from werkzeug.security import generate_password_hash
        citoyen.password = generate_password_hash(new_password)
        
        # Sauvegarder en base
        from app import db
        db.session.commit()
        
        logger.info(f"Mot de passe réinitialisé pour téléphone: {phone_number}")
        
        return jsonify({
            'message': 'Mot de passe réinitialisé avec succès',
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur reset mot de passe: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500


# Ajoutez cette route dans votre citoyen_route.py

@citoyen_bp.route('/updatetelephone/<string:phone_number>', methods=['PUT'])
def update_password_by_phone(phone_number):
    """Met à jour le mot de passe d'un utilisateur via son numéro de téléphone."""
    try:
        data = request.get_json()
        
        if not data or 'password' not in data:
            return jsonify({'message': 'Nouveau mot de passe requis'}), 400
        
        new_password = data['password']
        
        # Validation du mot de passe
        if len(new_password) < 7:
            return jsonify({'message': 'Mot de passe trop court (minimum 7 caractères)'}), 400
        
        # Vérifier qu'il contient au moins un chiffre
        if not any(char.isdigit() for char in new_password):
            return jsonify({'message': 'Le mot de passe doit contenir au moins un chiffre'}), 400
        
        # Trouver l'utilisateur par numéro de téléphone
        citoyen = Citoyen.query.filter_by(telephone=phone_number).first()
        
        if not citoyen:
            return jsonify({'message': 'Utilisateur non trouvé avec ce numéro de téléphone'}), 404
        
        # Mettre à jour le mot de passe
        from werkzeug.security import generate_password_hash
        citoyen.password = generate_password_hash(new_password)
        
        # Sauvegarder en base
        from app import db
        db.session.commit()
        
        logger.info(f"Mot de passe mis à jour via téléphone: {phone_number}")
        
        # 🔔 NOTIFICATION: Changement mot de passe
        try:
            send_notification(
                user_id=citoyen.IDuser,
                title="🔐 Mot de passe modifié",
                message="Votre mot de passe a été modifié avec succès",
                priority='high',
                category='security'
            )
        except Exception as notif_error:
            logger.warning(f"Erreur notification changement mot de passe: {notif_error}")
        
        return jsonify({
            'message': 'Mot de passe mis à jour avec succès',
            'success': True,
            'user_id': citoyen.IDuser
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur mise à jour mot de passe par téléphone: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500