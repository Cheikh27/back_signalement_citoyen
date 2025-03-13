from flask import Blueprint, request, jsonify, current_app
from app.services.commentaire.commentaireSignalement_service import (
    create_commentaire_signalement, get_commentaire_signalement_by_id, get_all_commentaires_signalement,
    get_commentaires_signalement_by_citoyen, get_commentaires_signalement_by_signalement,
    update_commentaire_signalement, delete_commentaire_signalement
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'commentaire_signalement'
commentaire_signalement_bp = Blueprint('commentaire_signalement', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@commentaire_signalement_bp.route('/add', methods=['POST'])
def add_commentaire_signalement():
    data = request.get_json()
    nouveau_commentaire = create_commentaire_signalement(
        description=data['description'],
        citoyen_id=data['citoyen_id'],
        signalement_id=data['signalement_id']
    )
    logger.info(f"Nouveau commentaire de signalement créé avec l'ID: {nouveau_commentaire.IDcommentaire}")
    return jsonify({'id': nouveau_commentaire.IDcommentaire}), 201

# Route pour obtenir un enregistrement par ID
@commentaire_signalement_bp.route('/<int:commentaire_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_commentaire_signalement')
def get_commentaire_signalement(commentaire_id):
    logger.info(f"Récupération du commentaire de signalement avec l'ID: {commentaire_id}")
    commentaire = get_commentaire_signalement_by_id(commentaire_id)
    if commentaire:
        return jsonify({
            'id': commentaire.IDcommentaire,
            'description': commentaire.description,
            'citoyen_id': commentaire.citoyenID,
            'signalement_id': commentaire.signalementID,
            'dateCreated': commentaire.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@commentaire_signalement_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_signalement')
def list_commentaires_signalement():
    logger.info("Récupération de tous les commentaires de signalement")
    commentaires = get_all_commentaires_signalement()
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'signalement_id': c.signalementID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les enregistrements par citoyen
@commentaire_signalement_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_signalement_by_citoyen')
def list_commentaires_signalement_by_citoyen(citoyen_id):
    logger.info(f"Récupération des commentaires de signalement pour le citoyen avec l'ID: {citoyen_id}")
    commentaires = get_commentaires_signalement_by_citoyen(citoyen_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'signalement_id': c.signalementID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour obtenir les enregistrements par signalement
@commentaire_signalement_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_commentaires_signalement_by_signalement')
def list_commentaires_signalement_by_signalement(signalement_id):
    logger.info(f"Récupération des commentaires de signalement pour le signalement avec l'ID: {signalement_id}")
    commentaires = get_commentaires_signalement_by_signalement(signalement_id)
    return jsonify([{
        'id': c.IDcommentaire,
        'description': c.description,
        'citoyen_id': c.citoyenID,
        'dateCreated': c.dateCreated
    } for c in commentaires])

# Route pour mettre à jour un enregistrement
@commentaire_signalement_bp.route('/update/<int:commentaire_id>', methods=['PUT'])
def modify_commentaire_signalement(commentaire_id):
    data = request.get_json()
    commentaire = update_commentaire_signalement(commentaire_id, description=data.get('description'))
    if commentaire:
        logger.info(f"Commentaire de signalement avec l'ID {commentaire_id} mis à jour")
        return jsonify({'id': commentaire.IDcommentaire}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@commentaire_signalement_bp.route('/delete/<int:commentaire_id>', methods=['DELETE'])
def remove_commentaire_signalement(commentaire_id):
    success = delete_commentaire_signalement(commentaire_id)
    if success:
        logger.info(f"Commentaire de signalement avec l'ID {commentaire_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
