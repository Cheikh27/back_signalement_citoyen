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

@user_bp.route('/<int:user_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_user')
def get_user(user_id):
    """
    Récupère un utilisateur spécifique via son ID.
    ---
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Détails de l'utilisateur
      404:
        description: Utilisateur non trouvé
      500:
        description: Erreur interne
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
            return jsonify({'message': 'Authentification échouée '}), 401
            
        access_token = create_access_token(identity=user.IDuser)
        return jsonify({
            'access_token': access_token,
            'user_type': user.type_user
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