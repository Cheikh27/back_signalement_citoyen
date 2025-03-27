from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.commentaire.commentairePublication_service import (
    create_commentaire_publication, get_commentaire_publication_by_id, get_all_commentaires_publication,
    get_commentaires_publication_by_citoyen, get_commentaires_publication_by_publication,
    update_commentaire_publication, delete_commentaire_publication
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'commentaire_publication'
commentaire_publication_bp = Blueprint('commentaire_publication', __name__)

# Route pour créer un nouvel enregistrement
@commentaire_publication_bp.route('/add', methods=['POST'])
def add_commentaire_publication():
    """
    Ajoute un nouveau commentaire à une publication.
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
            publication_id:
              type: integer
              example: 1
    responses:
      201:
        description: Commentaire de publication créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['description', 'citoyen_id', 'publication_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un commentaire de publication")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_commentaire = create_commentaire_publication(
            description=data['description'],
            citoyen_id=data['citoyen_id'],
            publication_id=data['publication_id']
        )
        logger.info(f"Nouveau commentaire de publication créé avec l'ID: {nouveau_commentaire.IDcommentaire}")
        return jsonify({'id': nouveau_commentaire.IDcommentaire}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un commentaire de publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@commentaire_publication_bp.route('/<int:commentaire_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_commentaire_publication')
def get_commentaire_publication(commentaire_id):
    """
    Récupère un commentaire de publication spécifique via son ID.
    ---
    parameters:
      - name: commentaire_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du commentaire de publication
      404:
        description: Commentaire de publication non trouvé
    """
    logger.info(f"Récupération du commentaire de publication avec l'ID: {commentaire_id}")
    commentaire = get_commentaire_publication_by_id(commentaire_id)
    if commentaire:
        return jsonify({
            'id': commentaire.IDcommentaire,
            'description': commentaire.description,
            'citoyen_id': commentaire.citoyenID,
            'publication_id': commentaire.publicationID,
            'dateCreated': commentaire.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les commentaires de publication
@commentaire_publication_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_publication')
def list_commentaires_publication():
    """
    Récupère tous les commentaires de publication enregistrés.
    ---
    responses:
      200:
        description: Liste des commentaires de publication
    """
    logger.info("Récupération de tous les commentaires de publication")
    commentaires = get_all_commentaires_publication()
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'publication_id': c.publicationID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les commentaires de publication d'un citoyen
@commentaire_publication_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_publication_by_citoyen')
def list_commentaires_publication_by_citoyen(citoyen_id):
    """
    Récupère tous les commentaires de publication d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des commentaires de publication
    """
    logger.info(f"Récupération des commentaires de publication pour le citoyen avec l'ID: {citoyen_id}")
    commentaires = get_commentaires_publication_by_citoyen(citoyen_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'publication_id': c.publicationID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les commentaires de publication d'une publication
@commentaire_publication_bp.route('/<int:publication_id>/publications', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_commentaires_publication_by_publication')
def list_commentaires_publication_by_publication(publication_id):
    """
    Récupère tous les commentaires de publication liés à une publication spécifique.
    ---
    parameters:
      - name: publication_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des commentaires de publication associés
    """
    logger.info(f"Récupération des commentaires de publication pour la publication avec l'ID: {publication_id}")
    commentaires = get_commentaires_publication_by_publication(publication_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour mettre à jour un commentaire de publication
@commentaire_publication_bp.route('/update/<int:commentaire_id>', methods=['PUT'])
def modify_commentaire_publication(commentaire_id):
    """
    Met à jour un commentaire de publication existant.
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
        description: Commentaire de publication mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Commentaire de publication non trouvé
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour un commentaire de publication")
            return jsonify({'message': 'Bad Request'}), 400

        commentaire = update_commentaire_publication(commentaire_id, description=data['description'])
        if commentaire:
            logger.info(f"Commentaire de publication avec l'ID {commentaire_id} mis à jour")
            return jsonify({'id': commentaire.IDcommentaire}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un commentaire de publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un commentaire de publication
@commentaire_publication_bp.route('/delete/<int:commentaire_id>', methods=['DELETE'])
def remove_commentaire_publication(commentaire_id):
    """
    Supprime un commentaire de publication de la base de données.
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
        description: Commentaire de publication non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_commentaire_publication(commentaire_id)
        if success:
            logger.info(f"Commentaire de publication avec l'ID {commentaire_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un commentaire de publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
