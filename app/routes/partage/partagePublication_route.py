from flask import Blueprint, request, jsonify, current_app
from app.services.partage.partagePublication_service import (
    create_partager_publication, get_partager_publication_by_id, get_all_partager_publications,
    get_partager_publications_by_citoyen, get_partager_publications_by_publication,
    update_partager_publication, delete_partager_publication
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'partager_publication'
partager_publication_bp = Blueprint('partager_publication', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@partager_publication_bp.route('/add', methods=['POST'])
def add_partager_publication():
    data = request.get_json()
    nouveau_partage = create_partager_publication(
        citoyen_id=data['citoyen_id'],
        publication_id=data['publication_id'],
        nb_partage=data.get('nb_partage', 0)
    )
    logger.info(f"Nouveau partage de publication créé avec l'ID: {nouveau_partage.IDpartager}")
    return jsonify({'id': nouveau_partage.IDpartager}), 201

# Route pour obtenir un enregistrement par ID
@partager_publication_bp.route('/<int:partager_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_partager_publication')
def get_partager_publication(partager_id):
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

# Route pour obtenir tous les enregistrements
@partager_publication_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_publications')
def list_partager_publications():
    logger.info("Récupération de tous les partages de publication")
    partager_publications = get_all_partager_publications()
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID,
        'publication_id': p.publicationID
    } for p in partager_publications])

# Route pour obtenir les enregistrements par citoyen
@partager_publication_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_publications_by_citoyen')
def list_partager_publications_by_citoyen(citoyen_id):
    logger.info(f"Récupération des partages de publication pour le citoyen avec l'ID: {citoyen_id}")
    partager_publications = get_partager_publications_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'publication_id': p.publicationID
    } for p in partager_publications])

# Route pour obtenir les enregistrements par publication
@partager_publication_bp.route('/<int:publication_id>/publications', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_publications_by_publication')
def list_partager_publications_by_publication(publication_id):
    logger.info(f"Récupération des partages de publication pour la publication avec l'ID: {publication_id}")
    partager_publications = get_partager_publications_by_publication(publication_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID
    } for p in partager_publications])

# Route pour mettre à jour un enregistrement
@partager_publication_bp.route('/update/<int:partager_id>', methods=['PUT'])
def modify_partager_publication(partager_id):
    data = request.get_json()
    partager = update_partager_publication(partager_id, nb_partage=data.get('nb_partage'))
    if partager:
        logger.info(f"Partage de publication avec l'ID {partager_id} mis à jour")
        return jsonify({'id': partager.IDpartager}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@partager_publication_bp.route('/delete/<int:partager_id>', methods=['DELETE'])
def remove_partager_publication(partager_id):
    success = delete_partager_publication(partager_id)
    if success:
        logger.info(f"Partage de publication avec l'ID {partager_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
