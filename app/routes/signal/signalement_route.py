from flask import Blueprint, request, jsonify, current_app
from app.services.signal.signalement_service import (
    create_signalement, get_signalement_by_id, get_all_signalements,
    get_signalements_by_citoyen, update_signalement, delete_signalement
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'signalement'
signalement_bp = Blueprint('signalement', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@signalement_bp.route('/add', methods=['POST'])
def add_signalement():
    data = request.get_json()
    nouveau_signalement = create_signalement(
        description=data['description'],
        elements=data['elements'],
        statut=data.get('statut', 'en_cours'),
        nb_vote_positif=data.get('nb_vote_positif'),
        nb_vote_negatif=data.get('nb_vote_negatif'),
        cible=data['cible'],
        id_moderateur=data.get('id_moderateur'),
        citoyen_id=data['citoyen_id']
    )
    logger.info(f"Nouveau signalement créé avec l'ID: {nouveau_signalement.IDsignalement}")
    return jsonify({'Nouveau signalement créé avec l\'ID': nouveau_signalement.IDsignalement}), 201

# Route pour obtenir un enregistrement par ID
@signalement_bp.route('/<int:signalement_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_signalement')
def get_signalement(signalement_id):
    logger.info(f"Récupération du signalement avec l'ID: {signalement_id}")
    signalement = get_signalement_by_id(signalement_id)
    if signalement:
        return jsonify({
            'id': signalement.IDsignalement,
            'description': signalement.description,
            'elements': signalement.elements,
            'statut': signalement.statut,
            'nbVotePositif': signalement.nbVotePositif,
            'nbVoteNegatif': signalement.nbVoteNegatif,
            'cible': signalement.cible,
            'IDmoderateur': signalement.IDmoderateur,
            'citoyen_id': signalement.citoyenID,
            'dateCreated': signalement.dateCreated
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@signalement_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_signalements')
def list_signalements():
    logger.info("Récupération de tous les signalements")
    signalements = get_all_signalements()
    return jsonify([{
        'id': s.IDsignalement,
        'description': s.description,
        'elements': s.elements,
        'statut': s.statut,
        'nbVotePositif': s.nbVotePositif,
        'nbVoteNegatif': s.nbVoteNegatif,
        'cible': s.cible,
        'IDmoderateur': s.IDmoderateur,
        'citoyen_id': s.citoyenID,
        'dateCreated': s.dateCreated
    } for s in signalements])

# Route pour obtenir les enregistrements par citoyen
@signalement_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_signalements_by_citoyen')
def list_signalements_by_citoyen(citoyen_id):
    logger.info(f"Récupération des signalements pour le citoyen avec l'ID: {citoyen_id}")
    signalements = get_signalements_by_citoyen(citoyen_id)
    return jsonify([{
        'id': s.IDsignalement,
        'description': s.description,
        'elements': s.elements,
        'statut': s.statut,
        'nbVotePositif': s.nbVotePositif,
        'nbVoteNegatif': s.nbVoteNegatif,
        'cible': s.cible,
        'IDmoderateur': s.IDmoderateur,
        'dateCreated': s.dateCreated
    } for s in signalements])

# Route pour mettre à jour un enregistrement
@signalement_bp.route('/update/<int:signalement_id>', methods=['PUT'])
def modify_signalement(signalement_id):
    data = request.get_json()
    signalement = update_signalement(
        signalement_id,
        description=data.get('description'),
        elements=data.get('elements'),
        statut=data.get('statut'),
        nb_vote_positif=data.get('nb_vote_positif'),
        nb_vote_negatif=data.get('nb_vote_negatif'),
        cible=data.get('cible'),
        id_moderateur=data.get('id_moderateur')
    )
    if signalement:
        logger.info(f"Signalement avec l'ID {signalement_id} mis à jour")
        return jsonify({'id': signalement.IDsignalement}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@signalement_bp.route('/delete/<int:signalement_id>', methods=['DELETE'])
def remove_signalement(signalement_id):
    success = delete_signalement(signalement_id)
    if success:
        logger.info(f"Signalement avec l'ID {signalement_id} supprimé")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
