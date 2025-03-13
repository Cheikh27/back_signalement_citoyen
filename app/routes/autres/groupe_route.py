from flask import Blueprint, request, jsonify, current_app
from app.services.autres.groupe_service import (
    create_groupe, get_groupe_by_id, get_all_groupes,
    update_groupe, delete_groupe
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'groupe'
groupe_bp = Blueprint('groupe', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@groupe_bp.route('/add', methods=['POST'])
def add_groupe():
    data = request.get_json()
    nouveau_groupe = create_groupe(
        nom=data['nom'],
        description=data['description'],
        image=data['image'],
        admin=data['admin']
    )
    logger.info(f"Nouveau groupe créé avec l'ID: {nouveau_groupe.IDgroupe}")
    return jsonify({'id': nouveau_groupe.IDgroupe}), 201

# Route pour obtenir un enregistrement par ID
@groupe_bp.route('/<int:groupe_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_groupe')
def get_groupe(groupe_id):
    logger.info(f"Récupération du groupe avec l'ID: {groupe_id}")
    groupe = get_groupe_by_id(groupe_id)
    if groupe:
        return jsonify({
            'id': groupe.IDgroupe,
            'nom': groupe.nom,
            'description': groupe.description,
            # 'statut': groupe.statut,
            'image': groupe.image,
            'admin': groupe.admin,
            'dateCreated': groupe.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@groupe_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_groupes')
def list_groupes():
    logger.info("Récupération de tous les groupes")
    groupes = get_all_groupes()
    return jsonify([{
        'id': g.IDgroupe,
        'nom': g.nom,
        'description': g.description,
        # 'statut': g.statut,
        'image': g.image,
        'admin': g.admin,
        'dateCreated': g.dateCreated
    } for g in groupes])

# Route pour mettre à jour un enregistrement
@groupe_bp.route('/update/<int:groupe_id>', methods=['PUT'])
def modify_groupe(groupe_id):
    data = request.get_json()
    groupe = update_groupe(
        groupe_id,
        nom=data.get('nom'),
        description=data.get('description'),
        statut=data.get('statut'),
        image=data.get('image'),
        admin=data.get('admin')
    )
    if groupe:
        logger.info(f"Groupe avec l'ID {groupe_id} mis à jour")
        return jsonify({'id': groupe.IDgroupe}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@groupe_bp.route('/delete/<int:groupe_id>', methods=['DELETE'])
def remove_groupe(groupe_id):
    success = delete_groupe(groupe_id)
    if success:
        logger.info(f"Groupe avec l'ID {groupe_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
