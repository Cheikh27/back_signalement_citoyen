from flask import Blueprint, request, jsonify, current_app
from app.services.reaction.signature_service import (
    create_signature, get_signature_by_id, get_all_signatures,
    get_signatures_by_citoyen, get_signatures_by_petition,
    update_signature, delete_signature
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'signature'
signature_bp = Blueprint('signature', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@signature_bp.route('/add', methods=['POST'])
def add_signature():
    data = request.get_json()
    nouvelle_signature = create_signature(
        citoyen_id=data['citoyen_id'],
        petition_id=data['petition_id'],
        nb_signature=data.get('nb_signature', 1)
    )
    logger.info(f"Nouvelle signature créée avec l'ID: {nouvelle_signature.IDsignature}")
    return jsonify({'id': nouvelle_signature.IDsignature}), 201

# Route pour obtenir un enregistrement par ID
@signature_bp.route('/<int:signature_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_signature')
def get_signature(signature_id):
    logger.info(f"Récupération de la signature avec l'ID: {signature_id}")
    signature = get_signature_by_id(signature_id)
    if signature:
        return jsonify({
            'id': signature.IDsignature,
            'dateCreated': signature.dateCreated,
            'nbSignature': signature.nbSignature,
            'citoyen_id': signature.citoyenID,
            'petition_id': signature.petitionID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@signature_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_signatures')
def list_signatures():
    logger.info("Récupération de toutes les signatures")
    signatures = get_all_signatures()
    return jsonify([{
        'id': s.IDsignature,
        'dateCreated': s.dateCreated,
        'nbSignature': s.nbSignature,
        'citoyen_id': s.citoyenID,
        'petition_id': s.petitionID
    } for s in signatures])

# Route pour obtenir les enregistrements par citoyen
@signature_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_signatures_by_citoyen')
def list_signatures_by_citoyen(citoyen_id):
    logger.info(f"Récupération des signatures pour le citoyen avec l'ID: {citoyen_id}")
    signatures = get_signatures_by_citoyen(citoyen_id)
    return jsonify([{
        'id': s.IDsignature,
        'dateCreated': s.dateCreated,
        'nbSignature': s.nbSignature,
        'petition_id': s.petitionID
    } for s in signatures])

# Route pour obtenir les enregistrements par pétition
@signature_bp.route('/<int:petition_id>/petitions', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_signatures_by_petition')
def list_signatures_by_petition(petition_id):
    logger.info(f"Récupération des signatures pour la pétition avec l'ID: {petition_id}")
    signatures = get_signatures_by_petition(petition_id)
    return jsonify([{
        'id': s.IDsignature,
        'dateCreated': s.dateCreated,
        'nbSignature': s.nbSignature,
        'citoyen_id': s.citoyenID
    } for s in signatures])

# Route pour mettre à jour un enregistrement
@signature_bp.route('/update/<int:signature_id>', methods=['PUT'])
def modify_signature(signature_id):
    data = request.get_json()
    signature = update_signature(signature_id, nb_signature=data.get('nb_signature'))
    if signature:
        logger.info(f"Signature avec l'ID {signature_id} mise à jour")
        return jsonify({'id': signature.IDsignature}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@signature_bp.route('/delete/<int:signature_id>', methods=['DELETE'])
def remove_signature(signature_id):
    success = delete_signature(signature_id)
    if success:
        logger.info(f"Signature avec l'ID {signature_id} supprimée")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
