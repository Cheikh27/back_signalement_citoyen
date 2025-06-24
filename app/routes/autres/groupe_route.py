from flask import Blueprint, request, jsonify # type: ignore
import logging
from app import cache
from app.services.autres.groupe_service import (
    create_groupe, get_groupe_by_id, get_all_groupes,
    update_groupe, delete_groupe
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'groupe'
groupe_bp = Blueprint('groupe', __name__)

# Route pour créer un nouvel enregistrement
@groupe_bp.route('/add', methods=['POST'])
def add_groupe():
    """
    Crée un nouveau groupe.
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
              example: "Nouveau Groupe"
            description:
              type: string
              example: "Description du groupe"
            image:
              type: string
              example: "http://example.com/image.png"
            admin:
              type: integer
              example: 1
    responses:
      201:
        description: Groupe créé avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
      400:
        description: Données incomplètes
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        required_fields = ['nom', 'description', 'image', 'admin']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un groupe")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_groupe = create_groupe(
            nom=data['nom'],
            description=data['description'],
            image=data['image'],
            admin=data['admin']
        )
        logger.info(f"Nouveau groupe créé avec l'ID: {nouveau_groupe.IDgroupe}")
        return jsonify({'id': nouveau_groupe.IDgroupe}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un groupe: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@groupe_bp.route('/<int:groupe_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_groupe')
def get_groupe(groupe_id):
    """
    Récupère un groupe par son ID.
    ---
    parameters:
      - name: groupe_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Groupe trouvé
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            nom:
              type: string
              example: "Nouveau Groupe"
            description:
              type: string
              example: "Description du groupe"
            image:
              type: string
              example: "http://example.com/image.png"
            admin:
              type: integer
              example: 1
            dateCreated:
              type: string
              example: "2023-10-01T00:00:00Z"
      404:
        description: Groupe non trouvé
    """
    logger.info(f"Récupération du groupe avec l'ID: {groupe_id}")
    groupe = get_groupe_by_id(groupe_id)
    if groupe:
        return jsonify({
            'id': groupe.IDgroupe,
            'nom': groupe.nom,
            'description': groupe.description,
            'image': groupe.image,
            'admin': groupe.admin,
            'dateCreated': groupe.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@groupe_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_groupes')
def list_groupes():
    """
    Récupère tous les groupes.
    ---
    responses:
      200:
        description: Liste des groupes
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              nom:
                type: string
                example: "Nouveau Groupe"
              description:
                type: string
                example: "Description du groupe"
              image:
                type: string
                example: "http://example.com/image.png"
              admin:
                type: integer
                example: 1
              dateCreated:
                type: string
                example: "2023-10-01T00:00:00Z"
    """
    logger.info("Récupération de tous les groupes")
    groupes = get_all_groupes()
    return jsonify([{
        'id': g.IDgroupe,
        'nom': g.nom,
        'description': g.description,
        'image': g.image,
        'admin': g.admin,
        'dateCreated': g.dateCreated
    } for g in groupes])

# Route pour mettre à jour un enregistrement
@groupe_bp.route('/update/<int:groupe_id>', methods=['PUT'])
def modify_groupe(groupe_id):
    """
    Met à jour un groupe.
    ---
    consumes:
      - application/json
    parameters:
      - name: groupe_id
        in: path
        required: true
        type: integer
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Nouveau Groupe"
            description:
              type: string
              example: "Description du groupe"
            statut:
              type: string
              example: "actif"
            image:
              type: string
              example: "http://example.com/image.png"
            admin:
              type: integer
              example: 1
    responses:
      200:
        description: Groupe mis à jour avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
      400:
        description: Données incomplètes
      404:
        description: Groupe non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes reçues pour mettre à jour un groupe")
            return jsonify({'message': 'Bad Request'}), 400

        groupe = update_groupe(
            groupe_id,
            nom=data.get('nom'),
            description=data.get('description'),
            statut=data.get('statut'),
            image=data.get('image'),
            admin=data.get('admin')
        )
        if groupe:
            logger.info(f"Groupe avec l'ID {groupe_id} mis à jour")
            return jsonify({'id': groupe.IDgroupe}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un groupe: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@groupe_bp.route('/delete/<int:groupe_id>', methods=['DELETE'])
def remove_groupe(groupe_id):
    """
    Supprime un groupe.
    ---
    parameters:
      - name: groupe_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Groupe supprimé avec succès
      404:
        description: Groupe non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        success = delete_groupe(groupe_id)
        if success:
            logger.info(f"Groupe avec l'ID {groupe_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un groupe: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
