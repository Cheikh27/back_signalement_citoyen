from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.users.citoyen_model import Citoyen
from app.services.users.citoyen_service import (
    create_citoyen, get_citoyen_by_id, get_all_citoyens,
    update_citoyen, delete_citoyen, authenticate_citoyen
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'citoyen'
citoyen_bp = Blueprint('citoyen', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@citoyen_bp.route('/add', methods=['POST'])
def add_citoyen():
    data = request.get_json()
    # user_type = data.get('user_type')
    # if user_type != 'citoyen':
    #     return jsonify({'message': 'Invalid user type'}), 400

    new_citoyen = create_citoyen(
        nom=data['nom'],
        adresse=data['adresse'],
        password=data['password'],
        role=data['role'],
        username=data['username'],
        image=data['image'],
        telephone=data['telephone'],
        prenom=data['prenom']
    )
    if not new_citoyen:
        return jsonify({'message': 'Citoyen creation failed'}), 400

    logger.info(f"Nouvel citoyen créé avec l'ID: {new_citoyen.IDuser}")
    return jsonify({'id': new_citoyen.IDuser}), 201

# Route pour obtenir un enregistrement par ID
@citoyen_bp.route('/<int:citoyen_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_citoyen')
def get_citoyen(citoyen_id):
    logger.info(f"Récupération du citoyen avec l'ID: {citoyen_id}")
    citoyen = get_citoyen_by_id(citoyen_id)
    if citoyen:
        return jsonify({
            'id': citoyen.IDuser,
            'nom': citoyen.nom,
            'adresse': citoyen.adresse,
            'role': citoyen.role,
            'username': citoyen.username,
            'image': citoyen.image,
            'telephone': citoyen.telephone,
            'prenom': citoyen.prenom,
            'dateCreated': citoyen.dateCreated,
            'type_user': citoyen.type_user
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@citoyen_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_citoyens')
def list_citoyens():
    logger.info("Récupération de tous les citoyens")
    citoyens = get_all_citoyens()
    return jsonify([{
        'id': c.IDuser,
        'nom': c.nom,
        'adresse': c.adresse,
        'role': c.role,
        'username': c.username,
        'image': c.image,
        'telephone': c.telephone,
        'prenom': c.prenom,
        'dateCreated': c.dateCreated,
        'type_user': c.type_user
    } for c in citoyens])

# Route pour mettre à jour un enregistrement
@citoyen_bp.route('/update/<int:citoyen_id>', methods=['PUT'])
def modify_citoyen(citoyen_id):
    data = request.get_json()
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
    if citoyen:
        logger.info(f"Citoyen avec l'ID {citoyen_id} mis à jour")
        return jsonify({'id': citoyen.IDuser}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@citoyen_bp.route('/delete/<int:citoyen_id>', methods=['DELETE'])
def remove_citoyen(citoyen_id):
    success = delete_citoyen(citoyen_id)
    if success:
        logger.info(f"Citoyen avec l'ID {citoyen_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404

# Route pour l'inscription
@citoyen_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_type = data.get('user_type')
    if user_type != 'citoyen':
        return jsonify({'message': 'Invalid user type'}), 400

    new_citoyen, access_token = create_citoyen(
        nom=data['nom'],
        adresse=data['adresse'],
        password=data['password'],
        role=data['role'],
        username=data['username'],
        image=data['image'],
        telephone=data['telephone'],
        prenom=data['prenom']
    )
    if not new_citoyen:
        return jsonify({'message': 'Citoyen creation failed'}), 400

    logger.info(f"Nouvel citoyen enregistré avec l'ID: {new_citoyen.IDuser}")
    return jsonify({'message': 'Citoyen registered successfully', 'access_token': access_token}), 201

# Route pour la connexion
@citoyen_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    citoyen = authenticate_citoyen(data['username'], data['password'])
    if citoyen:
        access_token = create_access_token(identity=citoyen.IDuser)
        logger.info(f"Citoyen {citoyen.IDuser} connecté")
        return jsonify(access_token=access_token), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Route pour la déconnexion
@citoyen_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    logger.info(f"Citoyen déconnecté")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@citoyen_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_citoyen_id = get_jwt_identity()
    citoyen = Citoyen.query.get(current_citoyen_id)
    return jsonify({
        'id': citoyen.IDuser,
        'nom': citoyen.nom,
        'role': citoyen.role,
        'username': citoyen.username
    }), 200
