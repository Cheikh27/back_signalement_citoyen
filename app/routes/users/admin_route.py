from flask import Blueprint, request, jsonify
import logging
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app import cache
from app.models.users.admin_model import Admin
from app.services.users.admin_service import (
    create_admin, get_admin_by_id, get_all_admins,
    update_admin, delete_admin, authenticate_admin
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'admin'
admin_bp = Blueprint('admin', __name__)

# Route pour créer un nouvel enregistrement
@admin_bp.route('/add', methods=['POST'])
def add_admin():
    """
    Ajoute un nouvel administrateur.
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
            prenom:
              type: string
              example: "Jean"
    responses:
      201:
        description: Administrateur créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'prenom']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un admin")
            return jsonify({'message': 'Bad Request'}), 400

        new_admin = create_admin(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data['image'],
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        logger.info(f"Nouvel admin créé avec l'ID: {new_admin.IDuser}")
        return jsonify({'id': new_admin.IDuser}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un admin: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@admin_bp.route('/<int:admin_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_admin')
def get_admin(admin_id):
    """
    Récupère un administrateur spécifique via son ID.
    ---
    parameters:
      - name: admin_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails de l'administrateur
      404:
        description: Administrateur non trouvé
    """
    logger.info(f"Récupération de l'admin avec l'ID: {admin_id}")
    admin = get_admin_by_id(admin_id)
    if admin:
        return jsonify({
            'id': admin.IDuser,
            'nom': admin.nom,
            'adresse': admin.adresse,
            'role': admin.role,
            'username': admin.username,
            'image': admin.image,
            'telephone': admin.telephone,
            'dateCreated': admin.dateCreated,
            'prenom': admin.prenom,
            'type_user': admin.type_user
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@admin_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_admins')
def list_admins():
    """
    Récupère tous les administrateurs enregistrés.
    ---
    responses:
      200:
        description: Liste des administrateurs
    """
    logger.info("Récupération de tous les admins")
    admins = get_all_admins()
    return jsonify([{
        'id': a.IDuser,
        'nom': a.nom,
        'adresse': a.adresse,
        'role': a.role,
        'username': a.username,
        'image': a.image,
        'telephone': a.telephone,
        'dateCreated': a.dateCreated,
        'prenom': a.prenom,
        'type_user': a.type_user,
        'password':a.password
    } for a in admins])



# Route pour mettre à jour un enregistrement
@admin_bp.route('/update/<int:admin_id>', methods=['PUT'])
def modify_admin(admin_id):
    """
    Met à jour les informations d'un administrateur.
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
            image:
              type: string
              example: "url_to_new_image"
            prenom:
              type: string
              example: "Jean"
    responses:
      200:
        description: Administrateur mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Administrateur non trouvé
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes reçues pour mettre à jour un admin")
            return jsonify({'message': 'Bad Request'}), 400

        admin = update_admin(
            admin_id,
            nom=data.get('nom'),
            adresse=data.get('adresse'),
            password=data.get('password'),
            role=data.get('role'),
            image=data.get('image'),
            prenom=data.get('prenom')
        )
        if admin:
            logger.info(f"Admin avec l'ID {admin_id} mis à jour")
            return jsonify({'id': admin.IDuser}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un admin: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@admin_bp.route('/delete/<int:admin_id>', methods=['DELETE'])
def remove_admin(admin_id):
    """
    Supprime un administrateur de la base de données.
    ---
    parameters:
      - name: admin_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Administrateur non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_admin(admin_id)
        if success:
            logger.info(f"Admin avec l'ID {admin_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un admin: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour l'inscription
@admin_bp.route('/register', methods=['POST'])
def register():
    """
    Inscrit un nouvel administrateur.
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
            prenom:
              type: string
              example: "Jean"
    responses:
      201:
        description: Administrateur enregistré avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'prenom']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour enregistrer un admin")
            return jsonify({'message': 'Bad Request'}), 400

        new_admin, access_token = create_admin(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data['image'],
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        logger.info(f"Nouvel admin enregistré avec l'ID: {new_admin.IDuser}")
        return jsonify({'message': 'Admin registered successfully', 'access_token': access_token}), 201

    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement d'un admin: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour la connexion
@admin_bp.route('/login', methods=['POST'])
def login():
    """
    Connecte un administrateur.
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

        admin = authenticate_admin(data['username'], data['password'])
        
        if admin:
            access_token = access_token = create_access_token(
            identity=admin.IDuser,
            telephone=admin.telephone,
            username=admin.username,
            adresse=admin.adresse,
            prenom=admin.prenom,
            nom=admin.nom
            )
            logger.info(f"Admin {admin.IDuser} connecté")
            return jsonify(access_token=access_token), 200
        return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Erreur lors de la connexion d'un admin: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour la déconnexion
@admin_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Déconnecte un administrateur.
    ---
    responses:
      200:
        description: Déconnexion réussie
    """
    logger.info(f"Admin déconnecté")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@admin_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Récupère les informations de l'administrateur connecté.
    ---
    responses:
      200:
        description: Détails de l'administrateur connecté
    """
    current_admin_id = get_jwt_identity()
    admin = Admin.query.get(current_admin_id)
    return jsonify({
        'id': admin.IDuser,
        'nom': admin.nom,
        'role': admin.role,
        'username': admin.username
    }), 200