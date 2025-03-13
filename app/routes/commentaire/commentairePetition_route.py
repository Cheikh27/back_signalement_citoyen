from flask import Blueprint, request, jsonify, current_app
from app.services.commentaire.commentairePetition_service import (
    create_commentaire, get_commentaire_by_id, get_all_commentaires,
    get_commentaires_by_citoyen, get_commentaires_by_petition,
    update_commentaire, delete_commentaire
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'commentaire'
commentaire_petition_bp = Blueprint('commentaire', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@commentaire_petition_bp.route('/add', methods=['POST'])
def add_commentaire():
    data = request.get_json()
    nouveau_commentaire = create_commentaire(
        description=data['description'],
        citoyen_id=data['citoyen_id'],
        petition_id=data['petition_id']
    )
    logger.info(f"Nouveau commentaire créé avec l'ID: {nouveau_commentaire.IDcommentaire}")
    return jsonify({'id': nouveau_commentaire.IDcommentaire}), 201

# Route pour obtenir un enregistrement par ID
@commentaire_petition_bp.route('/<int:commentaire_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_commentaire')
def get_commentaire(commentaire_id):
    logger.info(f"Récupération du commentaire avec l'ID: {commentaire_id}")
    commentaire = get_commentaire_by_id(commentaire_id)
    if commentaire:
        return jsonify({
            'id': commentaire.IDcommentaire,
            'description': commentaire.description,
            'citoyen_id': commentaire.citoyenID,
            'petition_id': commentaire.petitionID,
            'dateCreated': commentaire.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@commentaire_petition_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires')
def list_commentaires():
    logger.info("Récupération de tous les commentaires")
    commentaires = get_all_commentaires()
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'petition_id': c.petitionID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les enregistrements par citoyen
@commentaire_petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_by_citoyen')
def list_commentaires_by_citoyen(citoyen_id):
    logger.info(f"Récupération des commentaires pour le citoyen avec l'ID: {citoyen_id}")
    commentaires = get_commentaires_by_citoyen(citoyen_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'petition_id': c.petitionID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les enregistrements par pétition
@commentaire_petition_bp.route('/<int:petition_id>/petitions', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_by_petition')
def list_commentaires_by_petition(petition_id):
    logger.info(f"Récupération des commentaires pour la pétition avec l'ID: {petition_id}")
    commentaires = get_commentaires_by_petition(petition_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour mettre à jour un enregistrement
@commentaire_petition_bp.route('/update/<int:commentaire_id>', methods=['PUT'])
def modify_commentaire(commentaire_id):
    data = request.get_json()
    commentaire = update_commentaire(commentaire_id, description=data.get('description'))
    if commentaire:
        logger.info(f"Commentaire avec l'ID {commentaire_id} mis à jour")
        return jsonify({'id': commentaire.IDcommentaire}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@commentaire_petition_bp.route('/delete/<int:commentaire_id>', methods=['DELETE'])
def remove_commentaire(commentaire_id):
    success = delete_commentaire(commentaire_id)
    if success:
        logger.info(f"Commentaire avec l'ID {commentaire_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
