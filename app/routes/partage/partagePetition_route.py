from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.partage.partagePetition_service import (
    create_partager_petition, get_partager_petition_by_id, get_all_partager_petitions,
    get_partager_petitions_by_citoyen, get_partager_petitions_by_petition,
    update_partager_petition, delete_partager_petition
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'partager_petition'
partager_petition_bp = Blueprint('partager_petition', __name__)

# Route pour créer un nouvel enregistrement
@partager_petition_bp.route('/add', methods=['POST'])
def add_partager_petition():
    """
    Crée un nouveau partage de pétition.
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
            petition_id:
              type: integer
              example: 1
            nb_partage:
              type: integer
              example: 0
    responses:
      201:
        description: Partage de pétition créé avec succès
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
        required_fields = ['citoyen_id', 'petition_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un partage de pétition")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_partage = create_partager_petition(
            citoyen_id=data['citoyen_id'],
            petition_id=data['petition_id'],
            nb_partage=data.get('nb_partage', 0)
        )
        logger.info(f"Nouveau partage de pétition créé avec l'ID: {nouveau_partage.IDpartager}")
        return jsonify({'id': nouveau_partage.IDpartager}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un partage de pétition: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@partager_petition_bp.route('/<int:partager_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_partager_petition')
def get_partager_petition(partager_id):
    """
    Récupère un partage de pétition par son ID.
    ---
    parameters:
      - name: partager_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Partage de pétition trouvé
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            dateCreated:
              type: string
              example: "2023-10-01T00:00:00Z"
            nbPartage:
              type: integer
              example: 1
            citoyen_id:
              type: integer
              example: 1
            petition_id:
              type: integer
              example: 1
      404:
        description: Partage de pétition non trouvé
    """
    logger.info(f"Récupération du partage de pétition avec l'ID: {partager_id}")
    partager = get_partager_petition_by_id(partager_id)
    if partager:
        return jsonify({
            'id': partager.IDpartager,
            'dateCreated': partager.dateCreated,
            'nbPartage': partager.nbPartage,
            'citoyen_id': partager.citoyenID,
            'petition_id': partager.petitionID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@partager_petition_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_petitions')
def list_partager_petitions():
    """
    Récupère tous les partages de pétition.
    ---
    responses:
      200:
        description: Liste des partages de pétition
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
              nbPartage:
                type: integer
                example: 1
              citoyen_id:
                type: integer
                example: 1
              petition_id:
                type: integer
                example: 1
    """
    logger.info("Récupération de tous les partages de pétition")
    partager_petitions = get_all_partager_petitions()
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID,
        'petition_id': p.petitionID
    } for p in partager_petitions])

# Route pour obtenir les enregistrements par citoyen
@partager_petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_petitions_by_citoyen')
def list_partager_petitions_by_citoyen(citoyen_id):
    """
    Récupère les partages de pétition pour un citoyen donné.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des partages de pétition
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
              nbPartage:
                type: integer
                example: 1
              petition_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des partages de pétition pour le citoyen avec l'ID: {citoyen_id}")
    partager_petitions = get_partager_petitions_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'petition_id': p.petitionID
    } for p in partager_petitions])

# Route pour obtenir les enregistrements par pétition
@partager_petition_bp.route('/<int:petition_id>/petitions', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_petitions_by_petition')
def list_partager_petitions_by_petition(petition_id):
    """
    Récupère les partages de pétition pour une pétition donnée.
    ---
    parameters:
      - name: petition_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des partages de pétition
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
              nbPartage:
                type: integer
                example: 1
              citoyen_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des partages de pétition pour la pétition avec l'ID: {petition_id}")
    partager_petitions = get_partager_petitions_by_petition(petition_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID
    } for p in partager_petitions])

# Route pour mettre à jour un enregistrement
@partager_petition_bp.route('/update/<int:partager_id>', methods=['PUT'])
def modify_partager_petition(partager_id):
    """
    Met à jour un partage de pétition.
    ---
    consumes:
      - application/json
    parameters:
      - name: partager_id
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
            nb_partage:
              type: integer
              example: 1
    responses:
      200:
        description: Partage de pétition mis à jour avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
      400:
        description: Données incomplètes
      404:
        description: Partage de pétition non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        if not data or 'nb_partage' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour un partage de pétition")
            return jsonify({'message': 'Bad Request'}), 400

        partager = update_partager_petition(partager_id, nb_partage=data['nb_partage'])
        if partager:
            logger.info(f"Partage de pétition avec l'ID {partager_id} mis à jour")
            return jsonify({'id': partager.IDpartager}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un partage de pétition: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@partager_petition_bp.route('/delete/<int:partager_id>', methods=['DELETE'])
def remove_partager_petition(partager_id):
    """
    Supprime un partage de pétition.
    ---
    parameters:
      - name: partager_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Partage de pétition supprimé avec succès
      404:
        description: Partage de pétition non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        success = delete_partager_petition(partager_id)
        if success:
            logger.info(f"Partage de pétition avec l'ID {partager_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un partage de pétition: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
