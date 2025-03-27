from flask import Blueprint, request, jsonify
import logging
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app import cache
from app.models.users.autorite_model import Authorite
from app.services.users.autorite_service import (
    create_authorite, get_authorite_by_id, get_all_authorites,
    update_authorite, delete_authorite, authenticate_authorite
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'autorite'
autorite_bp = Blueprint('autorite', __name__)

# Route pour créer un nouvel enregistrement
@autorite_bp.route('/add', methods=['POST'])
def add_authorite():
    """
    Ajoute une nouvelle autorité.
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
              example: "Dupont"
            adresse:
              type: string
              example: "123 Rue Exemple"
            password:
              type: string
              example: "password123"
            role:
              type: string
              example: "admin"
            username:
              type: string
              example: "dupont"
            image:
              type: string
              example: "url_to_image"
            telephone:
              type: string
              example: "0123456789"
            typeAuthorite:
              type: string
              example: "type1"
            description:
              type: string
              example: "Description de l'autorité"
    responses:
      201:
        description: Autorité créée avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'typeAuthorite', 'description']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer une autorité")
            return jsonify({'message': 'Bad Request'}), 400

        new_authorite = create_authorite(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data['image'],
            telephone=data['telephone'],
            typeAuthorite=data['typeAuthorite'],
            description=data['description']
        )
        logger.info(f"Nouvelle autorité créée avec l'ID: {new_authorite.IDuser}")
        return jsonify({'id': new_authorite.IDuser}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'une autorité: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@autorite_bp.route('/<int:authorite_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_authorite')
def get_authorite(authorite_id):
    """
    Récupère une autorité spécifique via son ID.
    ---
    parameters:
      - name: authorite_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails de l'autorité
      404:
        description: Autorité non trouvée
    """
    logger.info(f"Récupération de l'autorité avec l'ID: {authorite_id}")
    authorite = get_authorite_by_id(authorite_id)
    if authorite:
        return jsonify({
            'id': authorite.IDuser,
            'nom': authorite.nom,
            'adresse': authorite.adresse,
            'role': authorite.role,
            'username': authorite.username,
            'image': authorite.image,
            'telephone': authorite.telephone,
            'typeAuthorite': authorite.typeAuthorite,
            'description': authorite.description,
            'dateCreated': authorite.dateCreated,
            'type_user': authorite.type_user
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@autorite_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_authorites')
def list_authorites():
    """
    Récupère toutes les autorités enregistrées.
    ---
    responses:
      200:
        description: Liste des autorités
    """
    logger.info("Récupération de toutes les autorités")
    authorites = get_all_authorites()
    return jsonify([{
        'id': a.IDuser,
        'nom': a.nom,
        'adresse': a.adresse,
        'role': a.role,
        'username': a.username,
        'image': a.image,
        'telephone': a.telephone,
        'typeAuthorite': a.typeAuthorite,
        'description': a.description,
        'dateCreated': a.dateCreated,
        'type_user': a.type_user
    } for a in authorites])

# Route pour mettre à jour un enregistrement
@autorite_bp.route('/update/<int:authorite_id>', methods=['PUT'])
def modify_authorite(authorite_id):
    """
    Met à jour les informations d'une autorité.
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
              example: "Dupont"
            adresse:
              type: string
              example: "123 Rue Exemple"
            password:
              type: string
              example: "newpassword123"
            role:
              type: string
              example: "admin"
            username:
              type: string
              example: "dupont"
            image:
              type: string
              example: "url_to_new_image"
            telephone:
              type: string
              example: "0123456789"
            typeAuthorite:
              type: string
              example: "type1"
            description:
              type: string
              example: "Nouvelle description"
    responses:
      200:
        description: Autorité mise à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Autorité non trouvée
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes reçues pour mettre à jour une autorité")
            return jsonify({'message': 'Bad Request'}), 400

        authorite = update_authorite(
            authorite_id,
            nom=data.get('nom'),
            adresse=data.get('adresse'),
            password=data.get('password'),
            role=data.get('role'),
            username=data.get('username'),
            image=data.get('image'),
            telephone=data.get('telephone'),
            typeAuthorite=data.get('typeAuthorite'),
            description=data.get('description')
        )
        if authorite:
            logger.info(f"Autorité avec l'ID {authorite_id} mise à jour")
            return jsonify({'id': authorite.IDuser}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'une autorité: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@autorite_bp.route('/delete/<int:authorite_id>', methods=['DELETE'])
def remove_authorite(authorite_id):
    """
    Supprime une autorité de la base de données.
    ---
    parameters:
      - name: authorite_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Autorité non trouvée
      500:
        description: Erreur serveur
    """
    try:
        success = delete_authorite(authorite_id)
        if success:
            logger.info(f"Autorité avec l'ID {authorite_id} supprimée")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'une autorité: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour l'inscription
@autorite_bp.route('/register', methods=['POST'])
def register():
    """
    Inscrit une nouvelle autorité.
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
              example: "Dupont"
            adresse:
              type: string
              example: "123 Rue Exemple"
            password:
              type: string
              example: "password123"
            role:
              type: string
              example: "admin"
            username:
              type: string
              example: "dupont"
            image:
              type: string
              example: "url_to_image"
            telephone:
              type: string
              example: "0123456789"
            typeAuthorite:
              type: string
              example: "type1"
            description:
              type: string
              example: "Description de l'autorité"
    responses:
      201:
        description: Autorité enregistrée avec succès
      400:
        description: Données incomplètes ou type d'utilisateur invalide
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'typeAuthorite', 'description']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour enregistrer une autorité")
            return jsonify({'message': 'Bad Request'}), 400

        user_type = data.get('user_type')
        if user_type != 'authorite':
            return jsonify({'message': 'Invalid user type'}), 400

        new_authorite, access_token = create_authorite(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data['image'],
            telephone=data['telephone'],
            typeAuthorite=data['typeAuthorite'],
            description=data['description']
        )
        if not new_authorite:
            return jsonify({'message': 'Authorite creation failed'}), 400

        logger.info(f"Nouvelle autorité enregistrée avec l'ID: {new_authorite.IDuser}")
        return jsonify({'message': 'Authorite registered successfully', 'access_token': access_token}), 201

    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement d'une autorité: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour la connexion
@autorite_bp.route('/login', methods=['POST'])
def login():
    """
    Connecte une autorité.
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
              example: "dupont"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: Connexion réussie
      400:
        description: Données incomplètes
      401:
        description: Identifiants invalides
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['username', 'password']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour se connecter")
            return jsonify({'message': 'Bad Request'}), 400

        authorite = authenticate_authorite(data['username'], data['password'])
        if authorite:
            access_token = create_access_token(identity=authorite.IDuser)
            logger.info(f"Autorité {authorite.IDuser} connectée")
            return jsonify(access_token=access_token), 200
        return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Erreur lors de la connexion d'une autorité: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour la déconnexion
@autorite_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Déconnecte une autorité.
    ---
    responses:
      200:
        description: Déconnexion réussie
    """
    logger.info(f"Autorité déconnectée")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@autorite_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Récupère les informations de l'autorité connectée.
    ---
    responses:
      200:
        description: Détails de l'autorité connectée
    """
    current_authorite_id = get_jwt_identity()
    authorite = Authorite.query.get(current_authorite_id)
    return jsonify({
        'id': authorite.IDuser,
        'nom': authorite.nom,
        'role': authorite.role,
        'username': authorite.username
    }), 200