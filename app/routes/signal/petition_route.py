from flask import Blueprint, request, jsonify, current_app
from app.services.signal.petition_service import (
    create_petition, get_petition_by_id, get_all_petitions,
    get_petitions_by_citoyen, update_petition, delete_petition
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'petition'
petition_bp = Blueprint('petition', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@petition_bp.route('/add', methods=['POST'])
def add_petition():
    data = request.get_json()
    nouvelle_petition = create_petition(
        description=data['description'],
        nb_signature=data.get('nb_signature'),
        nb_partage=data.get('nb_partage'),
        date_fin=data.get('date_fin'),
        objectif_signature=data.get('objectif_signature'),
        titre=data['titre'],
        cible=data['cible'],
        id_moderateur=data.get('id_moderateur'),
        citoyen_id=data['citoyen_id']
    )
    logger.info(f"Nouvelle pétition créée avec l'ID: {nouvelle_petition.IDpetition}")
    return jsonify({'id': nouvelle_petition.IDpetition}), 201

# Route pour obtenir un enregistrement par ID
@petition_bp.route('/<int:petition_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_petition')
def get_petition(petition_id):
    logger.info(f"Récupération de la pétition avec l'ID: {petition_id}")
    petition = get_petition_by_id(petition_id)
    if petition:
        return jsonify({
            'id': petition.IDpetition,
            'description': petition.description,
            'nbSignature': petition.nbSignature,
            'nbPartage': petition.nbPartage,
            'dateFin': petition.dateFin,
            'objectifSignature': petition.objectifSignature,
            'titre': petition.titre,
            'cible': petition.cible,
            'IDmoderateur': petition.IDmoderateur,
            'citoyen_id': petition.citoyenID,
            'dateCreated': petition.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@petition_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_petitions')
def list_petitions():
    logger.info("Récupération de toutes les pétitions")
    petitions = get_all_petitions()
    return jsonify([{
        'id': p.IDpetition,
        'description': p.description,
        'nbSignature': p.nbSignature,
        'nbPartage': p.nbPartage,
        'dateFin': p.dateFin,
        'objectifSignature': p.objectifSignature,
        'titre': p.titre,
        # 'cible': p.cible.string,
        'IDmoderateur': p.IDmoderateur,
        'citoyen_id': p.citoyenID,
        'dateCreated': p.dateCreated
        
    } for p in petitions])

# Route pour obtenir les enregistrements par citoyen
@petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_petitions_by_citoyen')
def list_petitions_by_citoyen(citoyen_id):
    logger.info(f"Récupération des pétitions pour le citoyen avec l'ID: {citoyen_id}")
    petitions = get_petitions_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpetition,
        'description': p.description,
        'nbSignature': p.nbSignature,
        'nbPartage': p.nbPartage,
        'dateFin': p.dateFin,
        'objectifSignature': p.objectifSignature,
        'titre': p.titre,
        'cible': p.cible,
        'IDmoderateur': p.IDmoderateur,
        'dateCreated': p.dateCreated
    } for p in petitions])

# Route pour mettre à jour un enregistrement
@petition_bp.route('/update/<int:petition_id>', methods=['PUT'])
def modify_petition(petition_id):
    data = request.get_json()
    petition = update_petition(
        petition_id,
        description=data.get('description'),
        nb_signature=data.get('nb_signature'),
        nb_partage=data.get('nb_partage'),
        date_fin=data.get('date_fin'),
        objectif_signature=data.get('objectif_signature'),
        titre=data.get('titre'),
        cible=data.get('cible'),
        id_moderateur=data.get('id_moderateur')
    )
    if petition:
        logger.info(f"Pétition avec l'ID {petition_id} mise à jour")
        return jsonify({'id': petition.IDpetition}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@petition_bp.route('/delete/<int:petition_id>', methods=['DELETE'])
def remove_petition(petition_id):
    success = delete_petition(petition_id)
    if success:
        logger.info(f"Pétition avec l'ID {petition_id} supprimée")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
