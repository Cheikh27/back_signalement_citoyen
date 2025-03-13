from flask import Blueprint, request, jsonify, current_app
from app.services.partage.partageSignalement_service import (
    create_partager_signalement, get_partager_signalement_by_id, get_all_partager_signalements,
    get_partager_signalements_by_citoyen, get_partager_signalements_by_signalement,
    update_partager_signalement, delete_partager_signalement
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'partager_signalement'
partager_signalement_bp = Blueprint('partager_signalement', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@partager_signalement_bp.route('/add', methods=['POST'])
def add_partager_signalement():
    data = request.get_json()
    nouveau_partage = create_partager_signalement(
        citoyen_id=data['citoyen_id'],
        signalement_id=data['signalement_id'],
        nb_partage=data.get('nb_partage', 0)
    )
    logger.info(f"Nouveau partage de signalement créé avec l'ID: {nouveau_partage.IDpartager}")
    return jsonify({'id': nouveau_partage.IDpartager}), 201

# Route pour obtenir un enregistrement par ID
@partager_signalement_bp.route('/<int:partager_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_partager_signalement')
def get_partager_signalement(partager_id):
    logger.info(f"Récupération du partage de signalement avec l'ID: {partager_id}")
    partager = get_partager_signalement_by_id(partager_id)
    if partager:
        return jsonify({
            'id': partager.IDpartager,
            'dateCreated': partager.dateCreated,
            'nbPartage': partager.nbPartage,
            'citoyen_id': partager.citoyenID,
            'signalement_id': partager.SignalementID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@partager_signalement_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_signalements')
def list_partager_signalements():
    logger.info("Récupération de tous les partages de signalement")
    partager_signalements = get_all_partager_signalements()
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID,
        'signalement_id': p.SignalementID
    } for p in partager_signalements])

# Route pour obtenir les enregistrements par citoyen
@partager_signalement_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_signalements_by_citoyen')
def list_partager_signalements_by_citoyen(citoyen_id):
    logger.info(f"Récupération des partages de signalement pour le citoyen avec l'ID: {citoyen_id}")
    partager_signalements = get_partager_signalements_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'signalement_id': p.SignalementID
    } for p in partager_signalements])

# Route pour obtenir les enregistrements par signalement
@partager_signalement_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_partager_signalements_by_signalement')
def list_partager_signalements_by_signalement(signalement_id):
    logger.info(f"Récupération des partages de signalement pour le signalement avec l'ID: {signalement_id}")
    partager_signalements = get_partager_signalements_by_signalement(signalement_id)
    return jsonify([{
        'id': p.IDpartager,
        'dateCreated': p.dateCreated,
        'nbPartage': p.nbPartage,
        'citoyen_id': p.citoyenID
    } for p in partager_signalements])

# Route pour mettre à jour un enregistrement
@partager_signalement_bp.route('/update/<int:partager_id>', methods=['PUT'])
def modify_partager_signalement(partager_id):
    data = request.get_json()
    partager = update_partager_signalement(partager_id, nb_partage=data.get('nb_partage'))
    if partager:
        logger.info(f"Partage de signalement avec l'ID {partager_id} mis à jour")
        return jsonify({'id': partager.IDpartager}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@partager_signalement_bp.route('/delete/<int:partager_id>', methods=['DELETE'])
def remove_partager_signalement(partager_id):
    success = delete_partager_signalement(partager_id)
    if success:
        logger.info(f"Partage de signalement avec l'ID {partager_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
