from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.signal.petition_service import (
    create_petition, get_petition_by_id, get_all_petitions,
    get_petitions_by_citoyen, update_petition, delete_petition
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'petition'
petition_bp = Blueprint('petition', __name__)

# Route pour créer un nouvel enregistrement
@petition_bp.route('/add', methods=['POST'])
def add_petition():
    """
    Ajoute une nouvelle pétition.
    ---
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            description:
              type: string
              example: "Pétition pour améliorer les infrastructures"
            titre:
              type: string
              example: "Amélioration des routes"
            cible:
              type: string
              example: "Gouvernement"
            citoyen_id:
              type: integer
              example: 1
    responses:
      201:
        description: Pétition créée avec succès
      400:
        description: Données incomplètes
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        required_fields = ['description', 'titre', 'cible', 'citoyen_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer une pétition")
            return jsonify({'message': 'Bad Request'}), 400

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

    except Exception as e:
        logger.error(f"Erreur lors de la création d'une pétition: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@petition_bp.route('/<int:petition_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_petition')
def get_petition(petition_id):
    """
    Récupère une pétition spécifique via son ID.
    ---
    parameters:
      - name: petition_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails de la pétition
      404:
        description: Pétition non trouvée
    """
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
@cache.cached(timeout=60, key_prefix='list_petitions')
def list_petitions():
    """
    Récupère toutes les pétitions enregistrées.
    ---
    responses:
      200:
        description: Liste des pétitions
    """
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
        'cible': p.cible,
        'IDmoderateur': p.IDmoderateur,
        'citoyen_id': p.citoyenID,
        'dateCreated': p.dateCreated
    } for p in petitions])

# Route pour obtenir les enregistrements par citoyen
@petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_petitions_by_citoyen')
def list_petitions_by_citoyen(citoyen_id):
    """
    Récupère toutes les pétitions d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des pétitions
    """
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
    """
    Met à jour les informations d'une pétition existante.
    ---
    parameters:
      - name: petition_id
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
              example: "Nouvelle description de la pétition"
            nb_signature:
              type: integer
              example: 100
    responses:
      200:
        description: Pétition mise à jour avec succès
      404:
        description: Pétition non trouvée
    """
    try:
        data = request.get_json()
        if not data:
            logger.error("Données incomplètes reçues pour mettre à jour une pétition")
            return jsonify({'message': 'Bad Request'}), 400

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

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'une pétition: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@petition_bp.route('/delete/<int:petition_id>', methods=['DELETE'])
def remove_petition(petition_id):
    """
    Supprime une pétition de la base de données.
    ---
    parameters:
      - name: petition_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Pétition non trouvée
      500:
        description: Erreur serveur
    """
    try:
        success = delete_petition(petition_id)
        if success:
            logger.info(f"Pétition avec l'ID {petition_id} supprimée")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'une pétition: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
