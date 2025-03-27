from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.reaction.vote_service import (
    create_vote, get_vote_by_id, get_all_votes,
    get_votes_by_citoyen, get_votes_by_signalement,
    delete_vote
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'vote'
vote_bp = Blueprint('vote', __name__)

# Route pour créer un nouvel enregistrement
@vote_bp.route('/add', methods=['POST'])
def add_vote():
    """
    Ajoute un nouveau vote.
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
    responses:
      201:
        description: Vote créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['citoyen_id', 'signalement_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un vote")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_vote = create_vote(
            citoyen_id=data['citoyen_id'],
            signalement_id=data['signalement_id']
        )
        logger.info(f"Nouveau vote créé avec l'ID: {nouveau_vote.IDvote}")
        return jsonify({'id': nouveau_vote.IDvote}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un vote: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@vote_bp.route('/<int:vote_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_vote')
def get_vote(vote_id):
    """
    Récupère un vote spécifique via son ID.
    ---
    parameters:
      - name: vote_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du vote
      404:
        description: Vote non trouvé
    """
    logger.info(f"Récupération du vote avec l'ID: {vote_id}")
    vote = get_vote_by_id(vote_id)
    if vote:
        return jsonify({
            'id': vote.IDvote,
            'dateCreated': vote.dateCreated,
            'citoyen_id': vote.citoyenID,
            'signalement_id': vote.signalementID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@vote_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_votes')
def list_votes():
    """
    Récupère tous les votes enregistrés.
    ---
    responses:
      200:
        description: Liste des votes
    """
    logger.info("Récupération de tous les votes")
    votes = get_all_votes()
    return jsonify([{
        'id': v.IDvote,
        'dateCreated': v.dateCreated,
        'citoyen_id': v.citoyenID,
        'signalement_id': v.signalementID
    } for v in votes])

# Route pour obtenir les enregistrements par citoyen
@vote_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_votes_by_citoyen')
def list_votes_by_citoyen(citoyen_id):
    """
    Récupère tous les votes d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des votes
    """
    logger.info(f"Récupération des votes pour le citoyen avec l'ID: {citoyen_id}")
    votes = get_votes_by_citoyen(citoyen_id)
    return jsonify([{
        'id': v.IDvote,
        'dateCreated': v.dateCreated,
        'signalement_id': v.signalementID
    } for v in votes])

# Route pour obtenir les enregistrements par signalement
@vote_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_votes_by_signalement')
def list_votes_by_signalement(signalement_id):
    """
    Récupère tous les votes liés à un signalement spécifique.
    ---
    parameters:
      - name: signalement_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des votes associés
    """
    logger.info(f"Récupération des votes pour le signalement avec l'ID: {signalement_id}")
    votes = get_votes_by_signalement(signalement_id)
    return jsonify([{
        'id': v.IDvote,
        'dateCreated': v.dateCreated,
        'citoyen_id': v.citoyenID
    } for v in votes])

# Route pour supprimer un enregistrement
@vote_bp.route('/delete/<int:vote_id>', methods=['DELETE'])
def remove_vote(vote_id):
    """
    Supprime un vote de la base de données.
    ---
    parameters:
      - name: vote_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Vote non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_vote(vote_id)
        if success:
            logger.info(f"Vote avec l'ID {vote_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un vote: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
