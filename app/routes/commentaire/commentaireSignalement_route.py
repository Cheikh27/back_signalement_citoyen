from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.commentaire.commentaireSignalement_service import (
    create_commentaire_signalement, get_commentaire_signalement_by_id, get_all_commentaires_signalement,
    get_commentaires_signalement_by_citoyen, get_commentaires_signalement_by_signalement,
    update_commentaire_signalement, delete_commentaire_signalement
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'commentaire_signalement'
commentaire_signalement_bp = Blueprint('commentaire_signalement', __name__)

# Route pour créer un nouvel enregistrement
@commentaire_signalement_bp.route('/add', methods=['POST'])
def add_commentaire_signalement():
    """
    Ajoute un nouveau commentaire à un signalement.
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
            signalement_id:
              type: integer
              example: 1
    responses:
      201:
        description: Commentaire de signalement créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['description', 'citoyen_id', 'signalement_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un commentaire de signalement")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_commentaire = create_commentaire_signalement(
            description=data['description'],
            citoyen_id=data['citoyen_id'],
            signalement_id=data['signalement_id']
        )
        logger.info(f"Nouveau commentaire de signalement créé avec l'ID: {nouveau_commentaire.IDcommentaire}")
        return jsonify({'id': nouveau_commentaire.IDcommentaire}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un commentaire de signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@commentaire_signalement_bp.route('/<int:commentaire_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_commentaire_signalement')
def get_commentaire_signalement(commentaire_id):
    """
    Récupère un commentaire de signalement spécifique via son ID.
    ---
    parameters:
      - name: commentaire_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du commentaire de signalement
      404:
        description: Commentaire de signalement non trouvé
    """
    logger.info(f"Récupération du commentaire de signalement avec l'ID: {commentaire_id}")
    commentaire = get_commentaire_signalement_by_id(commentaire_id)
    if commentaire:
        return jsonify({
            'id': commentaire.IDcommentaire,
            'description': commentaire.description,
            'citoyen_id': commentaire.citoyenID,
            'signalement_id': commentaire.signalementID,
            'dateCreated': commentaire.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les commentaires de signalement
@commentaire_signalement_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_signalement')
def list_commentaires_signalement():
    """
    Récupère tous les commentaires de signalement enregistrés.
    ---
    responses:
      200:
        description: Liste des commentaires de signalement
    """
    logger.info("Récupération de tous les commentaires de signalement")
    commentaires = get_all_commentaires_signalement()
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'signalement_id': c.signalementID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les commentaires de signalement d'un citoyen
@commentaire_signalement_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_signalement_by_citoyen')
def list_commentaires_signalement_by_citoyen(citoyen_id):
    """
    Récupère tous les commentaires de signalement d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des commentaires de signalement
    """
    logger.info(f"Récupération des commentaires de signalement pour le citoyen avec l'ID: {citoyen_id}")
    commentaires = get_commentaires_signalement_by_citoyen(citoyen_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'signalement_id': c.signalementID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les commentaires de signalement d'un signalement
@commentaire_signalement_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_signalement_by_signalement')
def list_commentaires_signalement_by_signalement(signalement_id):
    """
    Récupère tous les commentaires de signalement liés à un signalement spécifique.
    ---
    parameters:
      - name: signalement_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des commentaires de signalement associés
    """
    logger.info(f"Récupération des commentaires de signalement pour le signalement avec l'ID: {signalement_id}")
    commentaires = get_commentaires_signalement_by_signalement(signalement_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour mettre à jour un commentaire de signalement
@commentaire_signalement_bp.route('/update/<int:commentaire_id>', methods=['PUT'])
def modify_commentaire_signalement(commentaire_id):
    """
    Met à jour un commentaire de signalement existant.
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
        description: Commentaire de signalement mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Commentaire de signalement non trouvé
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour un commentaire de signalement")
            return jsonify({'message': 'Bad Request'}), 400

        commentaire = update_commentaire_signalement(commentaire_id, description=data['description'])
        if commentaire:
            logger.info(f"Commentaire de signalement avec l'ID {commentaire_id} mis à jour")
            return jsonify({'id': commentaire.IDcommentaire}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un commentaire de signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un commentaire de signalement
@commentaire_signalement_bp.route('/delete/<int:commentaire_id>', methods=['DELETE'])
def remove_commentaire_signalement(commentaire_id):
    """
    Supprime un commentaire de signalement de la base de données.
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
        description: Commentaire de signalement non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_commentaire_signalement(commentaire_id)
        if success:
            logger.info(f"Commentaire de signalement avec l'ID {commentaire_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un commentaire de signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
