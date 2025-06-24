from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.reaction.vote_service import (
    create_vote, get_vote_by_id, get_all_votes,
    get_votes_by_citoyen, get_votes_by_signalement,
    delete_vote, update_vote,get_user_vote_for_signalement
)
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'vote'
vote_bp = Blueprint('vote', __name__)

# Route pour créer un nouvel enregistrement

@vote_bp.route('/add', methods=['POST'])
def add_vote():
    """
    Ajoute un nouveau vote avec vérification préalable.
    """
    try:
        data = request.get_json()
        required_fields = ['citoyen_id', 'signalement_id', 'types']

        if not data or any(field not in data for field in required_fields):
            return jsonify({'message': 'Champs requis manquants'}), 400

        citoyen_id = data['citoyen_id']
        signalement_id = data['signalement_id']
        vote_type = data['types']

        # Vérifie si un vote actif existe déjà
        existing_vote = get_user_vote_for_signalement(citoyen_id, signalement_id)

        if existing_vote:
            return jsonify({
                'id': existing_vote.IDvote,
                'message': 'Vote déjà actif (non supprimé)',
                'existing_vote_type': existing_vote.types
            }), 409  # Cas 1 : vote actif déjà existant

        # Crée le vote
        vote, is_new = create_vote(citoyen_id, signalement_id, vote_type)

        if is_new:
            # 🔔 NOTIFICATION: Vote enregistré
            vote_emoji = "👍" if data['types'] == 'positif' else "👎"
            send_notification(
                user_id=data['citoyen_id'],
                title=f"{vote_emoji} Vote enregistré",
                message=f"Votre vote {data['types']} a été pris en compte",
                entity_type='signalement',
                entity_id=data['signalement_id'],
                priority='low',
                category='social'
            )
            
            # 🔥 NOTIFICATION AU CRÉATEUR (si vote positif)
            if data['types'] == 'positif':
                from app.models.signal.signalement_model import Signalement
                signalement = Signalement.query.get(data['signalement_id'])
                
                if signalement and signalement.citoyenID != data['citoyen_id']:
                    send_notification(
                        user_id=signalement.citoyenID,
                        title="👍 Nouveau vote positif !",
                        message="Quelqu'un a voté positivement pour votre signalement",
                        entity_type='signalement',
                        entity_id=data['signalement_id'],
                        priority='normal',
                        category='social'
                    )
                    
        if not is_new:
            return jsonify({
                'id': vote.IDvote,
                'message': 'Vote déjà présent (même supprimé)'
            }), 409  # Cas 2 : vote existe déjà dans la DB (ex : soft-deleted)

        # Nettoyage cache
        try:
            cache.delete(f'check_user_vote::{signalement_id}::{citoyen_id}')
        except:
            pass  # Pas bloquant

        return jsonify({
            'vote_id': vote.IDvote,
            'message': 'Vote créé avec succès'
        }), 201

    except Exception as e:
        logger.error(f"Erreur serveur: {str(e)}")
        return jsonify({'message': 'Erreur interne du serveur'}), 500


@vote_bp.route('/<int:vote_id>', methods=['GET'])
@cache.cached(timeout=0, key_prefix='get_vote')
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
            'signalement_id': vote.signalementID,
            'types': vote.types
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@vote_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=0, key_prefix='list_votes')
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
        'signalement_id': v.signalementID,
        'types': v.types,
        'is_deleted':v.is_deleted
    } for v in votes])

# Route pour obtenir les enregistrements par citoyen
@vote_bp.route('/<int:citoyen_id>/votes', methods=['GET'])
@cache.cached(timeout=0, key_prefix='list_votes_by_citoyen')
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
        'signalement_id': v.signalementID,
        'types': v.types
    } for v in votes])

# Route pour obtenir les enregistrements par signalement
@vote_bp.route('/<int:signalement_id>/votes', methods=['GET'])
@cache.cached(timeout=0, key_prefix='list_votes_by_signalement')
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
        'citoyen_id': v.citoyenID,
        'types': v.types
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

@vote_bp.route('/update/<int:vote_id>', methods=['PUT'])
def modify_vote(vote_id):
    """
    Met à jour une vote existante.
    ---
    consumes:
      - application/json
    parameters:
      - name: vote_id
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
            nb_vote:
              type: integer
              example: 1
    responses:
      200:
        description: vote mise à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: vote non trouvée
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'types' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour une vote")
            return jsonify({'message': 'Bad Request'}), 400
# vote_id, types=None,signalement_id=None,citoyen_id=None
        vote = update_vote(vote_id, types=data.get('types'))
       
        if vote:
            logger.info(f"vote avec l'ID {vote_id} mise à jour")
            return jsonify({'id': vote.IDvote}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'une vote: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500



@vote_bp.route('/check/<int:signalement_id>/<int:citoyen_id>', methods=['GET'])
# @cache.cached(timeout=0, key_prefix='check_user_vote')  # ← PROBLÈME POTENTIEL: CACHE
def check_user_vote(signalement_id, citoyen_id):
    """
    Vérifie si un utilisateur spécifique a voté pour un signalement donné.
    """
    try:
        logger.info(f"Vérification du vote pour signalement {signalement_id} et citoyen {citoyen_id}")
        
        # SOLUTION A: Désactiver le cache temporairement pour tester
        # @cache.cached(timeout=0, key_prefix='check_user_vote')
        
        # SOLUTION B: Forcer une requête fraîche à la base de données
        vote = get_user_vote_for_signalement(citoyen_id, signalement_id)
        
        # AJOUT: Log détaillé pour debug
        logger.info(f"Vote trouvé: {vote}")
        if vote:
            logger.info(f"Vote détails: ID={vote.IDvote}, type={vote.types}, is_deleted={vote.is_deleted}")
        
        if vote and not vote.is_deleted:
            logger.info(f"Vote actif trouvé: {vote.types}")
            return jsonify({
                'has_voted': True,
                'vote_type': vote.types,
                'vote_id': vote.IDvote
            }), 200
        else:
            logger.info("Aucun vote actif trouvé")
            return jsonify({
                'has_voted': False,
                'vote_type': None,
                'vote_id': None
            }), 200
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du vote: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

