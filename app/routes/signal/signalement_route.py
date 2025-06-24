import base64
from datetime import datetime
import logging
from flask import Blueprint, current_app, request, jsonify, send_file, abort
from io import BytesIO

from flask_jwt_extended import get_jwt_identity, jwt_required
from app import cache, db
from app.models import Signalement
from app.services import (
    create_signalement,
    get_signalement_by_id,
    get_all_signalements,
    get_signalements_by_citoyen,
    update_signalement,
    delete_signalement,
    search_signalements_by_keyword,
    get_signalement_with_fresh_urls
)
from app.supabase_media_service import SupabaseMediaService
# En haut de chaque fichier route
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users

from werkzeug.utils import secure_filename
import uuid
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

signalement_bp = Blueprint('signalement', __name__)

# Initialiser le service média
media_service = SupabaseMediaService()


# @signalement_bp.route('/add', methods=['POST'])
# def add_signalement():
#     try:
#         print("🚀 Début création signalement avec Supabase")
        
#         # Traitement des données (multipart ou JSON)
#         if 'application/json' not in request.content_type:
#             data = request.form.to_dict()
#             media_list = []
            
#             for key in request.files:
#                 file = request.files[key]
#                 if file and file.filename:
#                     file_data = file.read()
#                     media_list.append({
#                         'filename': file.filename,
#                         'mimetype': file.content_type or 'application/octet-stream',
#                         'data': file_data
#                     })
            
#             data['elements'] = media_list
#         else:
#             data = request.get_json()
#             media_list = data.get('elements', [])
        
#         # Validation des champs requis
#         required_fields = ['typeSignalement', 'description', 'cible', 'citoyen_id']
#         missing_fields = [field for field in required_fields if field not in data]
        
#         if missing_fields:
#             return jsonify({
#                 'message': 'Champs requis manquants', 
#                 'missing_fields': missing_fields
#             }), 400
        
#         # Créer le signalement avec Supabase
#         result = create_signalement(
#             citoyen_id=int(data['citoyen_id']),
#             typeSignalement=data['typeSignalement'],
#             description=data['description'],
#             elements=media_list,
#             anonymat=bool(data.get('anonymat', False)),
#             nb_vote_positif=int(data.get('nbVotePositif', 0)),
#             nb_vote_negatif=int(data.get('nbVoteNegatif', 0)),
#             cible=data['cible'],
#             republierPar=int(data['republierPar']) if data.get('republierPar') else None,
#             id_moderateur=int(data['id_moderateur']) if data.get('id_moderateur') else None
#         )
        
#         response_data = {
#             'id': result['signalement'].IDsignalement,
#             'message': 'Signalement créé avec succès',
#             'uploaded_media': result['uploaded_media'],
#             'total_media': len(media_list)
#         }
        
#         # Ajouter les avertissements si des uploads ont échoué
#         if result['failed_uploads']:
#             response_data['warnings'] = f"{len(result['failed_uploads'])} médias n'ont pas pu être uploadés"
#             response_data['failed_files'] = [f['filename'] for f in result['failed_uploads']]
        
#         return jsonify(response_data), 201
        
#     except Exception as e:
#         print(f"❌ Erreur création signalement: {e}")
#         db.session.rollback()
#         return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

@signalement_bp.route('/add', methods=['POST'])
def add_signalement():
    try:
        print("🚀 Début création signalement avec Supabase")
        
        # Traitement des données (multipart ou JSON)
        media_list = []
        data = {}
        
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            media_list = data.get('elements', [])
        else:
            # Mode multipart
            data = request.form.to_dict()
            
            # Traiter les fichiers
            for key in request.files:
                file = request.files[key]
                if file and file.filename:
                    file_content = file.read()
                    if len(file_content) > 0:
                        media_list.append({
                            'filename': file.filename,
                            'mimetype': file.content_type or 'application/octet-stream',
                            'data': file_content
                        })
            
            data['elements'] = media_list
        
        # Validation des champs requis
        required_fields = ['typeSignalement', 'description', 'cible', 'citoyen_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'message': 'Champs requis manquants', 
                'missing_fields': missing_fields
            }), 400
        
        # 🔧 CORRECTION ANONYMAT - Fonction robuste
        def parse_anonymat(value):
            """Parse la valeur anonymat de manière robuste"""
            if value is None:
                return False
            
            # Si c'est déjà un booléen
            if isinstance(value, bool):
                return value
            
            # Si c'est une chaîne (cas problématique résolu)
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes', 'oui']
            
            # Si c'est un nombre
            if isinstance(value, (int, float)):
                return bool(value)
            
            # Par défaut
            return False
        
        # Utiliser la fonction robuste pour l'anonymat
        anonymat_final = parse_anonymat(data.get('anonymat'))
        
        # Créer le signalement avec Supabase
        result = create_signalement(
            citoyen_id=int(data['citoyen_id']),
            typeSignalement=data['typeSignalement'],
            description=data['description'],
            elements=media_list,
            anonymat=anonymat_final,  # ← Utiliser la valeur corrigée
            nb_vote_positif=int(data.get('nbVotePositif', 0)),
            nb_vote_negatif=int(data.get('nbVoteNegatif', 0)),
            cible=data['cible'],
            republierPar=int(data['republierPar']) if data.get('republierPar') else None,
            id_moderateur=int(data['id_moderateur']) if data.get('id_moderateur') else None
        )
        
        send_notification(
            user_id=int(data['citoyen_id']),
            title="🚨 Signalement créé avec succès",
            message=f"Votre signalement '{data['description'][:50]}...' a été enregistré",
            entity_type='signalement',
            entity_id=result['signalement'].IDsignalement,
            priority='normal',
            category='signalement'
        )

        response_data = {
            'id': result['signalement'].IDsignalement,
            'message': 'Signalement créé avec succès',
            'uploaded_media': result['uploaded_media'],
            'total_media': len(media_list)
        }
        
        # Ajouter les avertissements si des uploads ont échoué
        if result['failed_uploads']:
            response_data['warnings'] = f"{len(result['failed_uploads'])} médias n'ont pas pu être uploadés"
            response_data['failed_files'] = [f['filename'] for f in result['failed_uploads']]
        
    
        from app.models.users.admin_model import Admin
        admins = Admin.query.filter_by(role='admin').all()
        admin_ids = [admin.IDuser for admin in admins]
        
        if admin_ids:
            send_to_multiple_users(
                user_ids=admin_ids,
                title="🔍 Nouveau signalement à modérer",
                message=f"Signalement de type '{data['typeSignalement']}' créé par citoyen #{data['citoyen_id']}",
                entity_type='signalement',
                entity_id=result['signalement'].IDsignalement,
                priority='high',
                category='moderation'
            )


        print(f"✅ Signalement créé (ID: {result['signalement'].IDsignalement}) - Anonymat: {anonymat_final}")
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"❌ Erreur création signalement: {e}")
        db.session.rollback()
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500


#------------------------------------------------------------------------
@signalement_bp.route('/<int:signalement_id>/fichiers', methods=['GET'])
def get_signalement_files_optimized(signalement_id):
    """Récupère les fichiers avec URLs optimisées pour l'affichage"""
    try:
        signalement = Signalement.query.get(signalement_id)
        
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        # Récupérer les éléments optimisés
        media_list = signalement.get_elements_optimized()
        
        # Résumé par catégorie
        summary = signalement.get_media_summary()
        
        return jsonify({
            'signalement_id': signalement_id,
            'elements': media_list,
            'summary': summary,
            'total_count': summary['total'],
            'categories': {
                'images': [m for m in media_list if m.get('category') == 'images'],
                'videos': [m for m in media_list if m.get('category') == 'videos'],
                'documents': [m for m in media_list if m.get('category') == 'documents'],
                'audios': [m for m in media_list if m.get('category') == 'audios']
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur récupération fichiers: {e}")
        return jsonify({'message': f'Erreur: {str(e)}'}), 500

@signalement_bp.route('/<int:signalement_id>/images', methods=['GET'])
def get_signalement_images(signalement_id):
    """Récupère uniquement les images d'un signalement"""
    try:
        signalement = Signalement.query.get(signalement_id)
        
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        images = signalement.get_images()
        
        return jsonify({
            'signalement_id': signalement_id,
            'images': images,
            'count': len(images)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500

@signalement_bp.route('/<int:signalement_id>/media/<category>', methods=['GET'])
def get_signalement_media_by_category(signalement_id, category):
    """Récupère les médias d'une catégorie spécifique"""
    try:
        signalement = Signalement.query.get(signalement_id)
        
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        # Valider la catégorie
        valid_categories = ['images', 'videos', 'documents', 'audios', 'others']
        if category not in valid_categories:
            return jsonify({'message': f'Catégorie invalide. Utilisez: {", ".join(valid_categories)}'}), 400
        
        media = signalement.get_media_by_category(category)
        
        return jsonify({
            'signalement_id': signalement_id,
            'category': category,
            'media': media,
            'count': len(media)
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500

@signalement_bp.route('/<int:signalement_id>', methods=['GET'])
def get_signalement_with_media_summary(signalement_id):
    """Récupère un signalement avec résumé détaillé des médias"""
    signalement = get_signalement_by_id(signalement_id)
    if not signalement or signalement.is_deleted:
        return jsonify({'message': 'Signalement introuvable'}), 404

    # Résumé des médias
    media_summary = signalement.get_media_summary()
    
    return jsonify({
        'id': signalement.IDsignalement,
        'typeSignalement': signalement.typeSignalement,
        'description': signalement.description,
        'statut': signalement.statut,
        'nbVotePositif': signalement.nbVotePositif,
        'nbVoteNegatif': signalement.nbVoteNegatif,
        'cible': signalement.cible,
        'anonymat': signalement.anonymat,
        'IDmoderateur': signalement.IDmoderateur,
        'citoyen_id': signalement.citoyenID,
        'dateCreated': signalement.dateCreated.isoformat() if signalement.dateCreated else None,
        'media_summary': media_summary,
        'has_media': signalement.has_media(),
        'media_urls': {
            'all': f'/api/signalement/{signalement_id}/fichiers',
            'images': f'/api/signalement/{signalement_id}/images',
            'videos': f'/api/signalement/{signalement_id}/media/videos',
            'documents': f'/api/signalement/{signalement_id}/media/documents'
        }
    })

@signalement_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signalements_with_media')
def list_signalements_with_media():
    """Liste tous les signalements avec informations médias"""
    signalements = get_all_signalements()
    
    return jsonify([{
        'id': s.IDsignalement,
        'typeSignalement': s.typeSignalement,
        'description': s.description,
        'statut': s.statut,
        'anonymat': s.anonymat,
        'nbVotePositif': s.nbVotePositif,
        'nbVoteNegatif': s.nbVoteNegatif,
        'cible': s.cible,
        'republierPar': s.republierPar,
        'IDmoderateur': s.IDmoderateur,
        'citoyen_id': s.citoyenID,
        'dateCreated': s.dateCreated.isoformat() if s.dateCreated else None,
        'media_summary': s.get_media_summary(),
        'has_media': s.has_media(),
        'preview_image': s.get_images()[0] if s.get_images() else None,  # Première image pour preview
        'media_urls': {
            'all': f'/api/signalement/{s.IDsignalement}/fichiers',
            'images': f'/api/signalement/{s.IDsignalement}/images'
        }
    } for s in signalements if not s.is_deleted])

@signalement_bp.route('/media/stats', methods=['GET'])
def get_media_statistics():
    """Statistiques globales des médias"""
    try:
        signalements = get_all_signalements()
        
        stats = {
            'total_signalements': len(signalements),
            'signalements_with_media': 0,
            'total_media': 0,
            'by_category': {
                'images': 0,
                'videos': 0,
                'documents': 0,
                'audios': 0,
                'others': 0
            },
            'by_type': {}
        }
        
        for signalement in signalements:
            if not signalement.is_deleted:
                summary = signalement.get_media_summary()
                
                if summary['total'] > 0:
                    stats['signalements_with_media'] += 1
                
                stats['total_media'] += summary['total']
                
                for category in stats['by_category']:
                    stats['by_category'][category] += summary.get(category, 0)
                
                # Compter par type de signalement
                type_sig = signalement.typeSignalement
                if type_sig not in stats['by_type']:
                    stats['by_type'][type_sig] = {'count': 0, 'with_media': 0}
                
                stats['by_type'][type_sig]['count'] += 1
                if summary['total'] > 0:
                    stats['by_type'][type_sig]['with_media'] += 1
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500

@signalement_bp.route('/<int:signalement_id>/refresh-urls', methods=['POST'])
def refresh_media_urls_enhanced(signalement_id):
    """Actualise les URLs avec optimisations d'affichage"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        fresh_elements = signalement.get_fresh_download_urls()
        
        return jsonify({
            'message': 'URLs actualisées avec optimisations',
            'signalement_id': signalement_id,
            'elements': fresh_elements,
            'summary': signalement.get_media_summary(),
            'refreshed_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500

# Route de debug pour tester l'affichage
@signalement_bp.route('/debug/<int:signalement_id>/media-urls', methods=['GET'])
def debug_media_urls(signalement_id):
    """Debug des URLs de médias pour résoudre les problèmes d'affichage"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        elements = signalement.get_elements()
        optimized = signalement.get_elements_optimized()
        fresh = signalement.get_fresh_download_urls()
        
        debug_info = {
            'signalement_id': signalement_id,
            'raw_elements': elements,
            'optimized_elements': optimized,
            'fresh_elements': fresh,
            'media_summary': signalement.get_media_summary(),
            'test_urls': []
        }
        
        # Tester l'accessibilité des URLs
        for element in optimized:
            url_test = {
                'filename': element.get('filename'),
                'category': element.get('category'),
                'urls': {
                    'display': element.get('display_url'),
                    'download': element.get('download_url'),
                    'thumbnail': element.get('thumbnail_url'),
                    'preview': element.get('preview_url')
                },
                'accessible': bool(element.get('url'))  # Test basique
            }
            debug_info['test_urls'].append(url_test)
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur debug: {str(e)}'}), 500
  
 

@signalement_bp.route('/<int:signalement_id>/media/<path:storage_path>', methods=['DELETE'])
def delete_media(signalement_id, storage_path):
    """Supprime un média spécifique"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        # Supprimer de Supabase
        success = media_service.delete_media(storage_path)
        
        if success:
            # Mettre à jour les métadonnées en DB
            media_list = signalement.get_elements()
            updated_list = [m for m in media_list if m.get('storage_path') != storage_path]
            signalement.set_elements(updated_list)
            
            db.session.commit()
            
            return jsonify({'message': 'Média supprimé avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500



@signalement_bp.route('/<int:citoyen_id>/signalements', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signalements_by_citoyen')
def list_signalements_by_citoyen(citoyen_id):
    signalements = get_signalements_by_citoyen(citoyen_id)
    return jsonify([{
        'id': s.IDsignalement,
        'typeSignalement': s.typeSignalement,
        'description': s.description,
        'statut': s.statut,
        'nbVotePositif': s.nbVotePositif,
        'nbVoteNegatif': s.nbVoteNegatif,
        'cible': s.cible,
        'IDmoderateur': s.IDmoderateur,
        'media_count': s.get_media_count(),
        'dateCreated': s.dateCreated.isoformat() if s.dateCreated else None,
        'elements_url': f'/api/signalement/{s.IDsignalement}/fichiers'
    } for s in signalements if not s.is_deleted])

@signalement_bp.route('/update/<int:signalement_id>', methods=['PUT'])
def modify_signalement(signalement_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

        signalement = update_signalement(
            signalement_id,
            typeSignalement=data.get('typeSignalement'),
            description=data.get('description'),
            elements=data.get('elements', []) if isinstance(data.get('elements'), list) else [],
            statut=data.get('statut'),
            nb_vote_positif=data.get('nbVotePositif'),
            nb_vote_negatif=data.get('nbVoteNegatif'),
            cible=data.get('cible'),
            id_moderateur=data.get('id_moderateur'),
            republierPar=data.get('republierPar')
        )

        if signalement:
            return jsonify({'id': signalement.IDsignalement}), 200
        else:
            return jsonify({'message': 'Signalement introuvable'}), 404

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du signalement {signalement_id} : {str(e)}", exc_info=True)
        return jsonify({'message': 'Erreur interne', 'error': str(e)}), 500

@signalement_bp.route('/delete/<int:signalement_id>', methods=['DELETE'])
def remove_signalement(signalement_id):
    try:
        success = delete_signalement(signalement_id)
        if success:
            return '', 204
        return jsonify({'message': 'Signalement introuvable'}), 404
    except Exception as e:
        logger.error(f"Erreur DELETE : {str(e)}")
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@signalement_bp.route('/search', methods=['GET'])
def search_signalements():
    query = request.args.get('q')
    if not query:
        return jsonify({'message': 'Paramètre "q" requis'}), 400

    try:
        resultats = search_signalements_by_keyword(query)
        return jsonify([{
            'id': s.IDsignalement,
            'typeSignalement': s.typeSignalement,
            'description': s.description,
            'statut': s.statut,
            'nbVotePositif': s.nbVotePositif,
            'nbVoteNegatif': s.nbVoteNegatif,
            'cible': s.cible,
            'IDmoderateur': s.IDmoderateur,
            'citoyen_id': s.citoyenID,
            'media_count': s.get_media_count(),
            'dateCreated': s.dateCreated.isoformat() if s.dateCreated else None,
            'elements_url': f'/api/signalement/{s.IDsignalement}/fichiers'
        } for s in resultats if not s.is_deleted]), 200
    except Exception as e:
        logger.error(f"Erreur GET /search : {str(e)}")
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

# Exemple Flask/FastAPI
@signalement_bp.route('/upload/republish', methods=['POST'])
def upload_republish_file():
    """Endpoint pour uploader les fichiers lors d'une republication"""
    try:
        print("📤 === UPLOAD REPUBLICATION DEBUG ===")
        
        # Vérifier qu'un fichier est présent
        if 'file' not in request.files:
            print("❌ Aucun fichier dans la requête")
            return jsonify({'error': 'Aucun fichier fourni'}), 400
            
        file = request.files['file']
        if file.filename == '':
            print("❌ Nom de fichier vide")
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Récupérer les paramètres
        user_id = request.form.get('user_id')
        original_filename = request.form.get('original_filename', file.filename)
        upload_type = request.form.get('upload_type', 'republication')
        
        print(f"📁 Fichier: {file.filename}")
        print(f"👤 User ID: {user_id}")
        print(f"📄 Original: {original_filename}")
        print(f"🔧 Type: {upload_type}")
        print(f"📊 Content-Type: {file.content_type}")
        
        if not user_id:
            return jsonify({'error': 'user_id requis'}), 400
        
        # Lire le contenu du fichier
        file.seek(0)  # ✅ IMPORTANT: Remettre le curseur au début
        file_content = file.read()
        file_size = len(file_content)
        
        print(f"📊 Taille lue: {file_size} bytes")
        
        if file_size == 0:
            return jsonify({'error': 'Fichier vide'}), 400
        
        # ✅ CORRECTION: Détecter le mimetype correctement
        mimetype = file.content_type
        if not mimetype or mimetype == 'application/octet-stream':
            import mimetypes
            detected_type, _ = mimetypes.guess_type(original_filename)
            if detected_type:
                mimetype = detected_type
            else:
                mimetype = 'application/octet-stream'
        
        print(f"🔍 Mimetype détecté: {mimetype}")
        
        # Upload vers Supabase via le service média
        try:
            metadata = media_service.upload_media(
                file_data=file_content,
                original_filename=original_filename,
                mimetype=mimetype,
                citoyen_id=int(user_id),
                upload_context='republication'  # ✅ Context spécial
            )
            
            print(f"✅ Upload Supabase réussi: {metadata}")
            
            # ✅ CORRECTION: Construire une réponse complète
            response_data = {
                'success': True,
                'filename': metadata.get('filename', original_filename),
                'mimetype': metadata.get('mimetype', mimetype),
                'size': metadata.get('size', file_size),
                'url': metadata.get('url'),
                'display_url': metadata.get('display_url', metadata.get('url')),
                'download_url': metadata.get('download_url', metadata.get('url')),
                'thumbnail_url': metadata.get('thumbnail_url'),
                'preview_url': metadata.get('preview_url'),
                'storage_path': metadata.get('storage_path'),
                'category': metadata.get('category', 'others'),
                'upload_date': metadata.get('uploaded_at'),
                'user_id': int(user_id),
                'upload_type': upload_type,
                'hash': metadata.get('hash'),
                # ✅ Flags booléens pour le frontend
                'is_image': metadata.get('is_image', False),
                'is_video': metadata.get('is_video', False),
                'is_document': metadata.get('is_document', False),
                'is_audio': metadata.get('is_audio', False)
            }
            
            print(f"📤 Réponse complète: {response_data}")
            return jsonify(response_data), 201
            
        except Exception as upload_error:
            print(f"❌ Erreur upload Supabase: {upload_error}")
            import traceback
            print(f"❌ Stack trace: {traceback.format_exc()}")
            
            return jsonify({
                'error': 'Erreur lors de l\'upload vers le stockage',
                'details': str(upload_error)
            }), 500
        
    except Exception as e:
        print(f"💥 Erreur générale upload republication: {e}")
        import traceback
        print(traceback.format_exc())
        
        return jsonify({
            'error': 'Erreur interne du serveur',
            'details': str(e)
        }), 500


@signalement_bp.route('/debug/republication/<int:signalement_id>', methods=['GET'])
def debug_republication_endpoint(signalement_id):
    """Endpoint pour tester la republication"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement:
            return jsonify({'error': 'Signalement introuvable'}), 404
        
        debug_info = {
            'signalement_id': signalement_id,
            'has_media': signalement.has_media(),
            'media_summary': signalement.get_media_summary(),
            'elements_raw': signalement.get_elements(),
            'elements_optimized': signalement.get_elements_optimized(),
            'images': signalement.get_images(),
            'videos': signalement.get_videos(),
            'documents': signalement.get_documents(),
            'media_count': signalement.get_media_count(),
            'first_image_for_preview': signalement.get_images()[0] if signalement.get_images() else None
        }
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@signalement_bp.route('/<int:signalement_id>/complete-for-republication', methods=['GET'])
def get_signalement_complete_for_republication(signalement_id):
    """Données complètes optimisées pour la republication"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement or signalement.is_deleted:
            return jsonify({'error': 'Signalement introuvable'}), 404
        
        # Récupérer toutes les données nécessaires
        media_summary = signalement.get_media_summary()
        all_media = signalement.get_elements_optimized()
        
        # URLs de téléchargement direct (sans redimensionnement)
        download_urls = []
        for media in all_media:
            # Utiliser l'URL de base sans paramètres de transformation
            base_url = media.get('url', '')
            if base_url:
                # Nettoyer les paramètres de redimensionnement
                clean_url = base_url.split('?')[0]  # Supprimer tout après le ?
                download_urls.append({
                    'filename': media.get('filename'),
                    'url': clean_url,
                    'display_url': media.get('display_url'),
                    'mimetype': media.get('mimetype'),
                    'category': media.get('category'),
                    'size': media.get('size')
                })
        
        response_data = {
            'signalement': {
                'id': signalement.IDsignalement,
                'typeSignalement': signalement.typeSignalement,
                'description': signalement.description,
                'anonymat': signalement.anonymat,
                'cible': signalement.cible,
                'citoyen_id': signalement.citoyenID,
                'dateCreated': signalement.dateCreated.isoformat() if signalement.dateCreated else None,
            },
            'media_info': {
                'has_media': signalement.has_media(),
                'summary': media_summary,
                'total_count': media_summary['total'],
                'download_urls': download_urls,  # ✅ URLs prêtes pour téléchargement
                'preview_image': signalement.get_images()[0] if signalement.get_images() else None
            },
            'republication_ready': True,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Erreur get_signalement_complete_for_republication: {e}")
        return jsonify({'error': str(e)}), 500


from app.services.notification.supabase_notification_service import send_notification  # Import à ajouter en haut

@signalement_bp.route('/update-status/<int:signalement_id>', methods=['PUT'])
@jwt_required()  # Protection JWT si nécessaire
def update_signalement_status(signalement_id):
    """
    Met à jour le statut d'un signalement avec notification automatique.
    ---
    consumes:
      - application/json
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
            statut:
              type: string
              enum: ['en_attente', 'en_cours', 'resolu', 'rejete', 'ferme']
              example: "en_cours"
            raison:
              type: string
              example: "Signalement pris en charge par les services techniques"
            moderateur_id:
              type: integer
              example: 1
    responses:
      200:
        description: Statut mis à jour avec succès
      400:
        description: Données invalides
      404:
        description: Signalement non trouvé
      403:
        description: Accès non autorisé
      500:
        description: Erreur serveur
    """
    try:
        # 1. Récupérer et valider les données
        data = request.get_json()
        if not data:
            logger.error("Données manquantes pour mise à jour statut")
            return jsonify({'message': 'Données requises'}), 400
        
        new_status = data.get('statut')
        raison = data.get('raison', '')
        moderateur_id = data.get('moderateur_id')
        
        # 2. Validation du statut
        valid_statuses = ['en_attente', 'en_cours', 'resolu', 'rejete', 'ferme']
        if not new_status or new_status not in valid_statuses:
            logger.error(f"Statut invalide: {new_status}")
            return jsonify({
                'message': 'Statut invalide', 
                'valid_statuses': valid_statuses
            }), 400
        
        # 3. Récupérer le signalement
        signalement = get_signalement_by_id(signalement_id)
        if not signalement or signalement.is_deleted:
            logger.error(f"Signalement {signalement_id} non trouvé")
            return jsonify({'message': 'Signalement non trouvé'}), 404
        
        # 4. Vérifier les permissions (optionnel)
        current_user_id = get_jwt_identity() if jwt_required else None
        # Ici vous pouvez ajouter la logique de vérification des droits
        # Par exemple: seuls les modérateurs/admins peuvent changer le statut
        
        # 5. Sauvegarder l'ancien statut pour historique
        old_status = signalement.statut
        logger.info(f"Changement statut signalement {signalement_id}: {old_status} → {new_status}")
        
        # 6. Mettre à jour le signalement
        updated_signalement = update_signalement(
            signalement_id,
            statut=new_status,
            id_moderateur=moderateur_id
        )
        
        if not updated_signalement:
            logger.error(f"Échec mise à jour signalement {signalement_id}")
            return jsonify({'message': 'Erreur mise à jour'}), 500
        
        # 7. 🔔 SYSTÈME DE NOTIFICATIONS
        try:
            # Messages personnalisés selon le statut
            status_messages = {
                'en_attente': {
                    'title': "⏳ Signalement en attente",
                    'message': "Votre signalement est en attente de traitement",
                    'priority': 'normal'
                },
                'en_cours': {
                    'title': "🔄 Signalement en cours de traitement",
                    'message': "Votre signalement est maintenant pris en charge par nos équipes",
                    'priority': 'high'
                },
                'resolu': {
                    'title': "✅ Signalement résolu !",
                    'message': "Bonne nouvelle ! Votre signalement a été résolu avec succès",
                    'priority': 'urgent'
                },
                'rejete': {
                    'title': "❌ Signalement rejeté",
                    'message': f"Votre signalement a été rejeté. {f'Raison: {raison}' if raison else ''}",
                    'priority': 'high'
                },
                'ferme': {
                    'title': "🔒 Signalement fermé",
                    'message': "Votre signalement a été fermé",
                    'priority': 'normal'
                }
            }
            
            # Envoyer la notification au créateur du signalement
            if new_status in status_messages:
                notification_data = status_messages[new_status]
                
                send_notification(
                    user_id=signalement.citoyenID,
                    title=notification_data['title'],
                    message=notification_data['message'],
                    data={
                        'old_status': old_status,
                        'new_status': new_status,
                        'raison': raison,
                        'moderateur_id': moderateur_id,
                        'signalement_type': signalement.typeSignalement,
                        'updated_at': datetime.utcnow().isoformat()
                    },
                    entity_type='signalement',
                    entity_id=signalement_id,
                    priority=notification_data['priority'],
                    category='status'
                )
                
                logger.info(f"Notification envoyée pour changement statut: {signalement_id}")
            
            # 🔥 NOTIFICATION SPÉCIALE: Si résolu, notifier aussi les abonnés
            if new_status == 'resolu':
                try:
                    # Récupérer les utilisateurs qui ont voté/commenté ce signalement
                    from app.models.reaction.vote_model import Vote
                    from app.models.commentaire.commentaireSignalement_model import CommentaireSignalement
                    
                    # IDs des utilisateurs intéressés (votants + commentateurs)
                    interested_users = set()
                    
                    votes = Vote.query.filter_by(signalementID=signalement_id, is_deleted=False).all()
                    for vote in votes:
                        if vote.citoyenID != signalement.citoyenID:  # Pas le créateur
                            interested_users.add(vote.citoyenID)
                    
                    comments = CommentaireSignalement.query.filter_by(signalementID=signalement_id).all()
                    for comment in comments:
                        if comment.citoyenID != signalement.citoyenID:  # Pas le créateur
                            interested_users.add(comment.citoyenID)
                    
                    # Notifier les utilisateurs intéressés
                    if interested_users:
                        from app.services.notification.supabase_notification_service import send_to_multiple_users
                        
                        send_to_multiple_users(
                            user_ids=list(interested_users),
                            title="🎉 Signalement résolu !",
                            message=f"Un signalement que vous avez suivi a été résolu: '{signalement.description[:50]}...'",
                            data={
                                'signalement_type': signalement.typeSignalement,
                                'resolved_at': datetime.utcnow().isoformat()
                            },
                            entity_type='signalement',
                            entity_id=signalement_id,
                            priority='normal',
                            category='social'
                        )
                        
                        logger.info(f"Notification résolution envoyée à {len(interested_users)} utilisateurs")
                
                except Exception as social_notif_error:
                    logger.warning(f"Erreur notifications sociales: {social_notif_error}")
                    # Ne pas faire échouer la requête principale
        
        except Exception as notif_error:
            logger.warning(f"Erreur système notifications: {notif_error}")
            # Les notifications ne doivent jamais faire échouer l'opération principale
        
        # 8. Nettoyer le cache si utilisé
        try:
            cache.delete(f'get_signalement::{signalement_id}')
            cache.delete('list_signalements')
        except:
            pass  # Cache optionnel
        
        # 9. Réponse de succès avec détails
        response_data = {
            'success': True,
            'message': 'Statut mis à jour avec succès',
            'signalement_id': signalement_id,
            'old_status': old_status,
            'new_status': new_status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if raison:
            response_data['raison'] = raison
        if moderateur_id:
            response_data['moderateur_id'] = moderateur_id
        
        logger.info(f"✅ Statut signalement {signalement_id} mis à jour: {old_status} → {new_status}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour statut signalement {signalement_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'message': 'Erreur interne du serveur',
            'error': str(e) if current_app.debug else 'Erreur interne'
        }), 500

