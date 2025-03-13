from flask import Blueprint, request, jsonify, current_app
from app.services.commentaire.commentairePublication_service import (
    create_commentaire_publication, get_commentaire_publication_by_id, get_all_commentaires_publication,
    get_commentaires_publication_by_citoyen, get_commentaires_publication_by_publication,
    update_commentaire_publication, delete_commentaire_publication
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'commentaire_publication'
commentaire_publication_bp = Blueprint('commentaire_publication', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@commentaire_publication_bp.route('/add', methods=['POST'])
def add_commentaire_publication():
    data = request.get_json()
    nouveau_commentaire = create_commentaire_publication(
        description=data['description'],
        citoyen_id=data['citoyen_id'],
        publication_id=data['publication_id']
    )
    logger.info(f"Nouveau commentaire de publication créé avec l'ID: {nouveau_commentaire.IDcommentaire}")
    return jsonify({'id': nouveau_commentaire.IDcommentaire}), 201

# Route pour obtenir un enregistrement par ID
@commentaire_publication_bp.route('/<int:commentaire_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_commentaire_publication')
def get_commentaire_publication(commentaire_id):
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

# Route pour obtenir tous les enregistrements
@commentaire_publication_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_publication')
def list_commentaires_publication():
    logger.info("Récupération de tous les commentaires de publication")
    commentaires = get_all_commentaires_publication()
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'publication_id': c.publicationID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les enregistrements par citoyen
@commentaire_publication_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_publication_by_citoyen')
def list_commentaires_publication_by_citoyen(citoyen_id):
    logger.info(f"Récupération des commentaires de publication pour le citoyen avec l'ID: {citoyen_id}")
    commentaires = get_commentaires_publication_by_citoyen(citoyen_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'publication_id': c.publicationID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les enregistrements par publication
@commentaire_publication_bp.route('/<int:publication_id>/publications', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_publication_by_publication')
def list_commentaires_publication_by_publication(publication_id):
    logger.info(f"Récupération des commentaires de publication pour la publication avec l'ID: {publication_id}")
    commentaires = get_commentaires_publication_by_publication(publication_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour mettre à jour un enregistrement
@commentaire_publication_bp.route('/update/<int:commentaire_id>', methods=['PUT'])
def modify_commentaire_publication(commentaire_id):
    data = request.get_json()
    commentaire = update_commentaire_publication(commentaire_id, description=data.get('description'))
    if commentaire:
        logger.info(f"Commentaire de publication avec l'ID {commentaire_id} mis à jour")
        return jsonify({'id': commentaire.IDcommentaire}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@commentaire_publication_bp.route('/delete/<int:commentaire_id>', methods=['DELETE'])
def remove_commentaire_publication(commentaire_id):
    success = delete_commentaire_publication(commentaire_id)
    if success:
        logger.info(f"Commentaire de publication avec l'ID {commentaire_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
