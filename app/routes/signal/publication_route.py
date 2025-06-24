from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.signal.publication_service import (
    create_publication, get_publication_by_id, get_all_publications,
    get_publications_by_autorite, get_publications_by_signalement,
    update_publication, delete_publication
)
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'publication'
publication_bp = Blueprint('publication', __name__)

# Route pour créer un nouvel enregistrement
@publication_bp.route('/add', methods=['POST'])
def add_publication():
    """
    Crée une nouvelle publication.
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - titre
            - description
            - element
            - autorite_id
            - signalement_id
          properties:
            titre:
              type: string
              example: "Titre de la publication"
            description:
              type: string
              example: "Description détaillée"
            element:
              type: string
              example: "Élément associé"
            nb_aime_positif:
              type: integer
              example: 0
            nb_aime_negatif:
              type: integer
              example: 0
            moderateur_id:
              type: integer
              example: 1
    responses:
      201:
        description: Publication créée avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur interne
    """
    try:
        data = request.get_json()
        required_fields = ['titre', 'description', 'element', 'autorite_id', 'signalement_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer une publication")
            return jsonify({'message': 'Bad Request'}), 400

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

        from app.models.signal.signalement_model import Signalement
        signalement = Signalement.query.get(data['signalement_id'])
        
        if signalement:
            send_notification(
                user_id=signalement.citoyenID,
                title="📢 Réponse officielle !",
                message=f"Une autorité a publié une réponse à votre signalement: '{data['titre']}'",
                entity_type='publication',
                entity_id=nouvelle_publication.IDpublication,
                priority='urgent',  # Réponse officielle = urgent
                category='status'
            )
            
        logger.info(f"Nouvelle publication créée avec l'ID: {nouvelle_publication.IDpublication}")
        return jsonify({'id': nouvelle_publication.IDpublication}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'une publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@publication_bp.route('/<int:publication_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_publication')
def get_publication(publication_id):
    """
    Récupère une publication spécifique par son identifiant.
    ---
    parameters:
      - name: publication_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails de la publication
      404:
        description: Publication non trouvée
    """
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
@cache.cached(timeout=60, key_prefix='list_publications')
def list_publications():
    """
    Récupère toutes les publications enregistrées.
    ---
    responses:
      200:
        description: Liste de toutes les publications
    """
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
@cache.cached(timeout=60, key_prefix='list_publications_by_autorite')
def list_publications_by_autorite(autorite_id):
    """
    Récupère toutes les publications associées à une autorité spécifique.
    ---
    parameters:
      - name: autorite_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des publications de l'autorité
    """
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
@cache.cached(timeout=60, key_prefix='list_publications_by_signalement')
def list_publications_by_signalement(signalement_id):
    """
    Récupère toutes les publications associées à un signalement spécifique.
    ---
    parameters:
      - name: signalement_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des publications du signalement
    """
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
    """
    Met à jour une publication existante.
    ---
    parameters:
      - name: publication_id
        in: path
        required: true
        type: integer
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            titre:
              type: string
              example: "Nouveau titre"
            description:
              type: string
              example: "Nouvelle description"
            element:
              type: string
              example: "Nouvel élément"
            nb_aime_positif:
              type: integer
              example: 5
            nb_aime_negatif:
              type: integer
              example: 2
    responses:
      200:
        description: Publication mise à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Publication non trouvée
      500:
        description: Erreur serveur interne
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes reçues pour mettre à jour une publication")
            return jsonify({'message': 'Bad Request'}), 400

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

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'une publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@publication_bp.route('/delete/<int:publication_id>', methods=['DELETE'])
def remove_publication(publication_id):
    """
    Supprime une publication de la base de données.
    ---
    parameters:
      - name: publication_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Publication supprimée avec succès
      404:
        description: Publication non trouvée
      500:
        description: Erreur serveur interne
    """
    try:
        success = delete_publication(publication_id)
        if success:
            logger.info(f"Publication avec l'ID {publication_id} supprimée")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'une publication: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500