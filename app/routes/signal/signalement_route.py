from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.signal.signalement_service import (
    create_signalement, get_signalement_by_id, get_all_signalements,
    get_signalements_by_citoyen, update_signalement, delete_signalement
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'signalement'
signalement_bp = Blueprint('signalement', __name__)

# Route pour créer un nouvel enregistrement
@signalement_bp.route('/add', methods=['POST'])
def add_signalement():
    """
    Crée un nouveau signalement.
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
            - description
            - elements
            - cible
            - citoyen_id
          properties:
            description:
              type: string
              example: "Description détaillée du signalement"
            elements:
              type: string
              example: "Éléments de preuve ou contexte"
            statut:
              type: string
              example: "en_cours"
              default: "en_cours"
            nb_vote_positif:
              type: integer
              example: 0
            nb_vote_negatif:
              type: integer
              example: 0
            cible:
              type: string
              example: "Autorité ou entité ciblée"
            id_moderateur:
              type: integer
              example: 1
            citoyen_id:
              type: integer
              example: 1
    responses:
      201:
        description: Signalement créé avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur interne
    """
    try:
        data = request.get_json()
        required_fields = ['description', 'elements', 'cible', 'citoyen_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer un signalement")
            return jsonify({'message': 'Bad Request'}), 400

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
        return jsonify({'id': nouveau_signalement.IDsignalement}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@signalement_bp.route('/<int:signalement_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_signalement')
def get_signalement(signalement_id):
    """
    Récupère un signalement spécifique par son identifiant.
    ---
    parameters:
      - name: signalement_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails du signalement
      404:
        description: Signalement non trouvé
    """
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
@cache.cached(timeout=60, key_prefix='list_signalements')
def list_signalements():
    """
    Récupère tous les signalements enregistrés.
    ---
    responses:
      200:
        description: Liste de tous les signalements
    """
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
@cache.cached(timeout=60, key_prefix='list_signalements_by_citoyen')
def list_signalements_by_citoyen(citoyen_id):
    """
    Récupère tous les signalements associés à un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des signalements du citoyen
    """
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
    """
    Met à jour un signalement existant.
    ---
    parameters:
      - name: signalement_id
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
            description:
              type: string
              example: "Description mise à jour"
            elements:
              type: string
              example: "Nouveaux éléments"
            statut:
              type: string
              example: "resolu"
            nb_vote_positif:
              type: integer
              example: 5
            nb_vote_negatif:
              type: integer
              example: 2
            cible:
              type: string
              example: "Nouvelle cible"
            id_moderateur:
              type: integer
              example: 2
    responses:
      200:
        description: Signalement mis à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Signalement non trouvé
      500:
        description: Erreur serveur interne
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes reçues pour mettre à jour un signalement")
            return jsonify({'message': 'Bad Request'}), 400

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

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@signalement_bp.route('/delete/<int:signalement_id>', methods=['DELETE'])
def remove_signalement(signalement_id):
    """
    Supprime un signalement de la base de données.
    ---
    parameters:
      - name: signalement_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Signalement supprimé avec succès
      404:
        description: Signalement non trouvé
      500:
        description: Erreur serveur interne
    """
    try:
        success = delete_signalement(signalement_id)
        if success:
            logger.info(f"Signalement avec l'ID {signalement_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un signalement: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500