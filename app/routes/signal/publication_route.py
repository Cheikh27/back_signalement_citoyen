from flask import Blueprint, request, jsonify, current_app
from app.services.signal.publication_service import (
    create_publication, get_publication_by_id, get_all_publications,
    get_publications_by_autorite, get_publications_by_signalement,
    update_publication, delete_publication
)
import logging
# from flask_caching import Cache # type: ignore

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'publication'
publication_bp = Blueprint('publication', __name__)

# Initialiser le cache
# cache = Cache(current_app)

# Route pour créer un nouvel enregistrement
@publication_bp.route('/add', methods=['POST'])
def add_publication():
    data = request.get_json()
    nouvelle_publication = create_publication(
        titre=data['titre'],
        description=data['description'],
        element=data['element'],
        nb_aime_positif=data.get('nb_aime_positif'),
        nb_aime_negatif=data.get('nb_aime_negatif'),
        autorite_id=data['autorite_id'],
        signalement_id=data['signalement_id'],
        IDmoderateur=data.get("moderateur_id")
    )
    logger.info(f"Nouvelle publication créée avec l'ID: {nouvelle_publication.IDpublication}")
    return jsonify({'id': nouvelle_publication.IDpublication}), 201

# Route pour obtenir un enregistrement par ID
@publication_bp.route('/<int:publication_id>', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='get_publication')
def get_publication(publication_id):
    logger.info(f"Récupération de la publication avec l'ID: {publication_id}")
    publication = get_publication_by_id(publication_id)
    if publication:
        return jsonify({
            'id': publication.IDpublication,
            'titre': publication.titre,
            'description': publication.description,
            'element': publication.element,
            'nbAimePositif': publication.nbAimePositif,
            'nbAimeNegatif': publication.nbAimeNegatif,
            'dateCreated': publication.dateCreated,
            'autorite_id': publication.autoriteID,
            'signalement_id': publication.signalementID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@publication_bp.route('/all', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_publications')
def list_publications():
    logger.info("Récupération de toutes les publications")
    publications = get_all_publications()
    return jsonify([{
        'id': p.IDpublication,
        'titre': p.titre,
        'description': p.description,
        'element': p.element,
        'nbAimePositif': p.nbAimePositif,
        'nbAimeNegatif': p.nbAimeNegatif,
        'dateCreated': p.dateCreated,
        'autorite_id': p.autoriteID,
        'signalement_id': p.signalementID
    } for p in publications])

# Route pour obtenir les enregistrements par autorité
@publication_bp.route('/<int:autorite_id>/autorites', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_publications_by_autorite')
def list_publications_by_autorite(autorite_id):
    logger.info(f"Récupération des publications pour l'autorité avec l'ID: {autorite_id}")
    publications = get_publications_by_autorite(autorite_id)
    return jsonify([{
        'id': p.IDpublication,
        'titre': p.titre,
        'description': p.description,
        'element': p.element,
        'nbAimePositif': p.nbAimePositif,
        'nbAimeNegatif': p.nbAimeNegatif,
        'dateCreated': p.dateCreated,
        'signalement_id': p.signalementID
    } for p in publications])

# Route pour obtenir les enregistrements par signalement
@publication_bp.route('/<int:signalement_id>/signalements', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_publications_by_signalement')
def list_publications_by_signalement(signalement_id):
    logger.info(f"Récupération des publications pour le signalement avec l'ID: {signalement_id}")
    publications = get_publications_by_signalement(signalement_id)
    return jsonify([{
        'id': p.IDpublication,
        'titre': p.titre,
        'description': p.description,
        'element': p.element,
        'nbAimePositif': p.nbAimePositif,
        'nbAimeNegatif': p.nbAimeNegatif,
        'dateCreated': p.dateCreated,
        'autorite_id': p.autoriteID
    } for p in publications])

# Route pour mettre à jour un enregistrement
@publication_bp.route('/update/<int:publication_id>', methods=['PUT'])
def modify_publication(publication_id):
    data = request.get_json()
    publication = update_publication(
        publication_id,
        titre=data.get('titre'),
        description=data.get('description'),
        element=data.get('element'),
        nb_aime_positif=data.get('nb_aime_positif'),
        nb_aime_negatif=data.get('nb_aime_negatif')
    )
    if publication:
        logger.info(f"Publication avec l'ID {publication_id} mise à jour")
        return jsonify({'id': publication.IDpublication}), 200
    return jsonify({'message': 'Not found'}), 404

# Route pour supprimer un enregistrement
@publication_bp.route('/delete/<int:publication_id>', methods=['DELETE'])
def remove_publication(publication_id):
    success = delete_publication(publication_id)
    if success:
        logger.info(f"Publication avec l'ID {publication_id} supprimée")
        return '', 204
    return jsonify({'message': 'Not found'}), 404
