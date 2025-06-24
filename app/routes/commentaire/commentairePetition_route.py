from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.commentaire.commentairePetition_service import (
    create_commentaire, get_commentaire_by_id, get_all_commentaires,
    get_commentaires_by_citoyen, get_commentaires_by_petition,
    update_commentaire, delete_commentaire
)
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'commentaire'
commentaire_petition_bp = Blueprint('commentaire', __name__)

# Route pour créer un nouvel enregistrement
@commentaire_petition_bp.route('/add', methods=['POST'])
def add_commentaire():
    """
    Ajoute un nouveau commentaire à une pétition.
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
            description:
              type: string
              example: "Ceci est un commentaire."
            citoyen_id:
              type: integer
              example: 1
            petition_id:
              type: integer
              example: 1
    responses:
      201:
        description: Commentaire créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['description', 'citoyen_id', 'petition_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un commentaire")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_commentaire = create_commentaire(
            description=data['description'],
            citoyen_id=data['citoyen_id'],
            petition_id=data['petition_id']
        )

        logger.info(f"Nouveau commentaire créé avec l'ID: {nouveau_commentaire.IDcommentaire}")

        try:
            # 1. Notification pour l'auteur du commentaire
            send_notification(
                user_id=data['citoyen_id'],
                title="💬 Commentaire publié",
                message="Votre commentaire sur la pétition a été publié avec succès",
                data={
                    'comment_id': nouveau_commentaire.IDcommentaire,
                    'comment_preview': data['description'][:100] + "..." if len(data['description']) > 100 else data['description'],
                    'action': 'comment_created'
                },
                entity_type='petition',
                entity_id=data['petition_id'],
                priority='low',
                category='social'
            )
            
            # 2. Notification pour le créateur de la pétition
            from app.models.signal.petition_model import Petition
            petition = Petition.query.get(data['petition_id'])
            
            if petition and petition.citoyenID != data['citoyen_id']:  # Ne pas se notifier soi-même
                send_notification(
                    user_id=petition.citoyenID,
                    title="💬 Nouveau commentaire sur votre pétition",
                    message=f"Quelqu'un a commenté votre pétition: '{data['description'][:50]}...'",
                    data={
                        'comment_id': nouveau_commentaire.IDcommentaire,
                        'commenter_id': data['citoyen_id'],
                        'petition_title': petition.titre[:50] + "..." if len(petition.titre) > 50 else petition.titre,
                        'comment_preview': data['description'][:100] + "..." if len(data['description']) > 100 else data['description'],
                        'action': 'comment_received'
                    },
                    entity_type='petition',
                    entity_id=data['petition_id'],
                    priority='normal',
                    category='social'
                )
                
                logger.info(f"Notification envoyée au créateur de la pétition {petition.citoyenID}")
            
            # 3. Notifier les autres commentateurs de cette pétition (engagement communautaire)
            try:
                from app.models.commentaire.commentairePetition_model import CommentairePetition
                
                # Récupérer les IDs des autres commentateurs (actifs dans les 30 derniers jours)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                other_commenters = CommentairePetition.query.filter(
                    CommentairePetition.petitionID == data['petition_id'],
                    CommentairePetition.citoyenID != data['citoyen_id'],  # Pas l'auteur actuel
                    CommentairePetition.citoyenID != (petition.citoyenID if petition else None),  # Pas le créateur (déjà notifié)
                    CommentairePetition.dateCreated >= thirty_days_ago
                ).distinct(CommentairePetition.citoyenID).all()
                
                if other_commenters:
                    commenter_ids = list(set([c.citoyenID for c in other_commenters]))  # Dédupliquer
                    
                    if commenter_ids:
                        send_to_multiple_users(
                            user_ids=commenter_ids,
                            title="💭 Nouveau commentaire",
                            message=f"Un nouveau commentaire a été ajouté à une pétition que vous suivez",
                            data={
                                'comment_id': nouveau_commentaire.IDcommentaire,
                                'petition_id': data['petition_id'],
                                'petition_title': petition.titre[:50] + "..." if petition and len(petition.titre) > 50 else (petition.titre if petition else ""),
                                'action': 'community_comment'
                            },
                            entity_type='petition',
                            entity_id=data['petition_id'],
                            priority='low',
                            category='social'
                        )
                        
                        logger.info(f"Notification envoyée à {len(commenter_ids)} autres commentateurs")
                
            except Exception as community_notif_error:
                logger.warning(f"Erreur notifications communautaires: {community_notif_error}")
                # Ne pas faire échouer l'opération principale
                
        except Exception as notif_error:
            logger.warning(f"Erreur système notifications commentaire pétition: {notif_error}")
            # Les notifications ne doivent jamais faire échouer l'opération principale
        
        return jsonify({
            'id': nouveau_commentaire.IDcommentaire,
            'message': 'Commentaire créé avec succès'
        }), 201
    
        return jsonify({'id': nouveau_commentaire.IDcommentaire}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un commentaire: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@commentaire_petition_bp.route('/<int:commentaire_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_commentaire')
def get_commentaire(commentaire_id):
    """
    Récupère un commentaire spécifique via son ID.
    ---
    parameters:
      - name: commentaire_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du commentaire
      404:
        description: Commentaire non trouvé
    """
    logger.info(f"Récupération du commentaire avec l'ID: {commentaire_id}")
    commentaire = get_commentaire_by_id(commentaire_id)
    if commentaire:
        return jsonify({
            'id': commentaire.IDcommentaire,
            'description': commentaire.description,
            'citoyen_id': commentaire.citoyenID,
            'petition_id': commentaire.petitionID,
            'dateCreated': commentaire.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les commentaires
@commentaire_petition_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires')
def list_commentaires():
    """
    Récupère tous les commentaires enregistrés.
    ---
    responses:
      200:
        description: Liste des commentaires
    """
    logger.info("Récupération de tous les commentaires")
    commentaires = get_all_commentaires()
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'petition_id': c.petitionID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les commentaires d'un citoyen
@commentaire_petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_by_citoyen')
def list_commentaires_by_citoyen(citoyen_id):
    """
    Récupère tous les commentaires d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des commentaires
    """
    logger.info(f"Récupération des commentaires pour le citoyen avec l'ID: {citoyen_id}")
    commentaires = get_commentaires_by_citoyen(citoyen_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'petition_id': c.petitionID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les commentaires d'une pétition
@commentaire_petition_bp.route('/<int:petition_id>/commentaires', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_by_petition')
def list_commentaires_by_petition(petition_id):
    """
    Récupère tous les commentaires liés à une pétition spécifique.
    ---
    parameters:
      - name: petition_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des commentaires associés
    """
    logger.info(f"Récupération des commentaires pour la pétition avec l'ID: {petition_id}")
    commentaires = get_commentaires_by_petition(petition_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour mettre à jour un commentaire
@commentaire_petition_bp.route('/update/<int:commentaire_id>', methods=['PUT'])
def modify_commentaire(commentaire_id):
    """
    Met à jour un commentaire existant.
    ---
    consumes:
      - application/json
    parameters:
      - name: commentaire_id
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
            description:
              type: string
              example: "Nouveau contenu du commentaire."
    responses:
      200:
        description: Commentaire mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Commentaire non trouvé
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour un commentaire")
            return jsonify({'message': 'Bad Request'}), 400

        commentaire = update_commentaire(commentaire_id, description=data['description'])
        if commentaire:
            logger.info(f"Commentaire avec l'ID {commentaire_id} mis à jour")
            return jsonify({'id': commentaire.IDcommentaire}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un commentaire: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un commentaire
@commentaire_petition_bp.route('/delete/<int:commentaire_id>', methods=['DELETE'])
def remove_commentaire(commentaire_id):
    """
    Supprime un commentaire de la base de données.
    ---
    parameters:
      - name: commentaire_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Commentaire non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_commentaire(commentaire_id)
        if success:
            logger.info(f"Commentaire avec l'ID {commentaire_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un commentaire: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
