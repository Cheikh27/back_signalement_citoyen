from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.partage.partagePublication_service import (
    create_partager_publication, get_partager_publication_by_id, get_all_partager_publications,
    get_partager_publications_by_citoyen, get_partager_publications_by_publication,
    update_partager_publication, delete_partager_publication
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'partager_publication'
partager_publication_bp = Blueprint('partager_publication', __name__)

# Route pour créer un nouvel enregistrement
@partager_publication_bp.route('/add', methods=['POST'])
def add_partager_publication():
    """
    Ajoute un nouveau partage de publication.
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
            nb_partage:
              type: integer
              example: 0
    responses:
      201:
        description: Partage de publication créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['citoyen_id', 'publication_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un partage de publication")
            return jsonify({'message': 'Bad Request'}), 400

        nouveau_partage = create_partager_publication(
            citoyen_id=data['citoyen_id'],
            publication_id=data['publication_id'],
            nb_partage=data.get('nb_partage', 0)
        )
        logger.info(f"Nouveau partage de publication créé avec l'ID: {nouveau_partage.IDpartager}")
        return jsonify({'id': nouveau_partage.IDpartager}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un partage de publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@partager_publication_bp.route('/<int:partager_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_partager_publication')
def get_partager_publication(partager_id):
    """
    Récupère un partage de publication spécifique via son ID.
    ---
    parameters:
      - name: partager_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du partage de publication
      404:
        description: Partage de publication non trouvé
    """
    logger.info(f"Récupération du partage de publication avec l'ID: {partager_id}")
    partager = get_partager_publication_by_id(partager_id)
    if partager:
        return jsonify({
            'id': partager.IDpartager,
            'dateCreated': partager.dateCreated,
            'nbPartage': partager.nbPartage,
            'citoyen_id': partager.citoyenID,
            'publication_id': partager.publicationID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les partages de publication
@partager_publication_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_publications')
def list_partager_publications():
    """
    Récupère tous les partages de publication enregistrés.
    ---
    responses:
      200:
        description: Liste des partages de publication
    """
    logger.info("Récupération de tous les partages de publication")
    partager_publications = get_all_partager_publications()
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID,
        'publication_id': p.publicationID
    } for p in partager_publications])

# Route pour obtenir les partages de publication d'un citoyen
@partager_publication_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_publications_by_citoyen')
def list_partager_publications_by_citoyen(citoyen_id):
    """
    Récupère tous les partages de publication d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des partages de publication
    """
    logger.info(f"Récupération des partages de publication pour le citoyen avec l'ID: {citoyen_id}")
    partager_publications = get_partager_publications_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'publication_id': p.publicationID
    } for p in partager_publications])

# Route pour obtenir les partages de publication d'une publication
@partager_publication_bp.route('/<int:publication_id>/publications', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_partager_publications_by_publication')
def list_partager_publications_by_publication(publication_id):
    """
    Récupère tous les partages de publication liés à une publication spécifique.
    ---
    parameters:
      - name: publication_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des partages de publication associés
    """
    logger.info(f"Récupération des partages de publication pour la publication avec l'ID: {publication_id}")
    partager_publications = get_partager_publications_by_publication(publication_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID
    } for p in partager_publications])

# Route pour mettre à jour un partage de publication
@partager_publication_bp.route('/update/<int:partager_id>', methods=['PUT'])
def modify_partager_publication(partager_id):
    """
    Met à jour un partage de publication existant.
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
        description: Partage de publication mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Partage de publication non trouvé
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'nb_partage' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour un partage de publication")
            return jsonify({'message': 'Bad Request'}), 400

        partager = update_partager_publication(partager_id, nb_partage=data['nb_partage'])
        if partager:
            logger.info(f"Partage de publication avec l'ID {partager_id} mis à jour")
            return jsonify({'id': partager.IDpartager}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un partage de publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un partage de publication
@partager_publication_bp.route('/delete/<int:partager_id>', methods=['DELETE'])
def remove_partager_publication(partager_id):
    """
    Supprime un partage de publication de la base de données.
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
        description: Partage de publication non trouvé
      500:
        description: Erreur serveur
    """
    try:
        success = delete_partager_publication(partager_id)
        if success:
            logger.info(f"Partage de publication avec l'ID {partager_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un partage de publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
