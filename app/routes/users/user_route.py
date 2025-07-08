from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import logging
from app import cache
from app.models.users.user_model import User
from app.services.users.user_service import (
    create_user, get_user_by_id, get_all_users,
    update_user, delete_user, authenticate_user
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'user'
user_bp = Blueprint('user', __name__)

# Configuration commune
REQUIRED_FIELDS = ['nom', 'adresse', 'password', 'role', 'username', 'telephone', 'user_type']
VALID_USER_TYPES = ['admin', 'authorite', 'citoyen', 'moderateur']

def validate_user_data(data, require_type=True):
    """
    Valide les données de l'utilisateur.
    
    :param data: Données de l'utilisateur à valider
    :param require_type: Indique si le type d'utilisateur doit être validé
    :return: True si les données sont valides, sinon False
    """
    if not data or any(field not in data for field in REQUIRED_FIELDS):
        logger.error("Données utilisateur incomplètes")
        return False
    if require_type and data.get('user_type') not in VALID_USER_TYPES:
        logger.error("Type utilisateur invalide")
        return False
    return True

@user_bp.route('/add', methods=['POST'])
def add_user():
    """
    Ajoute un nouvel utilisateur.
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
            adresse:
              type: string
            password:
              type: string
            role:
              type: string
            username:
              type: string
            telephone:
              type: string
            user_type:
              type: string
    responses:
      201:
        description: Utilisateur créé avec succès
      400:
        description: Données incomplètes pour créer un utilisateur
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not validate_user_data(data):
            return jsonify({'message': 'Bad Request'}), 400

        extra_fields = {k: v for k, v in data.items() if k not in REQUIRED_FIELDS + ['image']}
        
        new_user, access_token = create_user(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data.get('image'),
            telephone=data['telephone'],
            user_type=data['user_type'],
            **extra_fields
        )
        
        if not new_user:
            return jsonify({'message': 'Échec de la création'}), 400

        logger.info(f"Utilisateur créé ID: {new_user.IDuser}")
        return jsonify({
            'id': new_user.IDuser,
            'access_token': access_token,
            'type': new_user.type_user
        }), 201

    except Exception as e:
        logger.error(f"Erreur création utilisateur: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Remplacez cette partie dans votre user_route.py

@user_bp.route('/<int:user_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_user_by_id')  # ← Changé le key_prefix
def get_user_by_id_route(user_id):  # ← Changé le nom de la fonction
    """
    Récupère un utilisateur spécifique via son ID.
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
            
        return jsonify({
            'id': user.IDuser,
            'nom': user.nom,
            'adresse': user.adresse,
            'role': user.role,
            'username': user.username,
            'image': user.image,
            'telephone': user.telephone,
            'dateCreated': user.dateCreated,
            'type': user.type_user
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération utilisateur {user_id}: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500


@user_bp.route('/check/<string:username>', methods=['GET'])  # ← Changé le chemin pour éviter conflit
@cache.cached(timeout=60, key_prefix='check_user_by_username')
def check_user_by_username(username):
    """
    Vérifie l'existence d'un utilisateur et retourne son type.
    ---
    parameters:
      - name: username
        in: path
        required: true
        type: string
        example: "john_doe"
    responses:
      200:
        description: Utilisateur trouvé
      404:
        description: Utilisateur non trouvé
    """
    try:
        logger.info(f"🔍 Vérification de l'existence du username: {username}")
        
        # Importer les modèles nécessaires
        from app.models.users.admin_model import Admin
        from app.models.users.moderateur_model import Moderateur  
        from app.models.users.autorite_model import Authorite
        from app.models.users.citoyen_model import Citoyen
        
        # Rechercher dans chaque table d'utilisateur
        user_tables = [
            (Admin, 'admin'),
            (Moderateur, 'moderateur'), 
            (Authorite, 'authorite'),
            (Citoyen, 'citoyen')
        ]
        
        for UserModel, user_type in user_tables:
            user = UserModel.query.filter_by(username=username).first()
            
            if user:
                logger.info(f"✅ Utilisateur trouvé - Type: {user_type}, ID: {user.IDuser}")
                
                return jsonify({
                    'exists': True,
                    'user_type': user_type,
                    'type_user': user_type,  # Alias pour compatibilité
                    'user_id': user.IDuser,
                    'id': user.IDuser,  # Alias pour compatibilité
                    'username': user.username,
                    'message': f'Utilisateur {user_type} trouvé'
                }), 200
        
        # Aucun utilisateur trouvé
        logger.info(f"❌ Aucun utilisateur trouvé avec le username: {username}")
        return jsonify({
            'exists': False,
            'message': 'Utilisateur non trouvé'
        }), 404
        
    except Exception as e:
        logger.error(f"💥 Erreur lors de la vérification de l'utilisateur {username}: {str(e)}")
        return jsonify({
            'exists': False,
            'message': 'Erreur interne du serveur'
        }), 500


@user_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_users')
def list_users():
    """
    Récupère tous les utilisateurs enregistrés.
    ---
    responses:
      200:
        description: Liste des utilisateurs
      500:
        description: Erreur interne
    """
    try:
        users = get_all_users()
        return jsonify([{
            'id': u.IDuser,
            'nom': u.nom,
            'type': u.type_user,
            'username': u.username,
            'role': u.role
        } for u in users])
        
    except Exception as e:
        logger.error(f"Erreur liste utilisateurs: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

@user_bp.route('/update/<int:user_id>', methods=['PUT'])
def modify_user(user_id):
    """
    Met à jour les informations d'un utilisateur.
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
            adresse:
              type: string
            password:
              type: string
            role:
              type: string
            username:
              type: string
            telephone:
              type: string
    responses:
      200:
        description: Utilisateur mis à jour avec succès
      400:
        description: Données manquantes
      404:
        description: Utilisateur non trouvé
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

        extra_fields = {k: v for k, v in data.items() if k not in REQUIRED_FIELDS}
        
        user = update_user(
            user_id,
            nom=data.get('nom'),
            adresse=data.get('adresse'),
            password=data.get('password'),
            role=data.get('role'),
            username=data.get('username'),
            image=data.get('image'),
            telephone=data.get('telephone'),
            **extra_fields
        )
        
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
            
        return jsonify({
            'id': user.IDuser,
            'type': user.type_user
        }), 200

    except Exception as e:
        logger.error(f"Erreur mise à jour utilisateur {user_id}: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    """
    Supprime un utilisateur de la base de données.
    ---
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      204:
        description: Suppression réussie
      404:
        description: Utilisateur non trouvé
      500:
        description: Erreur interne
    """
    try:
        success = delete_user(user_id)
        if not success:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
            
        return '', 204
        
    except Exception as e:
        logger.error(f"Erreur suppression utilisateur {user_id}: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

@user_bp.route('/register', methods=['POST'])
def register():
    """
    Inscrit un nouvel utilisateur.
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
            adresse:
              type: string
            password:
              type: string
            role:
              type: string
            username:
              type: string
            telephone:
              type: string
            user_type:
              type: string
    responses:
      201:
        description: Enregistrement réussi
      400:
        description: Données incomplètes ou type d'utilisateur invalide
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not validate_user_data(data):
            return jsonify({'message': 'Bad Request'}), 400

        extra_fields = {k: v for k, v in data.items() if k not in REQUIRED_FIELDS + ['image']}
        
        new_user, access_token = create_user(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data.get('image'),
            telephone=data['telephone'],
            user_type=data['user_type'],
            **extra_fields
        )
        
        if not new_user:
            return jsonify({'message': 'Échec enregistrement'}), 400
            
        return jsonify({
            'message': 'Enregistrement réussi',
            'access_token': access_token,
            'user_type': new_user.type_user
        }), 201

    except Exception as e:
        logger.error(f"Erreur enregistrement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """
    Connecte un utilisateur.
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Connexion réussie
      400:
        description: Identifiants requis
      401:
        description: Authentification échouée
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Identifiants requis'}), 400

        user = authenticate_user(data['username'], data['password'])
        if not user:
            return jsonify({'message': 'Authentification échouée'}), 401
        
        # ✅ CORRECTIF: Utiliser la même structure que l'admin
        # Utiliser getattr pour gérer les champs qui peuvent ne pas exister
        access_token = create_access_token(
            identity=str(user.IDuser),
            telephone=str(getattr(user, 'telephone', '') or ''),
            username=str(user.username or ''),
            adresse=str(user.adresse or ''),
            prenom=str(getattr(user, 'prenom', '') or ''),
            nom=str(user.nom or ''),
            additional_claims={
                'role': user.role,
                'type_user': user.type_user,
                'image': getattr(user, 'image', None),
                'dateCreated': user.dateCreated.isoformat() if user.dateCreated else None
            }
        )
        
        logger.info(f"Utilisateur {user.IDuser} connecté")
        return jsonify({
            'access_token': access_token,
            'user_type': user.type_user,
            'user_info': {
                'id': user.IDuser,
                'nom': user.nom,
                'prenom': getattr(user, 'prenom', ''),
                'username': user.username,
                'telephone': getattr(user, 'telephone', ''),
                'adresse': user.adresse,
                'role': user.role,
                'type_user': user.type_user
            }
        }), 200

    except Exception as e:
        logger.error(f"Erreur connexion: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Déconnecte un utilisateur.
    ---
    responses:
      200:
        description: Déconnexion réussie
      500:
        description: Erreur interne
    """
    try:
        logger.info("Déconnexion utilisateur")
        return jsonify({'message': 'Déconnexion réussie'}), 200
    except Exception as e:
        logger.error(f"Erreur déconnexion: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

@user_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Récupère les informations de l'utilisateur connecté.
    ---
    responses:
      200:
        description: Détails de l'utilisateur connecté
      404:
        description: Utilisateur non trouvé
      500:
        description: Erreur interne
    """
    try:
        current_id = get_jwt_identity()
        user = User.query.get(current_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
            
        return jsonify({
            'id': user.IDuser,
            'nom': user.nom,
            'role': user.role,
            'username': user.username,
            'type': user.type_user
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur route protégée: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500