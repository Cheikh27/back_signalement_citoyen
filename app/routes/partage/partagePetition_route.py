from flask import Blueprint, request, jsonify, current_app
from app.services.partage.partagePetition_service import (
    create_partager_petition, get_partager_petition_by_id, get_all_partager_petitions,
    get_partager_petitions_by_citoyen, get_partager_petitions_by_petition,
    update_partager_petition, delete_partager_petition
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'partager_petition'
partager_petition_bp = Blueprint('partager_petition', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@partager_petition_bp.route('/add', methods=['POST'])
def add_partager_petition():
    data = request.get_json()
    nouveau_partage = create_partager_petition(
        citoyen_id=data['citoyen_id'],
        petition_id=data['petition_id'],
        nb_partage=data.get('nb_partage', 0)
    )
    logger.info(f"Nouveau partage de pétition créé avec l'ID: {nouveau_partage.IDpartager}")
    return jsonify({'id': nouveau_partage.IDpartager}), 201

# Route pour obtenir un enregistrement par ID
@partager_petition_bp.route('/<int:partager_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_partager_petition')
def get_partager_petition(partager_id):
    logger.info(f"Récupération du partage de pétition avec l'ID: {partager_id}")
    partager = get_partager_petition_by_id(partager_id)
    if partager:
        return jsonify({
            'id': partager.IDpartager,
            'dateCreated': partager.dateCreated,
            'nbPartage': partager.nbPartage,
            'citoyen_id': partager.citoyenID,
            'petition_id': partager.petitionID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@partager_petition_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_petitions')
def list_partager_petitions():
    logger.info("Récupération de tous les partages de pétition")
    partager_petitions = get_all_partager_petitions()
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID,
        'petition_id': p.petitionID
    } for p in partager_petitions])

# Route pour obtenir les enregistrements par citoyen
@partager_petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_petitions_by_citoyen')
def list_partager_petitions_by_citoyen(citoyen_id):
    logger.info(f"Récupération des partages de pétition pour le citoyen avec l'ID: {citoyen_id}")
    partager_petitions = get_partager_petitions_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'petition_id': p.petitionID
    } for p in partager_petitions])

# Route pour obtenir les enregistrements par pétition
@partager_petition_bp.route('/<int:petition_id>/petitions', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_petitions_by_petition')
def list_partager_petitions_by_petition(petition_id):
    logger.info(f"Récupération des partages de pétition pour la pétition avec l'ID: {petition_id}")
    partager_petitions = get_partager_petitions_by_petition(petition_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID
    } for p in partager_petitions])

# Route pour mettre à jour un enregistrement
@partager_petition_bp.route('/update/<int:partager_id>', methods=['PUT'])
def modify_partager_petition(partager_id):
    data = request.get_json()
    partager = update_partager_petition(partager_id, nb_partage=data.get('nb_partage'))
    if partager:
        logger.info(f"Partage de pétition avec l'ID {partager_id} mis à jour")
        return jsonify({'id': partager.IDpartager}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@partager_petition_bp.route('/delete/<int:partager_id>', methods=['DELETE'])
def remove_partager_petition(partager_id):
    success = delete_partager_petition(partager_id)
    if success:
        logger.info(f"Partage de pétition avec l'ID {partager_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
