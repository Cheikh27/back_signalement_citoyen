from flask import Blueprint, request, jsonify
import logging
from app import cache
from app.services.reaction.signature_service import (
    create_signature, get_signature_by_id, get_all_signatures,
    get_signatures_by_citoyen, get_signatures_by_petition,
    update_signature, delete_signature
)
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users


# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer un Blueprint pour les routes liées à 'signature'
signature_bp = Blueprint('signature', __name__)

# Route pour créer un nouvel enregistrement
# Modifiez votre route add_signature existante

@signature_bp.route('/add', methods=['POST'])
def add_signature():
    try:
        data = request.get_json()
        required_fields = ['citoyen_id', 'petition_id']
        if not data or any(field not in data for field in required_fields):
            logger.error("Données incomplètes reçues pour créer une signature")
            return jsonify({'message': 'Données manquantes'}), 400

        logger.info(f"✍️ Tentative signature: {data}")

        try:
            nouvelle_signature = create_signature(
                citoyen_id=data['citoyen_id'],
                petition_id=data['petition_id']
            )

            send_notification(
              user_id=data['citoyen_id'],
              title="✅ Signature confirmée",
              message="Votre signature a été enregistrée avec succès",
              entity_type='petition',
              entity_id=data['petition_id'],
              priority='normal',
              category='social'
            )
            logger.info(f"✅ Nouvelle signature créée avec l'ID: {nouvelle_signature.IDsignature}")

            from app.models.signal.petition_model import Petition
            
            petition = Petition.query.get(data['petition_id'])
            
            if petition and petition.citoyenID != data['citoyen_id']:  # Pas notifier soi-même
                send_notification(
                    user_id=petition.citoyenID,
                    title="🎉 Nouvelle signature !",
                    message=f"Quelqu'un a signé votre pétition '{petition.titre}'",
                    entity_type='petition',
                    entity_id=data['petition_id'],
                    priority='normal',
                    category='social'
                )
            return jsonify({'id': nouvelle_signature.IDsignature}), 201
            
        except ValueError as ve:
            # Gestion du cas "déjà signé"
            logger.warning(f"⚠️ Signature déjà existante: {str(ve)}")
            return jsonify({'message': str(ve)}), 409

    except Exception as e:
        logger.error(f"💥 Erreur lors de la création d'une signature: {str(e)}")
        return jsonify({'message': 'Erreur serveur'}), 500
    
    
# Route pour obtenir un enregistrement par ID
@signature_bp.route('/<int:signature_id>', methods=['GET'])
@cache.cached(timeout=60, key_prefix='get_signature')
def get_signature(signature_id):
    """
    Récupère une signature spécifique via son ID.
    ---
    parameters:
      - name: signature_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Détails de la signature
      404:
        description: Signature non trouvée
    """
    logger.info(f"Récupération de la signature avec l'ID: {signature_id}")
    signature = get_signature_by_id(signature_id)
    if signature:
        return jsonify({
            'id': signature.IDsignature,
            'dateCreated': signature.dateCreated,
            # 'nbSignature': signature.nbSignature,
            'citoyen_id': signature.citoyenID,
            'petition_id': signature.petitionID
        })
    return jsonify({'message': 'Not found'}), 404

# Route pour obtenir tous les enregistrements
@signature_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signatures')
def list_signatures():
    """
    Récupère toutes les signatures enregistrées.
    ---
    responses:
      200:
        description: Liste des signatures
    """
    logger.info("Récupération de toutes les signatures")
    signatures = get_all_signatures()
    return jsonify([{
        'id': s.IDsignature,
        'dateCreated': s.dateCreated,
        # 'nbSignature': s.nbSignature,
        'citoyen_id': s.citoyenID,
        'petition_id': s.petitionID
    } for s in signatures])

# Route pour obtenir les enregistrements par citoyen
@signature_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signatures_by_citoyen')
def list_signatures_by_citoyen(citoyen_id):
    """
    Récupère toutes les signatures d'un citoyen spécifique.
    ---
    parameters:
      - name: citoyen_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des signatures
    """
    logger.info(f"Récupération des signatures pour le citoyen avec l'ID: {citoyen_id}")
    signatures = get_signatures_by_citoyen(citoyen_id)
    return jsonify([{
        'id': s.IDsignature,
        'dateCreated': s.dateCreated,
        # 'nbSignature': s.nbSignature,
        'petition_id': s.petitionID
    } for s in signatures])

# Route pour obtenir les enregistrements par pétition
@signature_bp.route('/<int:petition_id>/signatures', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signatures_by_petition')
def list_signatures_by_petition(petition_id):
    """
    Récupère toutes les signatures liées à une pétition spécifique.
    ---
    parameters:
      - name: petition_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Liste des signatures associées
    """
    logger.info(f"Récupération des signatures pour la pétition avec l'ID: {petition_id}")
    signatures = get_signatures_by_petition(petition_id)
    return jsonify([{
        'id': s.IDsignature,
        'dateCreated': s.dateCreated,
        # 'nbSignature': s.nbSignature,
        'citoyen_id': s.citoyenID
    } for s in signatures])

# Route pour mettre à jour un enregistrement
@signature_bp.route('/update/<int:signature_id>', methods=['PUT'])
def modify_signature(signature_id):
    """
    Met à jour une signature existante.
    ---
    consumes:
      - application/json
    parameters:
      - name: signature_id
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
            nb_signature:
              type: integer
              example: 1
    responses:
      200:
        description: Signature mise à jour avec succès
      400:
        description: Données incomplètes
      404:
        description: Signature non trouvée
      500:
        description: Erreur serveur
    """
    try:
        data = request.get_json()
        if not data or 'nb_signature' not in data:
            logger.error("Données incomplètes reçues pour mettre à jour une signature")
            return jsonify({'message': 'Bad Request'}), 400

        signature = update_signature(signature_id, nb_signature=data['nb_signature'])
        if signature:
            logger.info(f"Signature avec l'ID {signature_id} mise à jour")
            return jsonify({'id': signature.IDsignature}), 200
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour d'une signature: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Route pour supprimer un enregistrement
@signature_bp.route('/delete/<int:signature_id>', methods=['DELETE'])
def remove_signature(signature_id):
    """
    Supprime une signature de la base de données.
    ---
    parameters:
      - name: signature_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      204:
        description: Suppression réussie
      404:
        description: Signature non trouvée
      500:
        description: Erreur serveur
    """

    # Récupérer la signature avant suppression pour les notifications
    signature = get_signature_by_id(signature_id)
    if signature:
        # 🔔 NOTIFICATION: Signature annulée
        try:
            send_notification(
                user_id=signature.citoyenID,
                title="✍️ Signature annulée",
                message="Votre signature a été annulée",
                entity_type='petition',
                entity_id=signature.petitionID,
                priority='low',
                category='social'
            )
            
            # Notifier aussi le créateur de la pétition
            from app.models.signal.petition_model import Petition
            petition = Petition.query.get(signature.petitionID)
            
            if petition and petition.citoyenID != signature.citoyenID:
                send_notification(
                    user_id=petition.citoyenID,
                    title="📉 Signature retirée",
                    message="Une signature a été retirée de votre pétition",
                    entity_type='petition',
                    entity_id=signature.petitionID,
                    priority='low',
                    category='social'
                )
        except Exception as notif_error:
            logger.warning(f"Erreur notification suppression signature: {notif_error}")
    try:
        
        success = delete_signature(signature_id)

        if success:
            logger.info(f"Signature avec l'ID {signature_id} supprimée")
            return '', 204
        return jsonify({'message': 'Not found'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la suppression d'une signature: {str(e)}")
        return jsonify({'message': 'Internal Server Error'}), 500

# Ajoutez cette route à votre fichier signature_routes.py

@signature_bp.route('/check/<int:petition_id>/<int:user_id>', methods=['GET'])
def check_signature(petition_id, user_id):
    """
    Vérifie si un utilisateur a déjà signé une pétition.
    ---
    parameters:
      - name: petition_id
        in: path
        required: true
        type: integer
        example: 1
      - name: user_id
        in: path
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Statut de la signature
        schema:
          type: object
          properties:
            has_signed:
              type: boolean
              example: true
            signature_id:
              type: integer
              example: 1
    """
    try:
        logger.info(f"🔍 Vérification signature: petition={petition_id}, user={user_id}")
        
        # Import du service
        from app.services.reaction.signature_service import get_signature_by_petition_and_citoyen
        
        # Vérifier si l'utilisateur a signé cette pétition
        signature = get_signature_by_petition_and_citoyen(petition_id, user_id)
        
        result = {
            'has_signed': signature is not None,
            'signature_id': signature.IDsignature if signature else None
        }
        
        logger.info(f"✅ Résultat check signature: {result}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification signature: {str(e)}")
        return jsonify({
            'has_signed': False,
            'signature_id': None
        }), 200  # Retourner 200 avec False en cas d'erreur