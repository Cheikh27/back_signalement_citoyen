from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import logging
from app import cache
from app.models.users.citoyen_model import Citoyen
from app.services.users.citoyen_service import (
    create_citoyen, get_citoyen_by_id, get_all_citoyens,
    update_citoyen, delete_citoyen, authenticate_citoyen
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'citoyen'
citoyen_bp = Blueprint('citoyen', __name__)

@citoyen_bp.route('/add', methods=['POST'])
def add_citoyen():
    """
    Ajoute un nouveau citoyen.
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
            prenom:
              type: string
    responses:
      201:
        description: Citoyen créé avec succès
      400:
        description: Données incomplètes pour la création de citoyen
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'telephone', 'prenom']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes pour la création de citoyen")
            return jsonify({'message': 'Bad Request'}), 400

        new_citoyen = create_citoyen(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data.get('image'),
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        
        if not new_citoyen:
            return jsonify({'message': 'Échec de la création du citoyen'}), 400

        logger.info(f"Citoyen créé ID: {new_citoyen.IDuser}")
        return jsonify({'id': new_citoyen.IDuser}), 201

    except Exception as e:
        logger.error(f"Erreur création citoyen: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/<int:citoyen_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_citoyen')
def get_citoyen(citoyen_id):
    """
    Récupère un citoyen spécifique via son ID.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Détails du citoyen
      404:
        description: Citoyen non trouvé
      500:
        description: Erreur interne
    """
    try:
        citoyen = get_citoyen_by_id(citoyen_id)
        if not citoyen:
            return jsonify({'message': 'Non trouvé'}), 404
            
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
        
    except Exception as e:
        logger.error(f"Erreur récupération citoyen {citoyen_id}: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_citoyens')
def list_citoyens():
    """
    Récupère tous les citoyens enregistrés.
    ---
    responses:
      200:
        description: Liste des citoyens
      500:
        description: Erreur interne
    """
    try:
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
        
    except Exception as e:
        logger.error(f"Erreur liste citoyens: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/update/<int:citoyen_id>', methods=['PUT'])
def modify_citoyen(citoyen_id):
    """
    Met à jour les informations d'un citoyen.
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
            prenom:
              type: string
    responses:
      200:
        description: Citoyen mis à jour avec succès
      400:
        description: Données manquantes
      404:
        description: Citoyen non trouvé
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

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
        
        if not citoyen:
            return jsonify({'message': 'Non trouvé'}), 404
            
        return jsonify({'id': citoyen.IDuser}), 200

    except Exception as e:
        logger.error(f"Erreur mise à jour citoyen {citoyen_id}: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/delete/<int:citoyen_id>', methods=['DELETE'])
def remove_citoyen(citoyen_id):
    """
    Supprime un citoyen de la base de données.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
    responses:
      204:
        description: Suppression réussie
      404:
        description: Citoyen non trouvé
      500:
        description: Erreur interne
    """
    try:
        success = delete_citoyen(citoyen_id)
        if not success:
            return jsonify({'message': 'Non trouvé'}), 404
            
        return '', 204
        
    except Exception as e:
        logger.error(f"Erreur suppression citoyen {citoyen_id}: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/register', methods=['POST'])
def register():
    """
    Inscrit un nouveau citoyen.
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
            prenom:
              type: string
    responses:
      201:
        description: Enregistrement réussi
      400:
        description: Champs obligatoires manquants ou type utilisateur invalide
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'adresse', 'password', 'role', 'username', 'telephone', 'prenom']
        if not data or any(field not in data for field in required_fields):
            return jsonify({'message': 'Champs obligatoires manquants'}), 400

        if data.get('user_type') != 'citoyen':
            return jsonify({'message': 'Type utilisateur invalide'}), 400

        new_citoyen, access_token = create_citoyen(
            nom=data['nom'],
            adresse=data['adresse'],
            password=data['password'],
            role=data['role'],
            username=data['username'],
            image=data.get('image'),
            telephone=data['telephone'],
            prenom=data['prenom']
        )
        
        if not new_citoyen:
            return jsonify({'message': 'Échec enregistrement'}), 400
            
        return jsonify({
            'message': 'Enregistrement réussi',
            'access_token': access_token
        }), 201

    except Exception as e:
        logger.error(f"Erreur enregistrement: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/login', methods=['POST'])
def login():
    """
    Connecte un citoyen.
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
        description: Identifiants manquants
      401:
        description: Identifiants invalides
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'message': 'Identifiants manquants'}), 400

        citoyen = authenticate_citoyen(data['username'], data['password'])
        if not citoyen:
            return jsonify({'message': 'Identifiants invalides'}), 401
            
        access_token = create_access_token(identity=citoyen.IDuser)
        return jsonify(access_token=access_token), 200

    except Exception as e:
        logger.error(f"Erreur connexion: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Déconnecte un citoyen.
    ---
    responses:
      200:
        description: Déconnexion réussie
      500:
        description: Erreur interne
    """
    try:
        logger.info("Déconnexion citoyen")
        return jsonify({'message': 'Déconnexion réussie'}), 200
    except Exception as e:
        logger.error(f"Erreur déconnexion: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500

@citoyen_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """
    Récupère les informations du citoyen connecté.
    ---
    responses:
      200:
        description: Détails du citoyen connecté
      404:
        description: Citoyen non trouvé
      500:
        description: Erreur interne
    """
    try:
        current_id = get_jwt_identity()
        citoyen = Citoyen.query.get(current_id)
        if not citoyen:
            return jsonify({'message': 'Non trouvé'}), 404
            
        return jsonify({
            'id': citoyen.IDuser,
            'nom': citoyen.nom,
            'role': citoyen.role,
            'username': citoyen.username
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur route protégée: {str(e)}")
        return jsonify({'message': 'Erreur interne'}), 500