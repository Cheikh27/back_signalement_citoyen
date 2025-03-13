from flask import Blueprint, request, jsonify, current_app
from app.services.reaction.vote_service import (
    create_vote, get_vote_by_id, get_all_votes,
    get_votes_by_citoyen, get_votes_by_signalement,
    delete_vote
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'vote'
vote_bp = Blueprint('vote', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@vote_bp.route('/add', methods=['POST'])
def add_vote():
    data = request.get_json()
    nouveau_vote = create_vote(
        citoyen_id=data['citoyen_id'],
        signalement_id=data['signalement_id']
    )
    logger.info(f"Nouveau vote créé avec l'ID: {nouveau_vote.IDvote}")
    return jsonify({'id': nouveau_vote.IDvote}), 201

# Route pour obtenir un enregistrement par ID
@vote_bp.route('/<int:vote_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_vote')
def get_vote(vote_id):
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
# @cache.cached(timeout=60, key_prefix='list_votes')
def list_votes():
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
# @cache.cached(timeout=60, key_prefix='list_votes_by_citoyen')
def list_votes_by_citoyen(citoyen_id):
    logger.info(f"Récupération des votes pour le citoyen avec l'ID: {citoyen_id}")
    votes = get_votes_by_citoyen(citoyen_id)
    return jsonify([{
        'id': v.IDvote,
        'dateCreated': v.dateCreated,
        'signalement_id': v.signalementID
    } for v in votes])

# Route pour obtenir les enregistrements par signalement
@vote_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_votes_by_signalement')
def list_votes_by_signalement(signalement_id):
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
    success = delete_vote(vote_id)
    if success:
        logger.info(f"Vote avec l'ID {vote_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
