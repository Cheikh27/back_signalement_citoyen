import base64
from datetime import datetime
import logging
from flask import Blueprint, current_app, request, jsonify, send_file, abort
from io import BytesIO
import numpy as np
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests
from app import cache, db
from app.models import Signalement
from app.models.users.admin_model import Admin
from app.services import (
    create_signalement,
    get_signalement_by_id,
    get_all_signalements,
    get_signalements_by_citoyen,
    update_signalement,
    delete_signalement,
    search_signalements_by_keyword,
    get_signalement_with_fresh_urls,
    export_signalements_geojson,
    get_advanced_signalement_stats,
    get_hotspots_analysis,
    get_signalements_by_status_with_location,
    get_user_signalement_stats,
    get_signalements_with_location
)
from app.supabase_media_service import SupabaseMediaService
from app.services.notification.supabase_notification_service import send_notification, send_to_multiple_users
from werkzeug.utils import secure_filename
import uuid
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
signalement_bp = Blueprint('signalement', __name__)
media_service = SupabaseMediaService()

@signalement_bp.route('/add', methods=['POST'])
def add_signalement():
    """
    Crée un nouveau signalement avec validation IA, géolocalisation et médias
    """
    try:
        print("📝 === DÉBUT CRÉATION SIGNALEMENT ===")
        media_list = []
        data = {}

        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            if data:
                media_list = data.get('elements', [])
            else:
                print("❌ Données JSON vides")
                return jsonify({'error': 'Données JSON vides'}), 400
        else:
            data = request.form.to_dict()
            for key in request.files:
                file = request.files[key]
                if file and file.filename:
                    try:
                        file_content = file.read()
                        if len(file_content) > 0:
                            media_list.append({
                                'filename': secure_filename(file.filename),
                                'mimetype': file.content_type or 'application/octet-stream',
                                'data': file_content,
                                'size': len(file_content)
                            })
                    except Exception as file_error:
                        print(f"❌ Erreur lecture fichier {file.filename}: {file_error}")
                        continue

        required_fields = ['description', 'citoyen_id']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            print(f"❌ Champs manquants: {missing_fields}")
            return jsonify({
                'message': 'Champs requis manquants',
                'missing_fields': missing_fields,
            }), 400

        location_data = None
        has_location_param = str(data.get('has_location', 'false')).lower() == 'true'
        if has_location_param:
            print("📍 Traitement de la géolocalisation")
            location_fields = {
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'accuracy': data.get('accuracy'),
                'altitude': data.get('altitude'),
                'heading': data.get('heading'),
                'speed': data.get('speed'),
                'location_timestamp': data.get('location_timestamp'),
                'location_address': data.get('location_address')
            }
            if location_fields['latitude'] and location_fields['longitude']:
                try:
                    lat = float(location_fields['latitude'])
                    lng = float(location_fields['longitude'])
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        location_data = {'latitude': lat, 'longitude': lng}
                        for field, value in location_fields.items():
                            if value is not None and field not in ['latitude', 'longitude']:
                                try:
                                    if field in ['accuracy', 'altitude', 'heading', 'speed']:
                                        location_data[field] = float(value)
                                    elif field == 'location_timestamp':
                                        location_data['timestamp'] = int(value)
                                    elif field == 'location_address':
                                        location_data['address'] = str(value)
                                except (ValueError, TypeError) as e:
                                    print(f"⚠️ Impossible de convertir {field}: {value} - {e}")
                    else:
                        print(f"❌ Coordonnées GPS invalides: {lat}, {lng}")
                        return jsonify({'message': 'Coordonnées GPS invalides'}), 400
                except (ValueError, TypeError) as e:
                    print(f"❌ Erreur conversion coordonnées: {e}")
                    return jsonify({'message': 'Format de coordonnées invalide'}), 400

        try:
            citoyen_id = int(data['citoyen_id'])
            nb_vote_positif = int(data.get('nbVotePositif', 0))
            nb_vote_negatif = int(data.get('nbVoteNegatif', 0))
            anonymat_final = bool(data.get('anonymat', False))
        except (ValueError, TypeError) as e:
            print(f"❌ Erreur de conversion des données numériques: {e}")
            return jsonify({'message': 'Erreur de conversion des données numériques', 'error': str(e)}), 400

        republier_par = int(data.get('republierPar')) if data.get('republierPar') else None
        id_moderateur = int(data.get('id_moderateur')) if data.get('id_moderateur') else None

        type_signalement = None
        ai_validation_results = {}
        try:
            print("🤖 Validation IA en cours...")
            try:
                text_response = requests.post(
                    'http://localhost:5001/process_text',
                    json={'text': data['description']},
                    timeout=15
                )
                if text_response.status_code == 200:
                    text_result = text_response.json()
                    text_features = text_result.get('features')
                    ai_validation_results['text_processing'] = {
                        'success': True,
                        'features_count': len(text_features) if text_features else 0,
                        'text_length': text_result.get('text_length', 0)
                    }
                    print(f"✅ Analyse textuelle réussie: {len(text_features)} features")
                else:
                    print(f"⚠️ Erreur analyse textuelle: {text_response.status_code}")
                    text_features = None
                    ai_validation_results['text_processing'] = {
                        'success': False,
                        'error': f"HTTP {text_response.status_code}"
                    }
            except requests.exceptions.RequestException as text_error:
                print(f"⚠️ Service IA texte indisponible: {text_error}")
                text_features = None
                ai_validation_results['text_processing'] = {
                    'success': False,
                    'error': str(text_error)
                }

            media_features_list = []
            is_valid = True
            ai_validation_results['media_processing'] = []
            if media_list:
                for i, media in enumerate(media_list):
                    media_result = {'index': i, 'filename': media.get('filename', f'media_{i}')}

                    try:
                        media_payload = {}
                        if 'data' in media and media['data']:
                            if isinstance(media['data'], bytes):
                                file_data = media['data']
                            else:
                                file_data = media['data'].encode() if isinstance(media['data'], str) else media['data']

                            media_base64 = base64.b64encode(file_data).decode('utf-8')
                            mime_type = media.get('mimetype', 'application/octet-stream')
                            media_payload['base64'] = f"data:{mime_type};base64,{media_base64}"
                            print(f"📤 Envoi média {i+1} en base64: {len(file_data)} bytes")
                            media_result['method'] = 'base64_from_memory'
                        elif 'filename' in media:
                            filename = media['filename']
                            possible_paths = [
                                filename,
                                os.path.join('uploads', filename),
                                os.path.join('temp', filename),
                                os.path.join('media', filename),
                                os.path.join('static', 'uploads', filename),
                                os.path.join('../uploads', filename),
                            ]

                            file_found = False
                            for path in possible_paths:
                                if os.path.exists(path):
                                    try:
                                        with open(path, 'rb') as f:
                                            file_data = f.read()

                                        media_base64 = base64.b64encode(file_data).decode('utf-8')
                                        mime_type = media.get('mimetype', 'application/octet-stream')
                                        media_payload['base64'] = f"data:{mime_type};base64,{media_base64}"
                                        print(f"📁 Fichier trouvé: {path} ({len(file_data)} bytes)")
                                        media_result['method'] = 'file_found'
                                        media_result['found_path'] = path
                                        file_found = True
                                        break
                                    except Exception as read_error:
                                        print(f"⚠️ Erreur lecture {path}: {read_error}")
                                        continue

                            if not file_found:
                                print(f"❌ Fichier non trouvé: {filename}")
                                print(f"📂 Chemins recherchés: {possible_paths}")
                                media_result.update({
                                    'success': False,
                                    'error': f'Fichier non trouvé: {filename}',
                                    'searched_paths': possible_paths
                                })
                                ai_validation_results['media_processing'].append(media_result)
                                continue
                        else:
                            media_result.update({'success': False, 'error': 'Aucune source de données'})
                            ai_validation_results['media_processing'].append(media_result)
                            continue

                        if media['mimetype'].startswith('image'):
                            endpoint = '/process_image'
                            timeout = 30
                        elif media['mimetype'].startswith('video'):
                            endpoint = '/process_video'
                            timeout = 120
                        else:
                            media_result.update({'success': False, 'error': 'Type de média non supporté'})
                            ai_validation_results['media_processing'].append(media_result)
                            continue

                        print(f"🤖 Appel IA: {endpoint} pour {media.get('filename', f'media_{i}')}")
                        media_response = requests.post(
                            f'http://localhost:5001{endpoint}',
                            json=media_payload,
                            timeout=timeout,
                            headers={'Content-Type': 'application/json'}
                        )

                        if media_response.status_code == 200:
                            media_data = media_response.json()
                            if 'features' in media_data:
                                media_features_list.append(media_data['features'])
                                media_result.update({
                                    'success': True,
                                    'features_count': len(media_data['features']),
                                    'processing_info': {
                                        'status': media_data.get('status'),
                                        'image_size': media_data.get('image_size'),
                                        'video_info': media_data.get('video_info')
                                    }
                                })
                                print(f"✅ Média {i+1} traité avec succès: {len(media_data['features'])} features")
                            else:
                                media_result.update({'success': False, 'error': 'Pas de features retournées'})
                                print(f"⚠️ Média {i+1}: pas de features dans la réponse")
                        else:
                            error_msg = f"HTTP {media_response.status_code}"
                            try:
                                error_detail = media_response.json().get('error', 'Erreur inconnue')
                                error_msg += f": {error_detail}"
                            except:
                                try:
                                    error_msg += f": {media_response.text[:200]}"
                                except:
                                    pass

                            media_result.update({'success': False, 'error': error_msg})
                            print(f"❌ Erreur IA média {i+1}: {error_msg}")

                    except requests.exceptions.Timeout:
                        media_result.update({'success': False, 'error': 'Timeout - traitement trop long'})
                        print(f"⏱️ Timeout média {i+1}")

                    except requests.exceptions.RequestException as media_error:
                        media_result.update({'success': False, 'error': f'Erreur réseau: {str(media_error)}'})
                        print(f"🌐 Erreur réseau média {i+1}: {media_error}")

                    except Exception as unexpected_error:
                        media_result.update({'success': False, 'error': f'Erreur inattendue: {str(unexpected_error)}'})
                        print(f"💥 Erreur inattendue média {i+1}: {unexpected_error}")

                    ai_validation_results['media_processing'].append(media_result)

            if text_features and media_features_list:
                try:
                    media_features = np.mean(media_features_list, axis=0).tolist()
                    validation_response = requests.post(
                        'http://localhost:5001/validate',
                        json={
                            'text_features': text_features,
                            'media_features': media_features,
                            'mode': current_app.config.get('AI_VALIDATION_MODE', 'normal')
                        },
                        timeout=15
                    )
                    if validation_response.status_code == 200:
                        validation_data = validation_response.json()
                        is_valid = validation_data.get('is_valid', True)

                        ai_validation_results['coherence_check'] = {
                            'success': True,
                            'is_valid': is_valid,
                            'similarity_score': validation_data.get('similarity_score'),
                            'confidence': validation_data.get('confidence'),
                            'threshold_used': validation_data.get('threshold_used')
                        }

                        print(f"🔍 Validation cohérence: {'✅ Valide' if is_valid else '❌ Non valide'}")
                        print(f"   Similarité: {validation_data.get('similarity_score', 'N/A')}")
                        print(f"   Confiance: {validation_data.get('confidence', 'N/A')}")
                    else:
                        ai_validation_results['coherence_check'] = {
                            'success': False,
                            'error': f"HTTP {validation_response.status_code}"
                        }
                except Exception as validation_error:
                    print(f"⚠️ Erreur validation cohérence: {validation_error}")
                    ai_validation_results['coherence_check'] = {
                        'success': False,
                        'error': str(validation_error)
                    }

            if text_features and (not media_features_list or is_valid):
                try:
                    if media_features_list:
                        combined_features = text_features + np.mean(media_features_list, axis=0).tolist()
                    else:
                        combined_features = text_features

                    categorize_response = requests.post(
                        'http://localhost:5001/categorize',
                        json={
                            'features': combined_features,
                            'text': data['description']
                        },
                        timeout=15
                    )

                    if categorize_response.status_code == 200:
                        categorize_data = categorize_response.json()
                        type_signalement = categorize_data.get('category', 'Autres')

                        ai_validation_results['categorization'] = {
                            'success': True,
                            'predicted_category': type_signalement,
                            'confidence': categorize_data.get('confidence'),
                            'all_scores': categorize_data.get('all_scores'),
                            'feature_magnitude': categorize_data.get('feature_magnitude')
                        }

                        print(f"🎯 Catégorie IA: {type_signalement}")
                        print(f"   Confiance: {categorize_data.get('confidence', 'N/A')}")
                    else:
                        ai_validation_results['categorization'] = {
                            'success': False,
                            'error': f"HTTP {categorize_response.status_code}"
                        }
                except Exception as categorize_error:
                    print(f"⚠️ Erreur catégorisation: {categorize_error}")
                    ai_validation_results['categorization'] = {
                        'success': False,
                        'error': str(categorize_error)
                    }

            if not type_signalement:
                description_lower = data['description'].lower()

                keyword_categories = {
                    'Voirie & Transports': ['route', 'trou', 'circulation', 'transport', 'feu', 'signalisation', 'nid', 'poule'],
                    'Propreté': ['déchet', 'ordure', 'sale', 'poubelle', 'nettoyer', 'caniveau'],
                    'Sécurité': ['danger', 'sécurité', 'vol', 'éclairage', 'lampadaire', 'agression'],
                    'Espaces Verts': ['arbre', 'parc', 'jardin', 'vert', 'fleur', 'herbe'],
                    'Environnement': ['pollution', 'bruit', 'eau', 'air', 'environnement', 'nuisance'],
                    'Services Publics': ['administration', 'mairie', 'service', 'public'],
                    'Animalier': ['animal', 'chien', 'chat', 'errant', 'abandon'],
                    'Urbanisme': ['construction', 'bâtiment', 'permis', 'urbanisme'],
                    'Social & Solidarité': ['aide', 'social', 'solidarité', 'pauvreté']
                }

                for category, keywords in keyword_categories.items():
                    if any(keyword in description_lower for keyword in keywords):
                        type_signalement = category
                        ai_validation_results['fallback_categorization'] = {
                            'used': True,
                            'method': 'keyword_matching',
                            'category': category,
                            'matched_keywords': [kw for kw in keywords if kw in description_lower]
                        }
                        print(f"🔍 Catégorie détectée par mots-clés: {category}")
                        break

                if not type_signalement:
                    type_signalement = "Autres"
                    ai_validation_results['fallback_categorization'] = {
                        'used': True,
                        'method': 'default',
                        'category': 'Autres'
                    }

            strict_validation = current_app.config.get('STRICT_AI_VALIDATION', False)
            if strict_validation and not is_valid:
                ai_validation_results['strict_validation_failed'] = True
                return jsonify({
                    'message': 'La description et les médias ne correspondent pas selon l\'analyse IA.',
                    'ai_validation': ai_validation_results,
                    'strict_mode': True
                }), 400

        except Exception as ai_error:
            print(f"⚠️ Service IA complètement indisponible: {ai_error}")
            import traceback
            print(f"Stack trace IA: {traceback.format_exc()}")

            type_signalement = "Autres"
            ai_validation_results = {
                'service_available': False,
                'error': str(ai_error),
                'fallback_mode': True
            }


        # Calcul de la priorité
        priority_data = {
            'type_signalement': type_signalement,
            'description': data['description'],
            'media_list': []
        }

        for media in media_list:
            if 'data' in media and isinstance(media['data'], bytes):
                # Convertir les données binaires en base64
                media_base64 = base64.b64encode(media['data']).decode('utf-8')
                priority_data['media_list'].append({
                    'filename': media.get('filename'),
                    'mimetype': media.get('mimetype'),
                    'data': media_base64,  # Envoyer la version base64
                    'size': media.get('size')
                })
            else:
                priority_data['media_list'].append(media)

        # Envoyer les données converties
        priority_response = requests.post(
            'http://localhost:5002/calculate_priority',
            json=priority_data,
            timeout=15
        )

        if priority_response.status_code == 200:
            priority = priority_response.json().get('priority', 'Moyenne')
        else:
            priority = 'Moyenne'

        result = create_signalement(
            citoyen_id=citoyen_id,
            typeSignalement=type_signalement,
            description=data['description'],
            elements=media_list,
            anonymat=anonymat_final,
            nb_vote_positif=nb_vote_positif,
            nb_vote_negatif=nb_vote_negatif,
            cible=data.get('cible', 'public'),
            republierPar=republier_par,
            id_moderateur=id_moderateur,
            location_data=location_data,
            priorite=priority
        )

        if not result or 'signalement' not in result:
            print("❌ Erreur lors de la création du signalement")
            return jsonify({'message': 'Erreur lors de la création du signalement'}), 500

        response_data = {
            'id': result['signalement'].IDsignalement,
            'message': 'Signalement créé avec succès',
            'type_signalement': type_signalement,
            'uploaded_media': result.get('uploaded_media', 0),
            'total_media': len(media_list),
            'has_location': result['signalement'].has_location,
            'status': result['signalement'].statut,
            'created_at': result['signalement'].dateCreated.isoformat() if result['signalement'].dateCreated else None,
            'priority': priority,
            'ai_analysis': ai_validation_results,
            'ai_validation_details': ai_validation_results if current_app.debug else None
        }

        if result['signalement'].has_location:
            try:
                gps_info = result['signalement'].get_location_data()
                response_data['location'] = {
                    'coordinates': gps_info.get('coordinates_string'),
                    'accuracy': gps_info.get('accuracy'),
                    'maps_url': result['signalement'].get_google_maps_url()
                }
            except Exception as location_error:
                print(f"⚠️ Erreur récupération données GPS: {location_error}")

        if result.get('failed_uploads'):
            response_data['warnings'] = f"{len(result['failed_uploads'])} médias n'ont pas pu être uploadés"
            response_data['failed_files'] = [f.get('filename', 'Fichier inconnu') for f in result['failed_uploads']]

        try:
            send_notification(
                user_id=citoyen_id,
                title="Signalement créé avec succès",
                message=f"Votre signalement '{data['description'][:50]}...' a été enregistré",
                entity_type='signalement',
                entity_id=result['signalement'].IDsignalement,
                priority='normal',
                category='signalement'
            )
            print("✅ Notification utilisateur envoyée")
        except Exception as notif_error:
            print(f"⚠️ Erreur notification utilisateur: {notif_error}")

        try:
            admins = Admin.query.filter_by(role='admin').all()
            admin_ids = [admin.IDuser for admin in admins]
            if admin_ids:
                admin_message = f"Signalement de type '{type_signalement}' créé par citoyen #{citoyen_id}"
                if location_data:
                    admin_message += " (avec localisation GPS)"

                send_to_multiple_users(
                    user_ids=admin_ids,
                    title="Nouveau signalement à modérer",
                    message=admin_message,
                    entity_type='signalement',
                    entity_id=result['signalement'].IDsignalement,
                    priority='high',
                    category='moderation'
                )
                print(f"✅ Notifications admin envoyées à {len(admin_ids)} utilisateurs")
        except Exception as admin_notif_error:
            print(f"⚠️ Erreur notifications admin: {admin_notif_error}")

        print(f"✅ Signalement {result['signalement'].IDsignalement} créé avec succès")
        return jsonify(response_data), 201

    except Exception as e:
        print(f"💥 ERREUR CRITIQUE création signalement: {e}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")

        try:
            db.session.rollback()
        except Exception as db_error:
            print(f"⚠️ Erreur rollback base de données: {db_error}")

        return jsonify({
            'message': 'Erreur interne du serveur',
            'error': str(e) if current_app.debug else 'Une erreur est survenue'
        }), 500



@signalement_bp.route('/<int:signalement_id>/location', methods=['GET'])
def get_signalement_location(signalement_id):
    """Récupère les informations de localisation d'un signalement"""
    try:
        signalement = Signalement.query.get(signalement_id)
        
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        if not signalement.has_location:
            return jsonify({
                'signalement_id': signalement_id,
                'has_location': False,
                'message': 'Aucune localisation disponible pour ce signalement'
            }), 200
        
        location_data = signalement.get_location_data()
        
        return jsonify({
            'signalement_id': signalement_id,
            'has_location': True,
            'location': location_data,
            'google_maps_url': signalement.get_google_maps_url(),
            'is_valid': signalement.is_location_valid()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500
    

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

# Dans votre route get_signalement_with_media_summary, remplacez le return par :

@signalement_bp.route('/<int:signalement_id>', methods=['GET'])
def get_signalement_with_media_summary(signalement_id):
    """Récupère un signalement avec résumé détaillé des médias et localisation"""
    signalement = get_signalement_by_id(signalement_id)
    if not signalement or signalement.is_deleted:
        return jsonify({'message': 'Signalement introuvable'}), 404

    # Résumé des médias
    media_summary = signalement.get_media_summary()
    
    # Données de localisation
    location_info = None
    if signalement.has_location:
        location_data = signalement.get_location_data()
        location_info = {
            'has_location': True,
            'coordinates': location_data.get('coordinates_string'),
            'latitude': location_data.get('latitude'),
            'longitude': location_data.get('longitude'),
            'accuracy': location_data.get('accuracy'),
            'address': location_data.get('address'),
            'google_maps_url': signalement.get_google_maps_url(),
            'is_valid': signalement.is_location_valid()
        }
    else:
        location_info = {'has_location': False}
    
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
        'location': location_info,  # ← AJOUT LOCALISATION
        'media_summary': media_summary,
        'has_media': signalement.has_media(),
        'media_urls': {
            'all': f'/api/signalement/{signalement_id}/fichiers',
            'images': f'/api/signalement/{signalement_id}/images',
            'videos': f'/api/signalement/{signalement_id}/media/videos',
            'documents': f'/api/signalement/{signalement_id}/media/documents'
        }
    })


# Dans votre route list_signalements_with_media, remplacez le return par :

@signalement_bp.route('/all', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signalements_with_media')
def list_signalements_with_media():
    """Liste tous les signalements avec informations médias et localisation"""
    signalements = get_all_signalements()
    
    result = []
    for s in signalements:
        if not s.is_deleted:
            # Informations de base
            signalement_data = {
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
                'priorite': s.priorite,
                'media_summary': s.get_media_summary(),
                'has_media': s.has_media(),
                'preview_image': s.get_images()[0] if s.get_images() else None,
                'media_urls': {
                    'all': f'/api/signalement/{s.IDsignalement}/fichiers',
                    'images': f'/api/signalement/{s.IDsignalement}/images'
                }
            }
            
            # ========== AJOUT LOCALISATION ==========
            if s.has_location:
                location_data = s.get_location_data()
                signalement_data['location'] = {
                    'has_location': True,
                    'coordinates': location_data.get('coordinates_string'),
                    'accuracy': location_data.get('accuracy'),
                    'maps_url': s.get_google_maps_url()
                }
            else:
                signalement_data['location'] = {'has_location': False}
            
            result.append(signalement_data)
    
    return jsonify(result)


# ========== NOUVELLES ROUTES GÉOGRAPHIQUES ==========

@signalement_bp.route('/by-location', methods=['GET'])
def get_signalements_by_location():
    """Récupère les signalements dans un rayon donné"""
    try:
        # Paramètres de la requête
        latitude = request.args.get('lat', type=float)
        longitude = request.args.get('lng', type=float)
        radius_km = request.args.get('radius', default=5, type=float)
        
        if not latitude or not longitude:
            return jsonify({
                'message': 'Paramètres lat et lng requis',
                'example': '/api/signalement/by-location?lat=14.6928&lng=-17.4467&radius=10'
            }), 400
        
        # Valider les coordonnées
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({'message': 'Coordonnées GPS invalides'}), 400
        
        # Limiter le rayon à 100km max
        if radius_km > 100:
            radius_km = 100
        
        signalements = get_signalements_by_location(latitude, longitude, radius_km)
        
        result = []
        for s in signalements:
            location_data = s.get_location_data()
            distance = s.calculate_distance_from(latitude, longitude)
            
            result.append({
                'id': s.IDsignalement,
                'typeSignalement': s.typeSignalement,
                'description': s.description,
                'statut': s.statut,
                'dateCreated': s.dateCreated.isoformat() if s.dateCreated else None,
                'location': {
                    'coordinates': location_data.get('coordinates_string'),
                    'distance_meters': round(distance) if distance else None,
                    'accuracy': location_data.get('accuracy')
                },
                'media_count': s.get_media_count(),
                'has_media': s.has_media()
            })
        
        # Trier par distance
        result.sort(key=lambda x: x['location']['distance_meters'] or float('inf'))
        
        return jsonify({
            'search_center': {'latitude': latitude, 'longitude': longitude},
            'search_radius_km': radius_km,
            'found_count': len(result),
            'signalements': result
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@signalement_bp.route('/location-stats', methods=['GET'])
def get_location_statistics():
    """Statistiques sur l'utilisation de la géolocalisation"""
    try:
        stats = get_location_statistics()
        
        return jsonify({
            'location_usage': stats,
            'summary': f"{stats['location_usage_rate']}% des signalements incluent une localisation GPS"
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@signalement_bp.route('/map-data', methods=['GET'])
def get_map_data():
    """Données optimisées pour affichage sur carte"""
    try:
        signalements = get_signalements_with_location()
        
        map_points = []
        for s in signalements:
            if s.is_location_valid():
                location_data = s.get_location_data()
                
                map_points.append({
                    'id': s.IDsignalement,
                    'lat': location_data['latitude'],
                    'lng': location_data['longitude'],
                    'type': s.typeSignalement,
                    'statut': s.statut,
                    'description': s.description[:100] + '...' if len(s.description) > 100 else s.description,
                    'date': s.dateCreated.isoformat() if s.dateCreated else None,
                    'accuracy': location_data.get('accuracy'),
                    'has_media': s.has_media(),
                    'media_count': s.get_media_count()
                })
        
        # Grouper par type pour la légende
        type_counts = {}
        for point in map_points:
            type_sig = point['type']
            type_counts[type_sig] = type_counts.get(type_sig, 0) + 1
        
        return jsonify({
            'points': map_points,
            'total_points': len(map_points),
            'types_legend': type_counts,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500
    
    

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



# Remplacez votre route list_signalements_by_citoyen par celle-ci :

@signalement_bp.route('/<int:citoyen_id>/signalements', methods=['GET'])
@cache.cached(timeout=60, key_prefix='list_signalements_by_citoyen')
def list_signalements_by_citoyen(citoyen_id):
    """Liste les signalements d'un citoyen avec informations de localisation"""
    try:
        signalements = get_signalements_by_citoyen(citoyen_id)
        
        # Paramètres optionnels
        include_location = request.args.get('include_location', 'true').lower() == 'true'
        location_only = request.args.get('location_only', 'false').lower() == 'true'
        
        # Filtrer si on veut seulement ceux avec localisation
        if location_only:
            signalements = [s for s in signalements if s.has_location]
        
        response_data = []
        location_stats = {'with_location': 0, 'without_location': 0}
        
        for s in signalements:
            if not s.is_deleted:
                item_data = {
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
                }
                
                # ========== INFORMATIONS DE LOCALISATION ==========
                if include_location:
                    if s.has_location:
                        location_data = s.get_location_data()
                        item_data['location'] = {
                            'has_location': True,
                            'coordinates': location_data.get('coordinates_string'),
                            'accuracy': location_data.get('accuracy'),
                            'maps_url': s.get_google_maps_url(),
                            'captured_at': location_data.get('timestamp')
                        }
                        location_stats['with_location'] += 1
                    else:
                        item_data['location'] = {'has_location': False}
                        location_stats['without_location'] += 1
                
                response_data.append(item_data)
        
        # ========== STATISTIQUES UTILISATEUR ==========
        user_stats = get_user_signalement_stats(citoyen_id)
        
        # Ajouter les stats de localisation
        if include_location:
            total = location_stats['with_location'] + location_stats['without_location']
            user_stats['location_usage'] = {
                'total_signalements': total,
                'with_location': location_stats['with_location'],
                'without_location': location_stats['without_location'],
                'location_rate': round((location_stats['with_location'] / total * 100), 2) if total > 0 else 0
            }
        
        return jsonify({
            'citoyen_id': citoyen_id,
            'total_signalements': len(response_data),
            'filters_applied': {
                'include_location': include_location,
                'location_only': location_only
            },
            'user_statistics': user_stats,
            'signalements': response_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500
# Remplacez votre route modify_signalement par celle-ci :

@signalement_bp.route('/update/<int:signalement_id>', methods=['PUT'])
def modify_signalement(signalement_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données manquantes'}), 400

        # ========== TRAITEMENT DE LA GÉOLOCALISATION ==========
        location_data = None
        location_update = data.get('location_update', False)
        
        if location_update:
            print("📍 Mise à jour de la localisation demandée")
            
            # Si on veut supprimer la localisation
            if data.get('remove_location', False):
                location_data = 'REMOVE'
                print("🗑️ Suppression de la localisation")
            
            # Si on veut ajouter/modifier la localisation
            elif data.get('location'):
                location_info = data['location']
                
                if location_info.get('latitude') and location_info.get('longitude'):
                    try:
                        lat = float(location_info['latitude'])
                        lng = float(location_info['longitude'])
                        
                        if -90 <= lat <= 90 and -180 <= lng <= 180:
                            location_data = {
                                'latitude': lat,
                                'longitude': lng,
                                'accuracy': float(location_info.get('accuracy', 0)) if location_info.get('accuracy') else None,
                                'altitude': float(location_info.get('altitude', 0)) if location_info.get('altitude') else None,
                                'heading': float(location_info.get('heading', 0)) if location_info.get('heading') else None,
                                'speed': float(location_info.get('speed', 0)) if location_info.get('speed') else None,
                                'timestamp': int(location_info.get('timestamp', 0)) if location_info.get('timestamp') else None,
                                'address': location_info.get('address')
                            }
                            print(f"✅ Nouvelles coordonnées: {lat}, {lng}")
                        else:
                            return jsonify({'message': 'Coordonnées GPS invalides'}), 400
                    except (ValueError, TypeError):
                        return jsonify({'message': 'Format de coordonnées invalide'}), 400

        # ========== APPEL DU SERVICE DE MISE À JOUR ==========
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
            republierPar=data.get('republierPar'),
            location_data=location_data  # ← AJOUT LOCALISATION
        )

        if signalement:
            # Préparer la réponse avec les nouvelles données
            response_data = {
                'id': signalement.IDsignalement,
                'message': 'Signalement mis à jour avec succès',
                'updated_fields': []
            }
            
            # Indiquer quels champs ont été mis à jour
            for field in ['typeSignalement', 'description', 'statut', 'cible']:
                if data.get(field) is not None:
                    response_data['updated_fields'].append(field)
            
            # Informations de localisation dans la réponse
            if location_update:
                if location_data == 'REMOVE':
                    response_data['location'] = {'has_location': False, 'action': 'removed'}
                elif location_data:
                    location_response = signalement.get_location_data()
                    response_data['location'] = {
                        'has_location': True,
                        'action': 'updated',
                        'coordinates': location_response.get('coordinates_string'),
                        'maps_url': signalement.get_google_maps_url()
                    }
                response_data['updated_fields'].append('location')
            
            return jsonify(response_data), 200
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

# Remplacez votre route search_signalements par celle-ci :

@signalement_bp.route('/search', methods=['GET'])
def search_signalements():
    query = request.args.get('q')
    if not query:
        return jsonify({'message': 'Paramètre "q" requis'}), 400

    # ========== PARAMÈTRES DE RECHERCHE GÉOGRAPHIQUE ==========
    latitude = request.args.get('lat', type=float)
    longitude = request.args.get('lng', type=float)
    radius_km = request.args.get('radius', default=10, type=float)
    location_only = request.args.get('location_only', 'false').lower() == 'true'

    try:
        # Recherche textuelle normale
        resultats = search_signalements_by_keyword(query)
        
        # ========== FILTRAGE GÉOGRAPHIQUE ==========
        if latitude and longitude and (-90 <= latitude <= 90) and (-180 <= longitude <= 180):
            print(f"🗺️ Recherche géographique: {latitude}, {longitude} (rayon: {radius_km}km)")
            
            # Filtrer les résultats par proximité géographique
            resultats_geo = []
            for signalement in resultats:
                if signalement.has_location:
                    try:
                        distance = signalement.calculate_distance_from(latitude, longitude)
                        distance_km = distance / 1000 if distance else float('inf')
                        
                        if distance_km <= radius_km:
                            resultats_geo.append({
                                'signalement': signalement,
                                'distance_km': round(distance_km, 2),
                                'distance_meters': round(distance) if distance else None
                            })
                    except:
                        continue
            
            # Trier par distance
            resultats_geo.sort(key=lambda x: x['distance_km'])
            
            # Formater la réponse avec distances
            response_data = []
            for item in resultats_geo:
                s = item['signalement']
                location_data = s.get_location_data()
                
                response_data.append({
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
                    'elements_url': f'/api/signalement/{s.IDsignalement}/fichiers',
                    'location': {
                        'has_location': True,
                        'coordinates': location_data.get('coordinates_string'),
                        'distance_km': item['distance_km'],
                        'distance_meters': item['distance_meters'],
                        'maps_url': s.get_google_maps_url()
                    }
                })
            
            return jsonify({
                'search_query': query,
                'search_center': {'latitude': latitude, 'longitude': longitude},
                'search_radius_km': radius_km,
                'total_found': len(response_data),
                'results': response_data
            }), 200
        
        # ========== RECHERCHE SANS GÉOLOCALISATION ==========
        # Si on veut seulement les signalements avec localisation
        if location_only:
            resultats = [s for s in resultats if s.has_location]
        
        response_data = []
        for s in resultats:
            item_data = {
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
            }
            
            # Ajouter les informations de localisation si disponibles
            if s.has_location:
                location_data = s.get_location_data()
                item_data['location'] = {
                    'has_location': True,
                    'coordinates': location_data.get('coordinates_string'),
                    'maps_url': s.get_google_maps_url()
                }
            else:
                item_data['location'] = {'has_location': False}
            
            response_data.append(item_data)
        
        return jsonify({
            'search_query': query,
            'location_only': location_only,
            'total_found': len(response_data),
            'results': response_data
        }), 200
        
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

# Ajoutez cette route à la fin de votre fichier routes


@signalement_bp.route('/export/geojson', methods=['GET'])
def export_geojson():
    """Exporte les signalements au format GeoJSON"""
    try:
        include_private = request.args.get('include_private', 'false').lower() == 'true'
        
        geojson_data = export_signalements_geojson(include_private)
        
        # Préparer la réponse avec les bons headers
        response = jsonify(geojson_data)
        response.headers['Content-Type'] = 'application/geo+json'
        response.headers['Content-Disposition'] = f'attachment; filename=signalements_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.geojson'
        
        return response, 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur export: {str(e)}'}), 500


@signalement_bp.route('/hotspots', methods=['GET'])
def get_hotspots():
    """Analyse des zones à forte concentration de signalements"""
    try:
        min_signalements = request.args.get('min_count', default=3, type=int)
        radius_km = request.args.get('radius', default=1, type=float)
        
        # Limites raisonnables
        min_signalements = max(2, min(min_signalements, 20))
        radius_km = max(0.1, min(radius_km, 10))
        
        hotspots = get_hotspots_analysis(min_signalements, radius_km)
        
        return jsonify({
            'search_parameters': {
                'min_signalements': min_signalements,
                'radius_km': radius_km
            },
            'hotspots_found': len(hotspots),
            'hotspots': hotspots,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@signalement_bp.route('/stats/advanced', methods=['GET'])
def get_advanced_stats():
    """Statistiques avancées incluant la géolocalisation"""
    try:
        stats = get_advanced_signalement_stats()
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'message': f'Erreur: {str(e)}'}), 500
    
# Ajoutez cette nouvelle route pour corriger la localisation

@signalement_bp.route('/<int:signalement_id>/move-location', methods=['PUT'])
def move_signalement_location(signalement_id):
    """Corrige ou déplace la localisation d'un signalement"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Données requises'}), 400
        
        signalement = Signalement.query.get(signalement_id)
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        # Vérifier les nouvelles coordonnées
        new_latitude = data.get('latitude')
        new_longitude = data.get('longitude')
        
        if not new_latitude or not new_longitude:
            return jsonify({'message': 'Latitude et longitude requises'}), 400
        
        try:
            lat = float(new_latitude)
            lng = float(new_longitude)
            
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return jsonify({'message': 'Coordonnées GPS invalides'}), 400
        
        except (ValueError, TypeError):
            return jsonify({'message': 'Format de coordonnées invalide'}), 400
        
        # Sauvegarder l'ancienne position pour l'historique
        old_location = None
        if signalement.has_location:
            old_location = signalement.get_location_data()
        
        # Préparer les nouvelles données de localisation
        new_location_data = {
            'latitude': lat,
            'longitude': lng,
            'accuracy': float(data.get('accuracy', 0)) if data.get('accuracy') else None,
            'altitude': float(data.get('altitude', 0)) if data.get('altitude') else None,
            'address': data.get('address'),
            'timestamp': int(data.get('timestamp', 0)) if data.get('timestamp') else None
        }
        
        # Raison du déplacement (optionnel)
        move_reason = data.get('reason', 'Correction de localisation')
        
        # Mettre à jour la localisation
        success = signalement.set_location_data(new_location_data)
        
        if success:
            db.session.commit()
            
            # Calculer la distance déplacée si ancienne position existe
            distance_moved = None
            if old_location:
                distance_moved = signalement.calculate_distance_from(
                    old_location['latitude'], 
                    old_location['longitude']
                )
            
            # Log de l'action
            print(f"📍 Signalement {signalement_id} déplacé:")
            if old_location:
                print(f"   Ancien: {old_location.get('coordinates_string')}")
                print(f"   Nouveau: {lat}, {lng}")
                if distance_moved:
                    print(f"   Distance: {round(distance_moved)}m")
            else:
                print(f"   Nouvelle position: {lat}, {lng}")
            print(f"   Raison: {move_reason}")
            
            response_data = {
                'success': True,
                'message': 'Localisation mise à jour avec succès',
                'signalement_id': signalement_id,
                'new_location': {
                    'coordinates': f"{lat}, {lng}",
                    'maps_url': signalement.get_google_maps_url(),
                    'accuracy': new_location_data.get('accuracy')
                },
                'move_info': {
                    'reason': move_reason,
                    'moved_at': datetime.utcnow().isoformat()
                }
            }
            
            # Ajouter les infos de déplacement si applicable
            if old_location and distance_moved:
                response_data['move_info'].update({
                    'old_coordinates': old_location.get('coordinates_string'),
                    'distance_moved_meters': round(distance_moved),
                    'had_previous_location': True
                })
            else:
                response_data['move_info']['had_previous_location'] = False
            
            return jsonify(response_data), 200
            
        else:
            return jsonify({'message': 'Erreur lors de la mise à jour de la localisation'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur: {str(e)}'}), 500


@signalement_bp.route('/<int:signalement_id>/remove-location', methods=['DELETE'])
def remove_signalement_location(signalement_id):
    """Supprime la localisation d'un signalement"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement or signalement.is_deleted:
            return jsonify({'message': 'Signalement introuvable'}), 404
        
        if not signalement.has_location:
            return jsonify({'message': 'Ce signalement n\'a pas de localisation'}), 400
        
        # Sauvegarder l'ancienne position pour l'historique
        old_location = signalement.get_location_data()
        
        # Supprimer la localisation
        signalement.latitude = None
        signalement.longitude = None
        signalement.accuracy = None
        signalement.altitude = None
        signalement.heading = None
        signalement.speed = None
        signalement.location_timestamp = None
        signalement.location_address = None
        signalement.has_location = False
        
        db.session.commit()
        
        print(f"🗑️ Localisation supprimée pour signalement {signalement_id}")
        print(f"   Ancienne position: {old_location.get('coordinates_string')}")
        
        return jsonify({
            'success': True,
            'message': 'Localisation supprimée avec succès',
            'signalement_id': signalement_id,
            'removed_location': {
                'coordinates': old_location.get('coordinates_string'),
                'removed_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erreur: {str(e)}'}), 500