from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.users.user_model import User
from app.services.users.user_service import (
    create_user, get_user_by_id, get_all_users,
    update_user, delete_user, authenticate_user
)

user_bp = Blueprint('user', __name__)

# Route pour créer un nouvel enregistrement
@user_bp.route('/add', methods=['POST'])
def add_user():
    data = request.get_json()
    user_type = data.get('user_type')
    if user_type not in ['admin', 'authorite', 'citoyen', 'moderateur']:
        return jsonify({'message': 'Invalid user type'}), 400

    new_user, access_token = create_user(
        nom=data['nom'],
        adresse=data['adresse'],
        password=data['password'],
        role=data['role'],
        username=data['username'],
        image=data['image'],
        telephone=data['telephone'],
        user_type=user_type,
        **{key: data[key] for key in data if key not in ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'user_type']}
    )
    if not new_user:
        return jsonify({'message': 'User creation failed'}), 400

    return jsonify({'id': new_user.IDuser, 'access_token': access_token}), 201

# Route pour obtenir un enregistrement par ID
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if user:
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
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@user_bp.route('/all', methods=['GET'])
def list_users():
    users = get_all_users()
    return jsonify([{
        'id': u.IDuser,
        'nom': u.nom,
        'adresse': u.adresse,
        'role': u.role,
        'username': u.username,
        'image': u.image,
        'telephone': u.telephone,
        'dateCreated': u.dateCreated,
        'type': u.type_user
    } for u in users])

# Route pour mettre à jour un enregistrement
@user_bp.route('/update/<int:user_id>', methods=['PUT'])
def modify_user(user_id):
    data = request.get_json()
    user = update_user(
        user_id,
        nom=data.get('nom'),
        adresse=data.get('adresse'),
        password=data.get('password'),
        role=data.get('role'),
        username=data.get('username'),
        image=data.get('image'),
        telephone=data.get('telephone'),
        **{key: data[key] for key in data if key not in ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone']}
    )
    if user:
        return jsonify({'id': user.IDuser}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    success = delete_user(user_id)
    if success:
        return '', 204
    return jsonify({'message': 'Not found'}), 404

# Route pour l'inscription
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_type = data.get('user_type')
    if user_type not in ['admin', 'authorite', 'citoyen', 'moderateur']:
        return jsonify({'message': 'Invalid user type'}), 400

    new_user, access_token = create_user(
        nom=data['nom'],
        adresse=data['adresse'],
        password=data['password'],
        role=data['role'],
        username=data['username'],
        image=data['image'],
        telephone=data['telephone'],
        user_type=user_type,
        **{key: data[key] for key in data if key not in ['nom', 'adresse', 'password', 'role', 'username', 'image', 'telephone', 'user_type']}
    )
    if not new_user:
        return jsonify({'message': 'User creation failed'}), 400

    return jsonify({'message': 'User registered successfully', 'access_token': access_token}), 201

# Route pour la connexion
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = authenticate_user(data['username'], data['password'])
    if user:
        access_token = create_access_token(identity=user.IDuser)
        return jsonify(access_token=access_token), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Route pour la déconnexion
@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logout successful'}), 200

# Route protégée
@user_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({
        'id': user.IDuser,
        'nom': user.nom,
        'role': user.role,
        'username': user.username
    }), 200
