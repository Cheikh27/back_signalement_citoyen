from flask import Blueprint, request, jsonify, current_app
from app.services.autres.appartenir_service import (
    create_appartenir, get_appartenir_by_id, get_all_appartenirs,
    get_appartenirs_by_citoyen, get_appartenirs_by_groupe,
    update_appartenir, delete_appartenir
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'appartenir'
appartenir_bp = Blueprint('appartenir', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@appartenir_bp.route('/add', methods=['POST'])
def add_appartenir():
    data = request.get_json()
    nouvel_appartenir = create_appartenir(
        citoyen_id=data['citoyen_id'],
        groupe_id=data['groupe_id']
    )
    logger.info(f"Nouvel enregistrement d'appartenance créé avec l'ID: {nouvel_appartenir.IDappartenir}")
    return jsonify({'id': nouvel_appartenir.IDappartenir}), 201

# Route pour obtenir un enregistrement par ID
@appartenir_bp.route('/<int:appartenir_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_appartenir')
def get_appartenir(appartenir_id):
    logger.info(f"Récupération de l'enregistrement d'appartenance avec l'ID: {appartenir_id}")
    appartenir = get_appartenir_by_id(appartenir_id)
    if appartenir:
        return jsonify({
            'id': appartenir.IDappartenir,
            'dateCreated': appartenir.dateCreated,
            'citoyen_id': appartenir.citoyenID,
            'groupe_id': appartenir.groupeID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@appartenir_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_')
def list_appartenirs():
    logger.info("Récupération de tous les enregistrements d'appartenance")
    appartenirs= get_all_appartenirs()
    return jsonify([{
        'id': a.IDappartenir,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID,
        'groupe_id': a.groupeID
    } for a in appartenirs])

# Route pour obtenir les enregistrements par citoyen
@appartenir_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_appartenirs_by_citoyen')
def list_appartenirs_by_citoyen(citoyen_id):
    logger.info(f"Récupération des enregistrements d'appartenance pour le citoyen avec l'ID: {citoyen_id}")
    appartenirs = get_appartenirs_by_citoyen(citoyen_id)
    return jsonify([{
        'id': a.IDappartenir,
        'dateCreated': a.dateCreated,
        'groupe_id': a.groupeID
    } for a in appartenirs])

# Route pour obtenir les enregistrements par groupe
@appartenir_bp.route('/<int:groupe_id>/groupes', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_appartenirs_by_groupe')
def list_appartenirs_by_groupe(groupe_id):
    logger.info(f"Récupération des enregistrements d'appartenance pour le groupe avec l'ID: {groupe_id}")
    appartenirs = get_appartenirs_by_groupe(groupe_id)
    return jsonify([{
        'id': a.IDappartenir,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID
    } for a in appartenirs])

# Route pour mettre à jour un enregistrement
@appartenir_bp.route('/update/<int:appartenir_id>', methods=['PUT'])
def modify_appartenir(appartenir_id):
    data = request.get_json()
    appartenir = update_appartenir(
        appartenir_id,
        citoyen_id=data.get('citoyen_id'),
        groupe_id=data.get('groupe_id')
    )
    if appartenir:
        logger.info(f"Enregistrement d'appartenance avec l'ID {appartenir_id} mis à jour")
        return jsonify({'id': appartenir.IDappartenir}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@appartenir_bp.route('/delete/<int:appartenir_id>', methods=['DELETE'])
def remove_appartenir(appartenir_id):
    success = delete_appartenir(appartenir_id)
    if success:
        logger.info(f"Enregistrement d'appartenance avec l'ID {appartenir_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
