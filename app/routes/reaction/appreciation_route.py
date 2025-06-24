from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.reaction.appreciation_service import (
    create_appreciation, get_appreciation_by_id, get_all_appreciations,
    get_appreciations_by_citoyen, get_appreciations_by_publication,
    delete_appreciation
)
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users


# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'appreciation'
appreciation_bp = Blueprint('appreciation', __name__)

# Route pour créer un nouvel enregistrement
@appreciation_bp.route('/add', methods=['POST'])
def add_appreciation():
    """
    Ajoute une nouvelle appréciation.
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
            publication_id:
              type: integer
              example: 1
    responses:
      201:
        description: Appréciation créée avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['citoyen_id', 'publication_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer une appréciation")
            return jsonify({'message': 'Bad Request'}), 400

        nouvelle_appreciation = create_appreciation(
            citoyen_id=data['citoyen_id'],
            publication_id=data['publication_id']
        )
        logger.info(f"Nouvelle appréciation créée avec l'ID: {nouvelle_appreciation.IDappreciation}")
        # 🔔 SYSTÈME DE NOTIFICATIONS
        try:
            # 1. Notification pour l'auteur de l'appréciation
            send_notification(
                user_id=data['citoyen_id'],
                title="👏 Appréciation enregistrée",
                message="Votre appréciation a été enregistrée avec succès",
                entity_type='publication',
                entity_id=data['publication_id'],
                priority='low',
                category='social'
            )
            
            # 2. Notification pour l'autorité qui a publié
            from app.models.signal.publication_model import Publication
            publication = Publication.query.get(data['publication_id'])
            
            if publication and publication.autoriteID != data['citoyen_id']:
                send_notification(
                    user_id=publication.autoriteID,
                    title="👏 Nouvelle appréciation !",
                    message="Un citoyen a apprécié votre publication officielle",
                    entity_type='publication',
                    entity_id=data['publication_id'],
                    priority='normal',
                    category='social'
                )
                
        except Exception as notif_error:
            logger.warning(f"Erreur notifications appréciation: {notif_error}")
        return jsonify({'id': nouvelle_appreciation.IDappreciation}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'une appréciation: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@appreciation_bp.route('/<int:appreciation_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_appreciation')
def get_appreciation(appreciation_id):
    """
    Récupère une appréciation spécifique via son ID.
    ---
    parameters:
      - name: appreciation_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails de l'appréciation
      404:
        description: Appréciation non trouvée
    """
    logger.info(f"Récupération de l'appréciation avec l'ID: {appreciation_id}")
    appreciation = get_appreciation_by_id(appreciation_id)
    if appreciation:
        return jsonify({
            'id': appreciation.IDappreciation,
            'dateCreated': appreciation.dateCreated,
            'citoyen_id': appreciation.citoyenID,
            'publication_id': appreciation.PublicationID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@appreciation_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_appreciations')
def list_appreciations():
    """
    Récupère toutes les appréciations enregistrées.
    ---
    responses:
      200:
        description: Liste des appréciations
    """
    logger.info("Récupération de toutes les appréciations")
    appreciations = get_all_appreciations()
    return jsonify([{
        'id': a.IDappreciation,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID,
        'publication_id': a.PublicationID
    } for a in appreciations])

# Route pour obtenir les enregistrements par citoyen
@appreciation_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_appreciations_by_citoyen')
def list_appreciations_by_citoyen(citoyen_id):
    """
    Récupère toutes les appréciations d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des appréciations
    """
    logger.info(f"Récupération des appréciations pour le citoyen avec l'ID: {citoyen_id}")
    appreciations = get_appreciations_by_citoyen(citoyen_id)
    return jsonify([{
        'id': a.IDappreciation,
        'dateCreated': a.dateCreated,
        'publication_id': a.PublicationID
    } for a in appreciations])

# Route pour obtenir les enregistrements par publication
@appreciation_bp.route('/<int:publication_id>/publications', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_appreciations_by_publication')
def list_appreciations_by_publication(publication_id):
    """
    Récupère toutes les appréciations liées à une publication spécifique.
    ---
    parameters:
      - name: publication_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des appréciations associées
    """
    logger.info(f"Récupération des appréciations pour la publication avec l'ID: {publication_id}")
    appreciations = get_appreciations_by_publication(publication_id)
    return jsonify([{
        'id': a.IDappreciation,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID
    } for a in appreciations])

# Route pour supprimer un enregistrement
@appreciation_bp.route('/delete/<int:appreciation_id>', methods=['DELETE'])
def remove_appreciation(appreciation_id):
    """
    Supprime une appréciation de la base de données.
    ---
    parameters:
      - name: appreciation_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Appréciation non trouvée
      500:
        description: Erreur serveur
    """
    try:
        success = delete_appreciation(appreciation_id)
        if success:
            logger.info(f"Appréciation avec l'ID {appreciation_id} supprimée")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'une appréciation: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
