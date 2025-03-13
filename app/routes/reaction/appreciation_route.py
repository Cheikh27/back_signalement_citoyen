from flask import Blueprint, request, jsonify, current_app
from app.services.reaction.appreciation_service import (
    create_appreciation, get_appreciation_by_id, get_all_appreciations,
    get_appreciations_by_citoyen, get_appreciations_by_publication,
    delete_appreciation
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'appreciation'
appreciation_bp = Blueprint('appreciation', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@appreciation_bp.route('/add', methods=['POST'])
def add_appreciation():
    data = request.get_json()
    nouvelle_appreciation = create_appreciation(
        citoyen_id=data['citoyen_id'],
        publication_id=data['publication_id']
    )
    logger.info(f"Nouvelle appréciation créée avec l'ID: {nouvelle_appreciation.IDappreciation}")
    return jsonify({'id': nouvelle_appreciation.IDappreciation}), 201

# Route pour obtenir un enregistrement par ID
@appreciation_bp.route('/<int:appreciation_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_appreciation')
def get_appreciation(appreciation_id):
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
# @cache.cached(timeout=60, key_prefix='list_appreciations')
def list_appreciations():
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
# @cache.cached(timeout=60, key_prefix='list_appreciations_by_citoyen')
def list_appreciations_by_citoyen(citoyen_id):
    logger.info(f"Récupération des appréciations pour le citoyen avec l'ID: {citoyen_id}")
    appreciations = get_appreciations_by_citoyen(citoyen_id)
    return jsonify([{
        'id': a.IDappreciation,
        'dateCreated': a.dateCreated,
        'publication_id': a.PublicationID
    } for a in appreciations])

# Route pour obtenir les enregistrements par publication
@appreciation_bp.route('/<int:publication_id>/publications', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_appreciations_by_publication')
def list_appreciations_by_publication(publication_id):
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
    success = delete_appreciation(appreciation_id)
    if success:
        logger.info(f"Appréciation avec l'ID {appreciation_id} supprimée")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
