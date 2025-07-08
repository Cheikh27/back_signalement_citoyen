from datetime import datetime
from flask import Blueprint, request, jsonify
import logging
from app import db, cache
from app.models import Petition
from app.services import (
    create_petition,
    get_petition_by_id,
    get_all_petitions,
    get_petitions_by_citoyen,
    update_petition,
    delete_petition,
    search_petition_by_keyword,
)

from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

petition_bp = Blueprint('petition', __name__)

def safe_date_format(date_value):
    """Formate une date de manière sécurisée"""
    if date_value is None:
        return None
    if isinstance(date_value, datetime):
        return date_value.isoformat()
    if isinstance(date_value, str):
        return date_value
    return str(date_value)

@petition_bp.route('/add', methods=['POST'])
def add_petition():
    try:
        logger.info("Début de la requête POST /petition/add")

        # Vérifie si c’est multipart (fichiers)
        if 'application/json' not in request.content_type:
            data = request.form.to_dict()
            media_list = []
            for key in request.files:
                file = request.files[key]
                file_data = file.read()
                media_list.append({
                    'filename': file.filename,
                    'mimetype': file.content_type,
                    'data': file_data
                })
            data['elements'] = media_list
        else:
            data = request.get_json()
            media_list = data.get('elements', [])

        logger.info("Données reçues : %s", data)

        required_fields = ['citoyen_id', 'description', 'titre', 'destinataire']
        if not data or any(field not in data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in data]
            logger.warning("Champs requis manquants : %s", missing_fields)
            return jsonify({'message': 'Champs requis manquants', 'missing_fields': missing_fields}), 400

        if not isinstance(media_list, list):
            logger.warning("Le champ 'elements' n'est pas une liste")
            return jsonify({'message': 'Le champ \"elements\" doit être une liste'}), 400

        nouvelle_petition = create_petition(
            destinataire=data['destinataire'],
            elements=media_list,
            anonymat=bool(data.get('anonymat', False)),
            description=data['description'],
            nb_signature=int(data.get('nb_signature', 0)),
            nb_partage=int(data.get('nb_partage', 0)),
            # nb_commentaire=int(data.get('nb_commentaire', 0)),
            date_fin=data.get('date_fin') if data.get('date_fin') and data.get('date_fin').strip() else None,
            objectif_signature=int(data.get('objectif_signature', 0)),
            titre=data['titre'],
            republierPar=data.get('republierPar'),
            cible=None,  # Toujours null maintenant
            id_moderateur=int(data.get('id_moderateur')) if data.get('id_moderateur') else None,
            citoyen_id=int(data['citoyen_id'])
        )

        send_notification(
            user_id=int(data['citoyen_id']),
            title="📜 Pétition créée avec succès",
            message=f"Pétition '{data['titre']}' publiée avec objectif de {data.get('objectif_signature', 0)} signatures",
            entity_type='petition',
            entity_id=nouvelle_petition.IDpetition,
            priority='normal',
            category='petition'
        )

        logger.info("Nouvelle pétition créée avec succès, ID : %s", nouvelle_petition.IDpetition)
        return jsonify({'id': nouvelle_petition.IDpetition}), 201

    except Exception as e:
        logger.error("Erreur lors de la création de la pétition : %s", str(e), exc_info=True)
        db.session.rollback()
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

@petition_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_petitions')
def list_petitions():
    petitions = get_all_petitions()
    return jsonify([{
        'id': p.IDpetition,
        'titre': p.titre,
        'description': p.description,
        'statut': p.statut,
        'objectifSignature': p.objectifSignature,
        'anonymat': p.anonymat,
        'nbSignature': p.nbSignature,
        # 'nbCommentaire': p.nbCommentaire,
        'nbPartage': p.nbPartage,
        'destinataire': p.destinataire,
        'dateFin': safe_date_format(p.dateFin),  # ✅ CORRECTION
        'republierPar': p.republierPar,
        'IDmoderateur': p.IDmoderateur,
        'citoyen_id': p.citoyenID,
        'dateCreated': p.dateCreated.isoformat() if p.dateCreated else None,
        'elements': f'/api/petition/{p.IDpetition}/fichiers'
    } for p in petitions if not p.is_deleted])

@petition_bp.route('/<int:petition_id>', methods=['GET'])
def get_petition(petition_id):
    petition = get_petition_by_id(petition_id)
    if not petition or petition.is_deleted:
        return jsonify({'message': 'Pétition introuvable'}), 404

    return jsonify({
        'id': petition.IDpetition,
        'titre': petition.titre,
        'description': petition.description,
        'statut': petition.statut,
        'nbSignature': petition.nbSignature,
        'nbPartage': petition.nbPartage,
        # 'nbCommentaire': petition.nbCommentaire,
        'objectifSignature': petition.objectifSignature,
        'anonymat': petition.anonymat,
        'destinataire': petition.destinataire,
        'dateFin': safe_date_format(petition.dateFin),  # ✅ CORRECTION
        'IDmoderateur': petition.IDmoderateur,
        'citoyen_id': petition.citoyenID,
        'republierPar': petition.republierPar,
        'dateCreated': petition.dateCreated.isoformat() if petition.dateCreated else None,
        'elements': petition.get_elements()
    })

@petition_bp.route('/<int:citoyen_id>/citoyens', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_petitions_by_citoyen')
def list_petitions_by_citoyen(citoyen_id):
    petitions = get_petitions_by_citoyen(citoyen_id)
    return jsonify([{
        'id': p.IDpetition,
        'titre': p.titre,
        'description': p.description,
        'statut': p.statut,
        'nbSignature': p.nbSignature,
        'nbPartage': p.nbPartage,
        # 'nbCommentaire': p.nbCommentaire,
        'objectifSignature': p.objectifSignature,
        'destinataire': p.destinataire,
        'dateFin': safe_date_format(p.dateFin),  # ✅ CORRECTION
        'republierPar': p.republierPar,
        'IDmoderateur': p.IDmoderateur,
        'citoyen_id': p.citoyenID,
        'dateCreated': p.dateCreated.isoformat() if p.dateCreated else None,
        'elements': f'/api/petition/{p.IDpetition}/fichiers'
    } for p in petitions if not p.is_deleted])

@petition_bp.route('/update/<int:petition_id>', methods=['PUT'])
def modify_petition(petition_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

        media_list = data.get('elements', []) if isinstance(data.get('elements'), list) else []


        petition = update_petition(
            petition_id,
            destinataire=data.get('destinataire'),
            elements=media_list,
            anonymat=data.get('anonymat'),
            description=data.get('description'),
            nb_signature=data.get('nb_signature'),
            # nb_commentaire=data.get('nb_commentaire'),
            nb_partage=data.get('nb_partage'),
            date_fin=data.get('date_fin'),
            objectif_signature=data.get('objectif_signature'),
            titre=data.get('titre'),
            republierPar=data.get('republierPar'),
            cible=data.get('cible'),
            id_moderateur=data.get('id_moderateur')
        )
        if petition:
            return jsonify({'id': petition.IDpetition}), 200
        else:
            return jsonify({'message': 'Pétition introuvable'}), 404

    except Exception as e:
        logger.error(f"Erreur PUT /update : {str(e)}")
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

@petition_bp.route('/delete/<int:petition_id>', methods=['DELETE'])
def remove_petition(petition_id):
    try:
        success = delete_petition(petition_id)
        if success:
            return '', 204
        return jsonify({'message': 'Pétition introuvable'}), 404
    except Exception as e:
        logger.error(f"Erreur DELETE : {str(e)}")
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@petition_bp.route('/search', methods=['GET'])
def search_petitions():
    query = request.args.get('q')
    if not query:
        return jsonify({'message': 'Paramètre "q" requis'}), 400

    try:
        resultats = search_petition_by_keyword(query)
        return jsonify([{
            'id': p.IDpetition,
            'titre': p.titre,
            'description': p.description,
            'statut': p.statut,
            'nbSignature': p.nbSignature,
            'nbPartage': p.nbPartage,
            # 'nbCommentaire': p.nbCommentaire,
            'objectifSignature': p.objectifSignature,
            'destinataire': p.destinataire,
            'dateFin': safe_date_format(p.dateFin),  # ✅ CORRECTION
            'republierPar': p.republierPar,
            'IDmoderateur': p.IDmoderateur,
            'citoyen_id': p.citoyenID,
            'dateCreated': p.dateCreated.isoformat() if p.dateCreated else None,
            'elements': f'/api/petition/{p.IDpetition}/fichiers'
        } for p in resultats if not p.is_deleted]), 200
    except Exception as e:
        logger.error(f"Erreur GET /search : {str(e)}")
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@petition_bp.route('/<int:petition_id>/fichiers', methods=['GET'])
def get_petition_files(petition_id):
    petition = get_petition_by_id(petition_id)
    if not petition or petition.is_deleted:
        return jsonify({'message': 'Pétition introuvable'}), 404

    try:
        media_list = petition.get_elements()
        return jsonify(media_list), 200
    except Exception as e:
        return jsonify({'message': f'Erreur lecture éléments : {str(e)}'}), 500

@petition_bp.route('/stats', methods=['GET'])
def get_petition_stats():
    try:
        total_petitions = Petition.query.filter_by(is_deleted=False).count()
        active_petitions = Petition.query.filter_by(is_deleted=False, statut='en_attente').count()
        expired_petitions = Petition.query.filter(
            Petition.is_deleted == False,
            Petition.dateFin < datetime.utcnow()
        ).count()
        
        # Stats par destinataire
        destinataire_stats = db.session.query(
            Petition.destinataire,
            db.func.count(Petition.IDpetition).label('count')
        ).filter_by(is_deleted=False).group_by(Petition.destinataire).all()
        
        return jsonify({
            'total_petitions': total_petitions,
            'active_petitions': active_petitions,
            'expired_petitions': expired_petitions,
            'destinataire_distribution': {stat.destinataire: stat.count for stat in destinataire_stats}
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur GET /stats : {str(e)}")
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500