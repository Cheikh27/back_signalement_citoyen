from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.models.autres.suivre_model import Suivre
from app.services.autres.suivre_service import (
    create_suivre, get_suivre_by_id, get_all_suivres,
    get_suiveur_by_suivis,get_suivis_by_suiveur,
    update_suivre, delete_suivre
)

from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'suivre'
suivre_bp = Blueprint('suivre', __name__)

# Route pour créer un nouvel enregistrement
@suivre_bp.route('/add', methods=['POST'])
def add_suivre():
    """
    Crée un nouvel enregistrement de suivi.
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
            suiveur_id:
              type: integer
              example: 1
            suivis_id:
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
        if not data or 'suiveur_id' not in data or 'suivis_id' not in data:
            logger.error("Données incomplètes reçues pour créer un enregistrement de suivi")
            return jsonify({'message': 'Bad Request'}), 400

        nouvel_suivre = create_suivre(
            suiveur_id=data['suiveur_id'],
            suivis_id=data['suivis_id']
        )

        send_notification(
            user_id=data['suivis_id'],  # La personne suivie
            title="👤 Nouvel abonné !",
            message="Quelqu'un vous suit maintenant",
            entity_type='user',
            entity_id=data['suiveur_id'],
            priority='low',
            category='social'
        )

        
        logger.info(f"Nouvel enregistrement de suivi créé avec l'ID: {nouvel_suivre.IDsuivre}")
        return jsonify({'id': nouvel_suivre.IDsuivre}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un enregistrement de suivi: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@suivre_bp.route('/<int:suivre_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_suivre')
def get_suivre(suivre_id):
    """
    Récupère un enregistrement de suivi par son ID.
    ---
    parameters:
      - name: suivre_id
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
            suiveur_id:
              type: integer
              example: 1
            suivis_id:
              type: integer
              example: 1
      404:
        description: Enregistrement non trouvé
    """
    logger.info(f"Récupération de l'enregistrement de suivi avec l'ID: {suivre_id}")
    suivre = get_suivre_by_id(suivre_id)
    if suivre:
        return jsonify({
            'id': suivre.IDsuivre,
            'dateCreated': suivre.dateCreated,
            'suiveur_id': suivre.suiveurID,
            'suivis_id': suivre.suivisID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@suivre_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_suivres')
def list_suivres():
    """
    Récupère tous les enregistrements de suivi.
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
              suiveur_id:
                type: integer
                example: 1
              suivis_id:
                type: integer
                example: 1
    """
    logger.info("Récupération de tous les enregistrements de suivi")
    suivres = get_all_suivres()
    return jsonify([{
        'id': s.IDsuivre,
        'dateCreated': s.dateCreated,
        'suiveur_id': s.suiveurID,
        'suivis_id': s.suivisID,
        'is_deleted': s.is_deleted

        # dateCreated = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création
        # dateDeleted = db.Column(db.DateTime, nullable=True)  # Date de suppression
        # is_deleted = db.Column(db.Boolean, default=False)

    } for s in suivres])

# Route pour obtenir les enregistrements par suivre
@suivre_bp.route('/<int:suivis_id>/suiveurs', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_suivres_by_suivre')
def list_suiveur_by_suivis(suivis_id):
    """
    Récupère les enregistrements de suivi pour un utilisateur donné.
    ---
    parameters:
      - name: suiveur_id
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
              suivis_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des enregistrements de suivi pour l'utilisateur avec l'ID: {suivis_id}")
    suivres = get_suiveur_by_suivis(suivis_id)
    return jsonify([{
        'id': s.IDsuivre,
        'dateCreated': s.dateCreated,
        'suivis_id': s.suivisID,
        'suiveur_id': s.suiveurID
    } for s in suivres])

# Route pour obtenir les enregistrements par suivis
@suivre_bp.route('/<int:suiveur_id>/suivis', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_suivres_by_suivis')
def list_suivis_by_suiveur(suiveur_id):
    """
    Récupère les enregistrements de suivi pour un utilisateur donné.
    ---
    parameters:
      - name: suivis_id
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
              suiveur_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des enregistrements de suivi pour l'utilisateur avec l'ID: {suiveur_id}")
    suivres = get_suivis_by_suiveur(suiveur_id)
    return jsonify([{
        'id': s.IDsuivre,
        'dateCreated': s.dateCreated,
        'suiveur_id': s.suiveurID,
        'suivis_id': s.suivisID
    } for s in suivres])

# Route pour mettre à jour un enregistrement
@suivre_bp.route('/update/<int:suivre_id>', methods=['PUT'])
def modify_suivre(suivre_id):
    """
    Met à jour un enregistrement de suivi.
    ---
    consumes:
      - application/json
    parameters:
      - name: suiveur_id
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
            suiveur_id:
              type: integer
              example: 1
            suivis_id:
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
        if not data or ('suiveur_id' not in data and 'suivis_id' not in data):
            logger.error("Données incomplètes reçues pour mettre à jour un enregistrement de suivi")
            return jsonify({'message': 'Bad Request'}), 400

        suivre = update_suivre(
            suivre_id,
            suiveur_id=data.get('suiveur_id'),
            suivis_id=data.get('suivis_id')
        )
        if suivre:
            logger.info(f"Enregistrement de suivi avec l'ID {suivre_id} mis à jour")
            return jsonify({'id': suivre.IDsuivre}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un enregistrement de suivi: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@suivre_bp.route('/delete/<int:suivre_id>', methods=['DELETE'])
def remove_suivre(suivre_id):
    """
    Supprime un enregistrement de suivi.
    ---
    parameters:
      - name: suiveur_id
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
        success = delete_suivre(suivre_id)
        if success:
            logger.info(f"Enregistrement de suivi avec l'ID {suivre_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un enregistrement de suivi: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour vérifier si un utilisateur suit un autre
@suivre_bp.route('/check/<int:suiveur_id>/<int:suivis_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='check_suivre')
def check_suivre(suiveur_id, suivis_id):
    """
    Vérifie si un utilisateur suit un autre utilisateur.
    ---
    parameters:
      - name: suiveur_id
        in: path
        required: true
        type: integer
        example: 1
      - name: suivis_id
        in: path
        required: true
        type: integer
        example: 2
    responses:
      200:
        description: Statut de suivi
        schema:
          type: object
          properties:
            is_following:
              type: boolean
              example: true
            suivre_id:
              type: integer
              example: 1
    """
    try:
        logger.info(f"Vérification du suivi: utilisateur {suiveur_id} suit-il {suivis_id}")
        
        # Vérifier s'il existe une relation de suivi active
        suivre_relation = Suivre.query.filter_by(
            suiveurID=suiveur_id,
            suivisID=suivis_id,
            is_deleted=False
        ).first()
        
        if suivre_relation:
            return jsonify({
                'is_following': True,
                'suivre_id': suivre_relation.IDsuivre
            }), 200
        else:
            return jsonify({
                'is_following': False,
                'suivre_id': None
            }), 200
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du suivi: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour arrêter de suivre un utilisateur
@suivre_bp.route('/unfollow', methods=['POST'])
def unfollow_user():
    """
    Arrête de suivre un utilisateur.
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
            suiveur_id:
              type: integer
              example: 1
            suivis_id:
              type: integer
              example: 2
    responses:
      200:
        description: Arrêt de suivi réussi
      404:
        description: Relation de suivi non trouvée
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        if not data or 'suiveur_id' not in data or 'suivis_id' not in data:
            logger.error("Données incomplètes pour arrêter de suivre")
            return jsonify({'message': 'Bad Request'}), 400

        # Trouver et supprimer la relation de suivi
        suivre_relation = Suivre.query.filter_by(
            suiveurID=data['suiveur_id'],
            suivisID=data['suivis_id'],
            is_deleted=False
        ).first()
        
        if suivre_relation:
            success = delete_suivre(suivre_relation.IDsuivre)
            if success:
                logger.info(f"Utilisateur {data['suiveur_id']} a arrêté de suivre {data['suivis_id']}")
                return jsonify({'message': 'Unfollowed successfully'}), 200
            else:
                return jsonify({'message': 'Failed to unfollow'}), 500
        else:
            return jsonify({'message': 'Follow relationship not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt de suivi: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500