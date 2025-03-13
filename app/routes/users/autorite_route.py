from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.users.autorite_model import Authorite
from app.services.users.autorite_service import (
    create_authorite, get_authorite_by_id, get_all_authorites,
    update_authorite, delete_authorite, authenticate_authorite
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'autorite'
autorite_bp = Blueprint('autorite', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@autorite_bp.route('/add', methods=['POST'])
def add_authorite():
    data = request.get_json()
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
    
    return jsonify({'message':'autorite creer avec succes'}), 201

# Route pour obtenir un enregistrement par ID
@autorite_bp.route('/<int:authorite_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_authorite')
def get_authorite(authorite_id):
    logger.info(f"Récupération de l'autorite avec l'ID: {authorite_id}")
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
            # 'typeAuthorite': authorite.typeAuthorite,
            'description': authorite.description,
            'dateCreated': authorite.dateCreated,
            'type_user': authorite.type_user
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@autorite_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_authorites')
def list_authorites():
    logger.info("Récupération de tous les autorites")
    authorites = get_all_authorites()
    return jsonify([{
        'id': a.IDuser,
        'nom': a.nom,
        'adresse': a.adresse,
        'role': a.role,
        'username': a.username,
        'image': a.image,
        'telephone': a.telephone,
        # 'typeAuthorite': a.typeAuthorite,
        'description': a.description,
        'dateCreated': a.dateCreated,
        'type_user': a.type_user
    } for a in authorites])

# Route pour mettre à jour un enregistrement
@autorite_bp.route('/update/<int:authorite_id>', methods=['PUT'])
def modify_authorite(authorite_id):
    data = request.get_json()
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
        logger.info(f"Autorite avec l'ID {authorite_id} mis à jour")
        return jsonify({'id': authorite.IDuser}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@autorite_bp.route('/delete/<int:authorite_id>', methods=['DELETE'])
def remove_authorite(authorite_id):
    success = delete_authorite(authorite_id)
    if success:
        logger.info(f"Autorite avec l'ID {authorite_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404

# Route pour l'inscription
@autorite_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
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

    logger.info(f"Nouvel autorite enregistré avec l'ID: {new_authorite.IDuser}")
    return jsonify({'message': 'Authorite registered successfully', 'access_token': access_token}), 201

# Route pour la connexion
@autorite_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    authorite = authenticate_authorite(data['username'], data['password'])
    if authorite:
        access_token = create_access_token(identity=authorite.IDuser)
        logger.info(f"Autorite {authorite.IDuser} connecté")
        return jsonify(access_token=access_token), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Route pour la déconnexion
@autorite_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    logger.info(f"Autorite déconnecté")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@autorite_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_authorite_id = get_jwt_identity()
    authorite = Authorite.query.get(current_authorite_id)
    return jsonify({
        'id': authorite.IDuser,
        'nom': authorite.nom,
        'role': authorite.role,
        'username': authorite.username
    }), 200
