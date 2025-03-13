from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.users.admin_model import Admin
from app.services.users.admin_service import (
    create_admin, get_admin_by_id, get_all_admins,
    update_admin, delete_admin, authenticate_admin
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'admin'
admin_bp = Blueprint('admin', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@admin_bp.route('/add', methods=['POST'])
def add_admin():
    data = request.get_json()
    new_admin  = create_admin(
        nom=data['nom'],
        adresse=data['adresse'],
        password=data['password'],
        role=data['role'],
        username=data['username'],
        image=data['image'],
        telephone=data['telephone'],
        prenom=data['prenom']
    )
    if not new_admin:
        return jsonify({'message': 'Admin creation failed'}), 400

    logger.info(f"Nouvel admin créé avec l'ID: {new_admin.IDuser}")
    return jsonify({'Nouvel admin créé avec l\'ID': new_admin.IDuser }), 201

# Route pour obtenir un enregistrement par ID
@admin_bp.route('/<int:admin_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_admin')
def get_admin(admin_id):
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
# @cache.cached(timeout=60, key_prefix='list_admins')
def list_admins():
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
        'type_user': a.type_user
    } for a in admins])

# Route pour mettre à jour un enregistrement
@admin_bp.route('/update/<int:admin_id>', methods=['PUT'])
def modify_admin(admin_id):
    data = request.get_json()
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

# Route pour supprimer un enregistrement
@admin_bp.route('/delete/<int:admin_id>', methods=['DELETE'])
def remove_admin(admin_id):
    success = delete_admin(admin_id)
    if success:
        logger.info(f"Admin avec l'ID {admin_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404

# Route pour l'inscription
@admin_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_type = data.get('user_type')
    if user_type != 'admin':
        return jsonify({'message': 'Invalid user type'}), 400

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
    if not new_admin:
        return jsonify({'message': 'Admin creation failed'}), 400

    logger.info(f"Nouvel admin enregistré avec l'ID: {new_admin.IDuser}")
    return jsonify({'message': 'Admin registered successfully', 'access_token': access_token}), 201

# Route pour la connexion
@admin_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    admin = authenticate_admin(data['username'], data['password'])
    if admin:
        access_token = create_access_token(identity=admin.IDuser)
        logger.info(f"Admin {admin.IDuser} connecté")
        return jsonify(access_token=access_token), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Route pour la déconnexion
@admin_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    logger.info(f"Admin déconnecté")
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@admin_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_admin_id = get_jwt_identity()
    admin = Admin.query.get(current_admin_id)
    return jsonify({
        'id': admin.IDuser,
        'nom': admin.nom,
        'role': admin.role,
        'username': admin.username
    }), 200
