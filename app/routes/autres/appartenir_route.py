from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.autres.appartenir_service import (
    create_appartenir, get_appartenir_by_id, get_all_appartenirs,
    get_appartenirs_by_citoyen, get_appartenirs_by_groupe,
    update_appartenir, delete_appartenir
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'appartenir'
appartenir_bp = Blueprint('appartenir', __name__)

# Route pour créer un nouvel enregistrement
@appartenir_bp.route('/add', methods=['POST'])
def add_appartenir():
    """
    Crée un nouvel enregistrement d'appartenance.
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
            citoyen_id:
              type: integer
              example: 1
            groupe_id:
              type: integer
              example: 1
    responses:
      201:
        description: Enregistrement créé avec succès
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
        if not data or 'citoyen_id' not in data or 'groupe_id' not in data:
            logger.error("Données incomplètes reçues pour créer un enregistrement d'appartenance")
            return jsonify({'message': 'Bad Request'}), 400

        nouvel_appartenir = create_appartenir(
            citoyen_id=data['citoyen_id'],
            groupe_id=data['groupe_id']
        )
        logger.info(f"Nouvel enregistrement d'appartenance créé avec l'ID: {nouvel_appartenir.IDappartenir}")
        return jsonify({'id': nouvel_appartenir.IDappartenir}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un enregistrement d'appartenance: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@appartenir_bp.route('/<int:appartenir_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_appartenir')
def get_appartenir(appartenir_id):
    """
    Récupère un enregistrement d'appartenance par son ID.
    ---
    parameters:
      - name: appartenir_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Enregistrement trouvé
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            dateCreated:
              type: string
              example: "2023-10-01T00:00:00Z"
            citoyen_id:
              type: integer
              example: 1
            groupe_id:
              type: integer
              example: 1
      404:
        description: Enregistrement non trouvé
    """
    logger.info(f"Récupération de l'enregistrement d'appartenance avec l'ID: {appartenir_id}")
    appartenir = get_appartenir_by_id(appartenir_id)
    if appartenir:
        return jsonify({
            'id': appartenir.IDappartenir,
            'dateCreated': appartenir.dateCreated,
            'citoyen_id': appartenir.citoyenID,
            'groupe_id': appartenir.groupeID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@appartenir_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_appartenirs')
def list_appartenirs():
    """
    Récupère tous les enregistrements d'appartenance.
    ---
    responses:
      200:
        description: Liste des enregistrements
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              dateCreated:
                type: string
                example: "2023-10-01T00:00:00Z"
              citoyen_id:
                type: integer
                example: 1
              groupe_id:
                type: integer
                example: 1
    """
    logger.info("Récupération de tous les enregistrements d'appartenance")
    appartenirs = get_all_appartenirs()
    return jsonify([{
        'id': a.IDappartenir,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID,
        'groupe_id': a.groupeID
    } for a in appartenirs])

# Route pour obtenir les enregistrements par citoyen
@appartenir_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_appartenirs_by_citoyen')
def list_appartenirs_by_citoyen(citoyen_id):
    """
    Récupère les enregistrements d'appartenance pour un citoyen donné.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des enregistrements
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              dateCreated:
                type: string
                example: "2023-10-01T00:00:00Z"
              groupe_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des enregistrements d'appartenance pour le citoyen avec l'ID: {citoyen_id}")
    appartenirs = get_appartenirs_by_citoyen(citoyen_id)
    return jsonify([{
        'id': a.IDappartenir,
        'dateCreated': a.dateCreated,
        'groupe_id': a.groupeID
    } for a in appartenirs])

# Route pour obtenir les enregistrements par groupe
@appartenir_bp.route('/<int:groupe_id>/groupes', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_appartenirs_by_groupe')
def list_appartenirs_by_groupe(groupe_id):
    """
    Récupère les enregistrements d'appartenance pour un groupe donné.
    ---
    parameters:
      - name: groupe_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des enregistrements
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              dateCreated:
                type: string
                example: "2023-10-01T00:00:00Z"
              citoyen_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des enregistrements d'appartenance pour le groupe avec l'ID: {groupe_id}")
    appartenirs = get_appartenirs_by_groupe(groupe_id)
    return jsonify([{
        'id': a.IDappartenir,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID
    } for a in appartenirs])

# Route pour mettre à jour un enregistrement
@appartenir_bp.route('/update/<int:appartenir_id>', methods=['PUT'])
def modify_appartenir(appartenir_id):
    """
    Met à jour un enregistrement d'appartenance.
    ---
    consumes:
      - application/json
    parameters:
      - name: appartenir_id
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
            citoyen_id:
              type: integer
              example: 1
            groupe_id:
              type: integer
              example: 1
    responses:
      200:
        description: Enregistrement mis à jour avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
      400:
        description: Données incomplètes
      404:
        description: Enregistrement non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        if not data or ('citoyen_id' not in data and 'groupe_id' not in data):
            logger.error("Données incomplètes reçues pour mettre à jour un enregistrement d'appartenance")
            return jsonify({'message': 'Bad Request'}), 400

        appartenir = update_appartenir(
            appartenir_id,
            citoyen_id=data.get('citoyen_id'),
            groupe_id=data.get('groupe_id')
        )
        if appartenir:
            logger.info(f"Enregistrement d'appartenance avec l'ID {appartenir_id} mis à jour")
            return jsonify({'id': appartenir.IDappartenir}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un enregistrement d'appartenance: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@appartenir_bp.route('/delete/<int:appartenir_id>', methods=['DELETE'])
def remove_appartenir(appartenir_id):
    """
    Supprime un enregistrement d'appartenance.
    ---
    parameters:
      - name: appartenir_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Enregistrement supprimé avec succès
      404:
        description: Enregistrement non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        success = delete_appartenir(appartenir_id)
        if success:
            logger.info(f"Enregistrement d'appartenance avec l'ID {appartenir_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un enregistrement d'appartenance: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
