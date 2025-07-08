from flask import Blueprint, request, jsonify
import logging
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app import cache
from app.models.users.moderateur_model import Moderateur
from app.services.users.moderateur_service import (
    create_moderateur, get_moderateur_by_id, get_all_moderateurs,
    update_moderateur, delete_moderateur, authenticate_moderateur
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'moderateur'
moderateur_bp = Blueprint('moderateur', __name__)

# Route pour créer un nouvel enregistrement
@moderateur_bp.route('/add', methods=['POST'])
def add_moderateur():
    """
    Ajoute un nouveau modérateur.
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
            image:
              type: string
            telephone:
              type: string
            prenom:
              type: string
    responses:
      201:
        description: Modérateur créé avec succès
      400:
        description: Données incomplètes pour créer un modérateur
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'prenom']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes pour créer un modérateur")
            return jsonify({'message': 'Bad Request'}), 400

        new_moderateur = create_moderateur(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data['image'],
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        if not new_moderateur:
            return jsonify({'message': 'Échec création modérateur'}), 400

        logger.info(f"Nouveau modérateur créé avec l'ID: {new_moderateur.IDuser}")
        return jsonify({'id': new_moderateur.IDuser}), 201

    except Exception as e:
        logger.error(f"Erreur création modérateur: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@moderateur_bp.route('/<int:moderateur_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_moderateur')
def get_moderateur(moderateur_id):
    """
    Récupère un modérateur spécifique via son ID.
    ---
    parameters:
      - name: moderateur_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Détails du modérateur
      404:
        description: Modérateur non trouvé
      500:
        description: Erreur interne
    """
    logger.info(f"Récupération du modérateur avec l'ID: {moderateur_id}")
    moderateur = get_moderateur_by_id(moderateur_id)
    if moderateur:
        return jsonify({
            'id': moderateur.IDuser,
            'nom': moderateur.nom,
            'adresse': moderateur.adresse,
            'role': moderateur.role,
            'username': moderateur.username,
            'image': moderateur.image,
            'telephone': moderateur.telephone,
            'prenom': moderateur.prenom,
            'dateCreated': moderateur.dateCreated,
            'type_user': moderateur.type_user
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@moderateur_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_moderateurs')
def list_moderateurs():
    """
    Récupère tous les modérateurs enregistrés.
    ---
    responses:
      200:
        description: Liste des modérateurs
      500:
        description: Erreur interne
    """
    logger.info("Récupération de tous les modérateurs")
    moderateurs = get_all_moderateurs()
    return jsonify([{
        'id': m.IDuser,
        'nom': m.nom,
        'adresse': m.adresse,
        'role': m.role,
        'username': m.username,
        'image': m.image,
        'telephone': m.telephone,
        'prenom': m.prenom,
        'dateCreated': m.dateCreated,
        'type_user': m.type_user
    } for m in moderateurs])

# Route pour mettre à jour un enregistrement
@moderateur_bp.route('/update/<int:moderateur_id>', methods=['PUT'])
def modify_moderateur(moderateur_id):
    """
    Met à jour les informations d'un modérateur.
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
            image:
              type: string
            telephone:
              type: string
            prenom:
              type: string
    responses:
      200:
        description: Modérateur mis à jour avec succès
      400:
        description: Données manquantes
      404:
        description: Modérateur non trouvé
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes pour mettre à jour un modérateur")
            return jsonify({'message': 'Bad Request'}), 400

        moderateur = update_moderateur(
            moderateur_id,
            nom=data.get('nom'),
            adresse=data.get('adresse'),
            password=data.get('password'),
            role=data.get('role'),
            username=data.get('username'),
            image=data.get('image'),
            telephone=data.get('telephone'),
            prenom=data.get('prenom')
        )
        if moderateur:
            logger.info(f"Modérateur avec l'ID {moderateur_id} mis à jour")
            return jsonify({'id': moderateur.IDuser}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur mise à jour modérateur: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@moderateur_bp.route('/delete/<int:moderateur_id>', methods=['DELETE'])
def remove_moderateur(moderateur_id):
    """
    Supprime un modérateur de la base de données.
    ---
    parameters:
      - name: moderateur_id
        in: path
        required: true
        type: integer
    responses:
      204:
        description: Suppression réussie
      404:
        description: Modérateur non trouvé
      500:
        description: Erreur interne
    """
    try:
        success = delete_moderateur(moderateur_id)
        if success:
            logger.info(f"Modérateur avec l'ID {moderateur_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur suppression modérateur: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour l'inscription
@moderateur_bp.route('/register', methods=['POST'])
def register():
    """
    Inscrit un nouveau modérateur.
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
            image:
              type: string
            telephone:
              type: string
            prenom:
              type: string
    responses:
      201:
        description: Modérateur enregistré avec succès
      400:
        description: Données incomplètes ou type d'utilisateur invalide
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'prenom']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes pour enregistrer un modérateur")
            return jsonify({'message': 'Bad Request'}), 400

        user_type = data.get('user_type')
        if user_type != 'moderateur':
            return jsonify({'message': 'Invalid user type'}), 400

        new_moderateur, access_token = create_moderateur(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data['image'],
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        if not new_moderateur:
            return jsonify({'message': 'Échec création modérateur'}), 400

        logger.info(f"Nouveau modérateur enregistré avec l'ID: {new_moderateur.IDuser}")
        return jsonify({'message': 'Modérateur registered successfully', 'access_token': access_token}), 201

    except Exception as e:
        logger.error(f"Erreur enregistrement modérateur: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour la connexion
@moderateur_bp.route('/login', methods=['POST'])
def login():
    """
    Connecte un modérateur.
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
        description: Données incomplètes
      401:
        description: Identifiants invalides
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        required_fields = ['username', 'password']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes pour se connecter")
            return jsonify({'message': 'Bad Request'}), 400

        moderateur = authenticate_moderateur(data['username'], data['password'])
        
        if moderateur:
            # ✅ CORRECTIF: Utiliser la même structure que l'admin
            access_token = create_access_token(
                identity=str(moderateur.IDuser),
                telephone=str(moderateur.telephone or ''),
                username=str(moderateur.username or ''),
                adresse=str(moderateur.adresse or ''),
                prenom=str(moderateur.prenom or ''),
                nom=str(moderateur.nom or ''),
                additional_claims={
                    'role': moderateur.role,
                    'type_user': moderateur.type_user,
                    'image': moderateur.image,
                    'dateCreated': moderateur.dateCreated.isoformat() if moderateur.dateCreated else None
                }
            )
            
            logger.info(f"Modérateur {moderateur.IDuser} connecté")
            return jsonify({
                'access_token': access_token,
                'user_type': moderateur.type_user,
                'user_info': {
                    'id': moderateur.IDuser,
                    'nom': moderateur.nom,
                    'prenom': moderateur.prenom,
                    'username': moderateur.username,
                    'telephone': moderateur.telephone,
                    'adresse': moderateur.adresse,
                    'role': moderateur.role,
                    'type_user': moderateur.type_user
                }
            }), 200
        return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Erreur connexion modérateur: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour la déconnexion
@moderateur_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Déconnecte un modérateur.
    ---
    responses:
      200:
        description: Déconnexion réussie
      500:
        description: Erreur interne
    """
    logger.info(f"Modérateur déconnecté")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@moderateur_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Récupère les informations du modérateur connecté.
    ---
    responses:
      200:
        description: Détails du modérateur connecté
      404:
        description: Modérateur non trouvé
      500:
        description: Erreur interne
    """
    current_moderateur_id = get_jwt_identity()
    moderateur = Moderateur.query.get(current_moderateur_id)
    return jsonify({
        'id': moderateur.IDuser,
        'nom': moderateur.nom,
        'role': moderateur.role,
        'username': moderateur.username
    }), 200