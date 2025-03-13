from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.users.moderateur_model import Moderateur
from app.services.users.moderateur_service import (
    create_moderateur, get_moderateur_by_id, get_all_moderateurs,
    update_moderateur, delete_moderateur, authenticate_moderateur
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'moderateur'
moderateur_bp = Blueprint('moderateur', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@moderateur_bp.route('/add', methods=['POST'])
def add_moderateur():
    data = request.get_json()
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
        return jsonify({'message': 'Moderateur creation failed'}), 400

    logger.info(f"Nouvel moderateur créé avec l'ID: {new_moderateur.IDuser}")
    return jsonify({'id': new_moderateur.IDuser }), 201

# Route pour obtenir un enregistrement par ID
@moderateur_bp.route('/<int:moderateur_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_moderateur')
def get_moderateur(moderateur_id):
    logger.info(f"Récupération du moderateur avec l'ID: {moderateur_id}")
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
# @cache.cached(timeout=60, key_prefix='list_moderateurs')
def list_moderateurs():
    logger.info("Récupération de tous les moderateurs")
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
    data = request.get_json()
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
        logger.info(f"Moderateur avec l'ID {moderateur_id} mis à jour")
        return jsonify({'id': moderateur.IDuser}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@moderateur_bp.route('/delete/<int:moderateur_id>', methods=['DELETE'])
def remove_moderateur(moderateur_id):
    success = delete_moderateur(moderateur_id)
    if success:
        logger.info(f"Moderateur avec l'ID {moderateur_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404

# Route pour l'inscription
@moderateur_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
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
        return jsonify({'message': 'Moderateur creation failed'}), 400

    logger.info(f"Nouvel moderateur enregistré avec l'ID: {new_moderateur.IDuser}")
    return jsonify({'message': 'Moderateur registered successfully', 'access_token': access_token}), 201

# Route pour la connexion
@moderateur_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    moderateur = authenticate_moderateur(data['username'], data['password'])
    if moderateur:
        access_token = create_access_token(identity=moderateur.IDuser)
        logger.info(f"Moderateur {moderateur.IDuser} connecté")
        return jsonify(access_token=access_token), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Route pour la déconnexion
@moderateur_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    logger.info(f"Moderateur déconnecté")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@moderateur_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_moderateur_id = get_jwt_identity()
    moderateur = Moderateur.query.get(current_moderateur_id)
    return jsonify({
        'id': moderateur.IDuser,
        'nom': moderateur.nom,
        'role': moderateur.role,
        'username': moderateur.username
    }), 200
