from flask import Blueprint, request, jsonify # type: ignore
import logging
from app import cache

from app.services.autres.tutoriel_service import(
    create_tutoriel,delete_tutoriel,get_all_tutoriels,get_tutoriel_by_id,get_tutoriels_by_citoyen,update_tutoriel
)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'tutoriel'
tutoriel_bp = Blueprint('tutoriel', __name__)

# Route pour créer un nouvel enregistrement
@tutoriel_bp.route('/add', methods=['POST'])
def add_tutoriel():
    """
    Crée un nouvel enregistrement d'appartenance.
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
            citoyen_id:
              type: integer
              example: 1
            tutoriel_id:
              type: integer
              example: 1
    responses:
      201:
        description: Enregistrement créé avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
      400:
        description: Données incomplètes
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        if not data or 'citoyen_id' not in data or 'suivis' not in data:
            logger.error("Données incomplètes reçues pour créer un enregistrement d'appartenance")
            return jsonify({'message': 'Bad Request'}), 400

        nouvel_tutoriel = create_tutoriel(
            citoyen_id=data['citoyen_id'],
        )
        logger.info(f"Nouvel enregistrement d'appartenance créé avec l'ID: {nouvel_tutoriel.IDtutoriel}")
        return jsonify({'id': nouvel_tutoriel.IDtutoriel}), 201

    except Exception as e:
        logger.error(f"Erreur lors de la création d'un enregistrement d'appartenance: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour obtenir un enregistrement par ID
@tutoriel_bp.route('/<int:tutoriel_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_tutoriel')
def get_tutoriel(tutoriel_id):
    """
    Récupère un enregistrement d'appartenance par son ID.
    ---
    parameters:
      - name: tutoriel_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Enregistrement trouvé
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
            dateCreated:
              type: string
              example: "2023-10-01T00:00:00Z"
            citoyen_id:
              type: integer
              example: 1
            tutoriel_id:
              type: integer
              example: 1
      404:
        description: Enregistrement non trouvé
    """
    logger.info(f"Récupération de l'enregistrement d'appartenance avec l'ID: {tutoriel_id}")
    tutoriel = get_tutoriel_by_id(tutoriel_id)
    if tutoriel:
        return jsonify({
            'id': tutoriel.IDtutoriel,
            'dateCreated': tutoriel.dateCreated,
            'citoyen_id': tutoriel.citoyenID,
            'suivis': tutoriel.suivis
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@tutoriel_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_tutoriels')
def list_tutoriels():
    """
    Récupère tous les enregistrements d'appartenance.
    ---
    responses:
      200:
        description: Liste des enregistrements
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              dateCreated:
                type: string
                example: "2023-10-01T00:00:00Z"
              citoyen_id:
                type: integer
                example: 1
              tutoriel_id:
                type: integer
                example: 1
    """
    logger.info("Récupération de tous les enregistrements d'appartenance")
    tutoriels = get_all_tutoriels()
    return jsonify([{
        'id': a.IDtutoriel,
        'dateCreated': a.dateCreated,
        'citoyen_id': a.citoyenID,
        'suivis': a.suivis
    } for a in tutoriels])

# Route pour obtenir les enregistrements par citoyen
@tutoriel_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_tutoriels_by_citoyen')
def list_tutoriels_by_citoyen(citoyen_id):
    """
    Récupère les enregistrements d'appartenance pour un citoyen donné.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des enregistrements
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              dateCreated:
                type: string
                example: "2023-10-01T00:00:00Z"
              tutoriel_id:
                type: integer
                example: 1
    """
    logger.info(f"Récupération des enregistrements d'appartenance pour le citoyen avec l'ID: {citoyen_id}")
    tutoriels = get_tutoriels_by_citoyen(citoyen_id)
    return jsonify([{
        'id': a.IDtutoriel,
        'dateCreated': a.dateCreated,
        'suivis':a.suivis,
    } for a in tutoriels])

# Route pour obtenir les enregistrements par tutoriel
# @tutoriel_bp.route('/<int:tutoriel_id>/tutoriels', methods=['GET'])
# @cache.cached(timeout=60, key_prefix='list_tutoriels_by_tutoriel')
# def list_tutoriels_by_tutoriel(tutoriel_id):
#     """
#     Récupère les enregistrements d'appartenance pour un tutoriel donné.
#     ---
#     parameters:
#       - name: tutoriel_id
#         in: path
#         required: true
#         type: integer
#         example: 1
#     responses:
#       200:
#         description: Liste des enregistrements
#         schema:
#           type: array
#           items:
#             type: object
#             properties:
#               id:
#                 type: integer
#                 example: 1
#               dateCreated:
#                 type: string
#                 example: "2023-10-01T00:00:00Z"
#               citoyen_id:
#                 type: integer
#                 example: 1
#     """
#     logger.info(f"Récupération des enregistrements d'appartenance pour le tutoriel avec l'ID: {tutoriel_id}")
#     tutoriels = get_tutoriels_by_tutoriel(tutoriel_id)
#     return jsonify([{
#         'id': a.IDtutoriel,
#         'dateCreated': a.dateCreated,
#         'citoyen_id': a.citoyenID
#     } for a in tutoriels])

# Route pour mettre à jour un enregistrement
@tutoriel_bp.route('/update/<int:tutoriel_id>', methods=['PUT'])
def modify_tutoriel(tutoriel_id):
    """
    Met à jour un enregistrement d'appartenance.
    ---
    consumes:
      - application/json
    parameters:
      - name: tutoriel_id
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
            citoyen_id:
              type: integer
              example: 1
            tutoriel_id:
              type: integer
              example: 1
    responses:
      200:
        description: Enregistrement mis à jour avec succès
        schema:
          type: object
          properties:
            id:
              type: integer
              example: 1
      400:
        description: Données incomplètes
      404:
        description: Enregistrement non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        data = request.get_json()
        if not data or ('citoyen_id' not in data and 'tutoriel_id' not in data):
            logger.error("Données incomplètes reçues pour mettre à jour un enregistrement d'appartenance")
            return jsonify({'message': 'Bad Request'}), 400

        tutoriel = update_tutoriel(
            tutoriel_id,
            citoyen_id=data.get('citoyen_id'),
            suivis=data.get('suivis')
        )
        if tutoriel:
            logger.info(f"Enregistrement d'appartenance avec l'ID {tutoriel_id} mis à jour")
            return jsonify({'id': tutoriel.IDtutoriel}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'un enregistrement d'appartenance: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@tutoriel_bp.route('/delete/<int:tutoriel_id>', methods=['DELETE'])
def remove_tutoriel(tutoriel_id):
    """
    Supprime un enregistrement d'appartenance.
    ---
    parameters:
      - name: tutoriel_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Enregistrement supprimé avec succès
      404:
        description: Enregistrement non trouvé
      500:
        description: Erreur interne du serveur
    """
    try:
        success = delete_tutoriel(tutoriel_id)
        if success:
            logger.info(f"Enregistrement d'appartenance avec l'ID {tutoriel_id} supprimé")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'un enregistrement d'appartenance: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500
