from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.partage.partageSignalement_service import (
    create_partager_signalement, get_partager_signalement_by_id, get_all_partager_signalements,
    get_partager_signalements_by_citoyen, get_partager_signalements_by_signalement,
    update_partager_signalement, delete_partager_signalement
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'partager_signalement'
partager_signalement_bp = Blueprint('partager_signalement', __name__)

# Route pour créer un nouvel enregistrement
@partager_signalement_bp.route('/add', methods=['POST'])
def add_partager_signalement():
    """
    Ajoute un nouveau partage de signalement.
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
            signalement_id:
              type: integer
              example: 1
            nb_partage:
              type: integer
              example: 0
    responses:
      201:
        description: Partage de signalement créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['citoyen_id', 'signalement_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un partage de signalement")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_partage = create_partager_signalement(
            citoyen_id=data['citoyen_id'],
            signalement_id=data['signalement_id'],
            nb_partage=data.get('nb_partage', 0)
        )
        logger.info(f"Nouveau partage de signalement créé avec l'ID: {nouveau_partage.IDpartager}")
        return jsonify({'id': nouveau_partage.IDpartager}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un partage de signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@partager_signalement_bp.route('/<int:partager_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_partager_signalement')
def get_partager_signalement(partager_id):
    """
    Récupère un partage de signalement spécifique via son ID.
    ---
    parameters:
      - name: partager_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du partage de signalement
      404:
        description: Partage de signalement non trouvé
    """
    logger.info(f"Récupération du partage de signalement avec l'ID: {partager_id}")
    partager = get_partager_signalement_by_id(partager_id)
    if partager:
        return jsonify({
            'id': partager.IDpartager,
            'dateCreated': partager.dateCreated,
            'nbPartage': partager.nbPartage,
            'citoyen_id': partager.citoyenID,
            'signalement_id': partager.SignalementID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les partages de signalement
@partager_signalement_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_signalements')
def list_partager_signalements():
    """
    Récupère tous les partages de signalement enregistrés.
    ---
    responses:
      200:
        description: Liste des partages de signalement
    """
    logger.info("Récupération de tous les partages de signalement")
    partager_signalements = get_all_partager_signalements()
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID,
        'signalement_id': p.SignalementID
    } for p in partager_signalements])

# Route pour obtenir les partages de signalement d'un citoyen
@partager_signalement_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_signalements_by_citoyen')
def list_partager_signalements_by_citoyen(citoyen_id):
    """
    Récupère tous les partages de signalement d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des partages de signalement
    """
    logger.info(f"Récupération des partages de signalement pour le citoyen avec l'ID: {citoyen_id}")
    partager_signalements = get_partager_signalements_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'signalement_id': p.SignalementID
    } for p in partager_signalements])

# Route pour obtenir les partages de signalement d'un signalement
@partager_signalement_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_signalements_by_signalement')
def list_partager_signalements_by_signalement(signalement_id):
    """
    Récupère tous les partages de signalement liés à un signalement spécifique.
    ---
    parameters:
      - name: signalement_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des partages de signalement associés
    """
    logger.info(f"Récupération des partages de signalement pour le signalement avec l'ID: {signalement_id}")
    partager_signalements = get_partager_signalements_by_signalement(signalement_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID
    } for p in partager_signalements])

# Route pour mettre à jour un partage de signalement
@partager_signalement_bp.route('/update/<int:partager_id>', methods=['PUT'])
def modify_partager_signalement(partager_id):
    """
    Met à jour un partage de signalement existant.
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
        description: Partage de signalement mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Partage de signalement non trouvé
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'nb_partage' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour un partage de signalement")
            return jsonify({'message': 'Bad Request'}), 400

        partager = update_partager_signalement(partager_id, nb_partage=data['nb_partage'])
        if partager:
            logger.info(f"Partage de signalement avec l'ID {partager_id} mis à jour")
            return jsonify({'id': partager.IDpartager}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un partage de signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un partage de signalement
@partager_signalement_bp.route('/delete/<int:partager_id>', methods=['DELETE'])
def remove_partager_signalement(partager_id):
    """
    Supprime un partage de signalement de la base de données.
    ---
    parameters:
      - name: partager_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Partage de signalement non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_partager_signalement(partager_id)
        if success:
            logger.info(f"Partage de signalement avec l'ID {partager_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un partage de signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
