# app/routes/notification_route.py - VERSION FINALE COMPLÈTE
import json
from pydoc import text
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db
from app.models import FCMToken, NotificationHistory, NotificationPreferences
from app.models.notification.notification_models import NotificationTemplate
from app.services.notification.supabase_notification_service import (
    register_token, deactivate_token, send_test_notification,
    get_notification_history, mark_notification_read, get_user_tokens,
    get_notification_stats, update_user_preferences, send_to_multiple_users,
    send_notification
)
import logging
from datetime import datetime, timedelta

# Configuration du logging
logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__)

# =======================================
# ROUTES UTILISATEUR STANDARD
# =======================================

@notification_bp.route('/register-player', methods=['POST'])
@jwt_required()
def register_player():
    """
    Enregistrer un OneSignal Player ID
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        logger.info(f"[REGISTER-PLAYER] User {user_id} - Data: {data}")
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
            
        player_id = data.get('player_id')
        device_type = data.get('device_type', 'android')
        device_id = data.get('device_id')
        app_version = data.get('app_version', '1.0.0')
        
        if not player_id:
            return jsonify({'error': 'Player ID OneSignal requis'}), 400
        
        if device_type not in ['android', 'ios', 'web']:
            return jsonify({'error': 'device_type doit être android, ios ou web'}), 400
        
        success = register_token(
            user_id=user_id,
            token=player_id,
            device_type=device_type,
            device_id=device_id,
            app_version=app_version
        )
        
        if success:
            logger.info(f"[REGISTER-PLAYER] Succès pour user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Player ID OneSignal enregistré avec succès',
                'user_id': user_id,
                'device_type': device_type
            }), 200
        else:
            logger.error(f"[REGISTER-PLAYER] Échec pour user {user_id}")
            return jsonify({'error': 'Erreur lors de l\'enregistrement'}), 500
            
    except Exception as e:
        logger.error(f"[REGISTER-PLAYER] Erreur: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erreur serveur interne'}), 500

@notification_bp.route('/deactivate-player', methods=['POST'])
@jwt_required()
def deactivate_player():
    """
    Désactiver un Player ID OneSignal
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        player_id = data.get('player_id')
        if not player_id:
            return jsonify({'error': 'Player ID requis'}), 400
        
        success = deactivate_token(user_id, player_id)
        
        if success:
            logger.info(f"[DEACTIVATE-PLAYER] Player ID désactivé pour user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Player ID désactivé avec succès'
            }), 200
        else:
            return jsonify({'error': 'Player ID non trouvé ou déjà inactif'}), 404
            
    except Exception as e:
        logger.error(f"[DEACTIVATE-PLAYER] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@notification_bp.route('/test-notification', methods=['POST'])
@jwt_required()
def test_notification():
    """
    Envoyer une notification de test (développement uniquement)
    """
    try:
        if not current_app.config.get('DEBUG'):
            return jsonify({'error': 'Endpoint disponible uniquement en mode debug'}), 403
        
        user_id = get_jwt_identity()
        claims = get_jwt()
        username = claims.get('username', f'User{user_id}')
        
        data = request.get_json() or {}
        
        title = data.get('title', f'🧪 Test notification pour {username}')
        message = data.get('message', f'Test du système de notifications pour l\'utilisateur {username}')
        
        logger.info(f"[TEST-NOTIFICATION] Envoi pour user {user_id} ({username})")
        
        success = send_test_notification(
            user_id=user_id,
            title=title,
            message=message
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification de test envoyée via Supabase + OneSignal',
                'user_id': user_id,
                'username': username,
                'title': title
            }), 200
        else:
            return jsonify({
                'error': 'Échec envoi notification',
                'details': 'Vérifiez la configuration OneSignal/Supabase et que vous avez un Player ID enregistré'
            }), 500
            
    except Exception as e:
        logger.error(f"[TEST-NOTIFICATION] Erreur: {str(e)}", exc_info=True)
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@notification_bp.route('/history', methods=['GET'])
@jwt_required()
def notification_history():
    """
    Récupérer l'historique des notifications de l'utilisateur
    """
    try:
        user_id = get_jwt_identity()
        
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(max(1, request.args.get('per_page', 20, type=int)), 100)
        
        category = request.args.get('category')
        is_read = request.args.get('is_read')
        
        logger.info(f"[HISTORY] User {user_id} - Page {page}, Per page {per_page}")
        
        result = get_notification_history(
            user_id=user_id,
            page=page,
            per_page=per_page,
            category=category,
            is_read=is_read
        )
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            **result
        }), 200
        
    except Exception as e:
        logger.error(f"[HISTORY] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération historique'}), 500

@notification_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_read_route(notification_id):
    """
    Marquer une notification comme lue
    """
    try:
        user_id = get_jwt_identity()
        
        success = mark_notification_read(notification_id, user_id)
        
        if success:
            logger.info(f"[MARK-READ] Notification {notification_id} marquée lue pour user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Notification marquée comme lue',
                'notification_id': notification_id
            }), 200
        else:
            return jsonify({'error': 'Notification non trouvée ou déjà lue'}), 404
        
    except Exception as e:
        logger.error(f"[MARK-READ] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@notification_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_as_read():
    """
    Marquer toutes les notifications comme lues
    """
    try:
        user_id = get_jwt_identity()
        
        try:
            updated_count = NotificationHistory.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({
                'is_read': True,
                'clicked_at': db.func.now()
            })
            
            db.session.commit()
            
            logger.info(f"[MARK-ALL-READ] {updated_count} notifications marquées lues pour user {user_id}")
            
            return jsonify({
                'success': True,
                'message': f'{updated_count} notification(s) marquée(s) comme lue(s)',
                'updated_count': updated_count
            }), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        logger.error(f"[MARK-ALL-READ] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur marquage notifications'}), 500

@notification_bp.route('/tokens', methods=['GET'])
@jwt_required()
def get_user_tokens_route():
    """
    Récupérer les tokens de l'utilisateur connecté
    """
    try:
        user_id = get_jwt_identity()
        
        tokens = get_user_tokens(user_id)
        
        logger.info(f"[GET-TOKENS] User {user_id} a {len(tokens)} token(s)")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'tokens': tokens,
            'count': len(tokens)
        }), 200
        
    except Exception as e:
        logger.error(f"[GET-TOKENS] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération tokens'}), 500

@notification_bp.route('/stats', methods=['GET'])
@jwt_required()
def notification_stats():
    """
    Récupérer les statistiques de notifications
    """
    try:
        user_id = get_jwt_identity()
        
        stats = get_notification_stats(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"[STATS] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération statistiques'}), 500

@notification_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """
    Récupérer les préférences de notification
    """
    try:
        user_id = get_jwt_identity()
        
        preferences = NotificationPreferences.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            try:
                preferences = NotificationPreferences(user_id=user_id)
                db.session.add(preferences)
                db.session.commit()
                logger.info(f"[PREFERENCES] Préférences par défaut créées pour user {user_id}")
            except Exception as e:
                db.session.rollback()
                raise e
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'preferences': preferences.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"[GET-PREFERENCES] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération préférences'}), 500

@notification_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """
    Mettre à jour les préférences de notification
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données de préférences requises'}), 400
        
        allowed_fields = [
            'notifications_push', 'notifications_realtime', 'notifications_email',
            'nouveaux_signalements', 'commentaires_signalements', 'nouvelles_petitions',
            'commentaires_petitions', 'nouvelles_publications', 'commentaires_publications',
            'votes_signatures', 'reponses_autorites', 'mentions', 'changements_statut',
            'urgent_only', 'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'location_based', 'location_radius_km'
        ]
        
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not filtered_data:
            return jsonify({'error': 'Aucune préférence valide fournie'}), 400
        
        success = update_user_preferences(user_id, filtered_data)
        
        if success:
            logger.info(f"[UPDATE-PREFERENCES] Préférences mises à jour pour user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Préférences mises à jour avec succès',
                'updated_fields': list(filtered_data.keys())
            }), 200
        else:
            return jsonify({'error': 'Erreur mise à jour préférences'}), 500
        
    except Exception as e:
        logger.error(f"[UPDATE-PREFERENCES] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@notification_bp.route('/count-unread', methods=['GET'])
@jwt_required()
def count_unread():
    """
    Compter les notifications non lues
    """
    try:
        user_id = get_jwt_identity()
        
        count = NotificationHistory.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'unread_count': count
        }), 200
        
    except Exception as e:
        logger.error(f"[COUNT-UNREAD] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur comptage notifications'}), 500

@notification_bp.route('/delete/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """
    Supprimer une notification
    """
    try:
        user_id = get_jwt_identity()
        
        notification = NotificationHistory.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notification non trouvée'}), 404
        
        try:
            db.session.delete(notification)
            db.session.commit()
            
            logger.info(f"[DELETE] Notification {notification_id} supprimée pour user {user_id}")
            
            return jsonify({
                'success': True,
                'message': 'Notification supprimée avec succès',
                'notification_id': notification_id
            }), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
        
    except Exception as e:
        logger.error(f"[DELETE] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur suppression notification'}), 500

# =======================================
# ROUTES INTERACTIVES
# =======================================

@notification_bp.route('/send-direct', methods=['POST'])
@jwt_required()
def send_direct_notification():
    """
    Envoyer une notification directe à un utilisateur spécifique
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        sender_role = claims.get('role', 'citoyen')
        sender_name = claims.get('username', 'Utilisateur')
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        target_user_id = data.get('target_user_id')
        title = data.get('title')
        message = data.get('message')
        priority = data.get('priority', 'normal')
        category = data.get('category', 'message')
        
        if not all([target_user_id, title, message]):
            return jsonify({'error': 'target_user_id, title et message requis'}), 400
        
        # Vérifier que l'utilisateur cible existe
        from app.models import User
        target_user = User.query.get(target_user_id)
        if not target_user or target_user.is_deleted:
            return jsonify({'error': 'Utilisateur cible non trouvé'}), 404
        
        # Ajouter info de l'expéditeur
        enriched_data = {
            'sender_id': user_id,
            'sender_name': sender_name,
            'sender_role': sender_role,
            'direct_message': True
        }
        
        success = send_notification(
            user_id=target_user_id,
            title=f"💬 {title}",
            message=f"Message de {sender_name}: {message}",
            data=enriched_data,
            priority=priority,
            category=category
        )
        
        if success:
            logger.info(f"[SEND-DIRECT] Notification envoyée de {user_id} vers {target_user_id}")
            return jsonify({
                'success': True,
                'message': f'Notification envoyée à {target_user.username}',
                'target_user': target_user.username,
                'sender': sender_name
            }), 200
        else:
            return jsonify({'error': 'Échec envoi notification'}), 500
        
    except Exception as e:
        logger.error(f"[SEND-DIRECT] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@notification_bp.route('/broadcast', methods=['POST'])
@jwt_required()
def broadcast_notification():
    """
    Diffuser une notification à tous les utilisateurs (admin seulement)
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'citoyen')
        
        if user_role != 'admin':
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        title = data.get('title')
        message = data.get('message')
        priority = data.get('priority', 'normal')
        category = data.get('category', 'broadcast')
        user_types = data.get('user_types', ['citoyen'])  # Par défaut tous les citoyens
        
        if not all([title, message]):
            return jsonify({'error': 'title et message requis'}), 400
        
        # Récupérer les utilisateurs selon les types spécifiés
        from app.models import User
        query = User.query.filter_by(is_deleted=False)
        
        if user_types and user_types != ['all']:
            query = query.filter(User.type_user.in_(user_types))
        
        active_users = query.all()
        user_ids = [user.IDuser for user in active_users]
        
        # Envoyer les notifications
        success_count = send_to_multiple_users(
            user_ids=user_ids,
            title=f"📢 {title}",
            message=message,
            priority=priority,
            category=category,
            data={'broadcast': True, 'sender_id': str(user_id), 'user_types': user_types}
        )
        
        logger.info(f"[BROADCAST] {success_count}/{len(user_ids)} notifications diffusées par admin {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Notification diffusée à {success_count}/{len(user_ids)} utilisateur(s)',
            'sent_count': success_count,
            'total_users': len(user_ids),
            'user_types': user_types
        }), 200
        
    except Exception as e:
        logger.error(f"[BROADCAST] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur diffusion notification'}), 500

@notification_bp.route('/bulk-by-role', methods=['POST'])
@jwt_required()
def send_bulk_by_role():
    """
    Envoyer notification à tous les utilisateurs d'un rôle spécifique
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'citoyen')
        
        # Seuls admin et moderateur peuvent envoyer en masse
        if user_role not in ['admin', 'moderateur']:
            return jsonify({'error': 'Accès réservé aux administrateurs et modérateurs'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        target_role = data.get('target_role')
        title = data.get('title')
        message = data.get('message')
        priority = data.get('priority', 'normal')
        category = data.get('category', 'announcement')
        
        if not all([target_role, title, message]):
            return jsonify({'error': 'target_role, title et message requis'}), 400
        
        valid_roles = ['citoyen', 'admin', 'moderateur', 'authorite']
        if target_role not in valid_roles:
            return jsonify({'error': f'target_role doit être: {", ".join(valid_roles)}'}), 400
        
        # Récupérer utilisateurs du rôle cible
        from app.models import User
        users = User.query.filter_by(type_user=target_role, is_deleted=False).all()
        user_ids = [user.IDuser for user in users]
        
        if not user_ids:
            return jsonify({
                'success': True,
                'message': f'Aucun utilisateur trouvé avec le rôle {target_role}',
                'sent_count': 0,
                'total_users': 0
            }), 200
        
        success_count = send_to_multiple_users(
            user_ids=user_ids,
            title=f"📢 {title}",
            message=message,
            priority=priority,
            category=category,
            data={'bulk_role': True, 'target_role': target_role, 'sender_id': str(user_id)}
        )
        
        logger.info(f"[BULK-ROLE] {success_count}/{len(user_ids)} notifications envoyées au rôle {target_role} par {user_role} {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Notification envoyée à {success_count}/{len(user_ids)} {target_role}(s)',
            'sent_count': success_count,
            'total_users': len(user_ids),
            'target_role': target_role
        }), 200
        
    except Exception as e:
        logger.error(f"[BULK-ROLE] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur envoi bulk notification'}), 500

# =======================================
# ROUTES ADMIN AVANCÉES
# =======================================

@notification_bp.route('/admin/send-custom', methods=['POST'])
@jwt_required()
def send_custom_notification():
    """
    Envoyer une notification personnalisée (admin uniquement)
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'citoyen')
        
        if user_role != 'admin':
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        target_user_ids = data.get('target_user_ids', [])
        title = data.get('title')
        message = data.get('message')
        priority = data.get('priority', 'normal')
        category = data.get('category', 'admin_message')
        
        if not all([target_user_ids, title, message]):
            return jsonify({'error': 'target_user_ids, title et message requis'}), 400
        
        if not isinstance(target_user_ids, list) or len(target_user_ids) == 0:
            return jsonify({'error': 'target_user_ids doit être une liste non vide'}), 400
        
        success_count = send_to_multiple_users(
            user_ids=target_user_ids,
            title=title,
            message=message,
            priority=priority,
            category=category,
            data={'sender_id': str(user_id), 'admin_notification': True}
        )
        
        logger.info(f"[ADMIN-SEND] {success_count}/{len(target_user_ids)} notifications envoyées par admin {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Notifications envoyées à {success_count}/{len(target_user_ids)} utilisateur(s)',
            'sent_count': success_count,
            'total_targets': len(target_user_ids)
        }), 200
        
    except Exception as e:
        logger.error(f"[ADMIN-SEND] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur envoi notification personnalisée'}), 500

@notification_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def admin_notification_stats():
    """
    Statistiques globales des notifications (admin uniquement)
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'citoyen')
        
        if user_role != 'admin':
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        
        # Statistiques globales
        total_notifications = NotificationHistory.query.count()
        successful_notifications = NotificationHistory.query.filter_by(sent_successfully=True).count()
        failed_notifications = total_notifications - successful_notifications
        
        # Statistiques des tokens
        total_tokens = FCMToken.query.count()
        active_tokens = FCMToken.query.filter_by(is_active=True).count()
        
        # Statistiques par type de device
        android_tokens = FCMToken.query.filter_by(device_type='android', is_active=True).count()
        ios_tokens = FCMToken.query.filter_by(device_type='ios', is_active=True).count()
        web_tokens = FCMToken.query.filter_by(device_type='web', is_active=True).count()
        
        # Statistiques par catégorie (derniers 30 jours)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_notifications = NotificationHistory.query.filter(
            NotificationHistory.created_at >= thirty_days_ago
        ).all()
        
        category_stats = {}
        for notif in recent_notifications:
            cat = notif.category or 'general'
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'successful': 0}
            category_stats[cat]['total'] += 1
            if notif.sent_successfully:
                category_stats[cat]['successful'] += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'notifications': {
                    'total': total_notifications,
                    'successful': successful_notifications,
                    'failed': failed_notifications,
                    'success_rate': round((successful_notifications / total_notifications * 100), 2) if total_notifications > 0 else 0
                },
                'tokens': {
                    'total': total_tokens,
                    'active': active_tokens,
                    'inactive': total_tokens - active_tokens,
                    'by_platform': {
                        'android': android_tokens,
                        'ios': ios_tokens,
                        'web': web_tokens
                    }
                },
                'categories_last_30_days': category_stats
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[ADMIN-STATS] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération statistiques admin'}), 500

@notification_bp.route('/admin/cleanup-tokens', methods=['POST'])
@jwt_required()
def cleanup_old_tokens():
    """
    Nettoyer les anciens tokens inactifs (admin uniquement)
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role', 'citoyen')
        
        if user_role != 'admin':
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        
        from app.services.notification.supabase_notification_service import cleanup_invalid_tokens
        
        deleted_count = cleanup_invalid_tokens()
        
        logger.info(f"[CLEANUP-TOKENS] {deleted_count} tokens supprimés par admin {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count} ancien(s) token(s) supprimé(s)',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"[CLEANUP-TOKENS] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur nettoyage tokens'}), 500

# =======================================
# ROUTES UTILITAIRES
# =======================================

@notification_bp.route('/health', methods=['GET'])
@jwt_required()
def health_check():
    """
    Vérification de l'état du système de notifications
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        # Vérifier la configuration
        config_status = {
            'debug_mode': current_app.config.get('DEBUG', False),
            'onesignal_configured': bool(current_app.config.get('ONESIGNAL_APP_ID')),
            'supabase_configured': bool(current_app.config.get('SUPABASE_URL'))
        }
        
        # Vérifier les tokens de l'utilisateur
        user_tokens = FCMToken.query.filter_by(user_id=user_id, is_active=True).count()
        
        # Vérifier l'historique
        user_notifications = NotificationHistory.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'system_health': {
                'status': 'healthy',
                'config': config_status,
                'user_data': {
                    'user_id': user_id,
                    'username': claims.get('username', 'N/A'),
                    'active_tokens': user_tokens,
                    'total_notifications': user_notifications
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[HEALTH] Erreur: {str(e)}")
        return jsonify({
            'success': False,
            'system_health': {
                'status': 'unhealthy',
                'error': str(e)
            }
        }), 500

@notification_bp.route('/types', methods=['GET'])
def get_notification_types():
    """
    Récupérer tous les types de notifications disponibles
    """
    try:
        notification_types = {
            'categories': {
                'signalement': {
                    'name': 'Signalements',
                    'description': 'Notifications liées aux signalements citoyens',
                    'color': '#e74c3c',
                    'icon': '📍'
                },
                'petition': {
                    'name': 'Pétitions', 
                    'description': 'Notifications liées aux pétitions',
                    'color': '#3498db',
                    'icon': '✍️'
                },
                'publication': {
                    'name': 'Publications',
                    'description': 'Réponses officielles des autorités',
                    'color': '#2ecc71',
                    'icon': '📢'
                },
                'social': {
                    'name': 'Social',
                    'description': 'Interactions sociales (suiveurs, mentions)',
                    'color': '#9b59b6',
                    'icon': '👥'
                },
                'status': {
                    'name': 'Statuts',
                    'description': 'Changements de statut de contenus',
                    'color': '#f39c12',
                    'icon': '📋'
                },
                'system': {
                    'name': 'Système',
                    'description': 'Notifications système importantes',
                    'color': '#34495e',
                    'icon': '⚙️'
                },
                'admin': {
                    'name': 'Administration',
                    'description': 'Messages administratifs',
                    'color': '#e67e22',
                    'icon': '👑'
                }
            },
            'priorities': {
                'low': {
                    'name': 'Faible',
                    'description': 'Notifications non urgentes',
                    'color': '#95a5a6',
                    'sound': 'none'
                },
                'normal': {
                    'name': 'Normal',
                    'description': 'Notifications standard',
                    'color': '#3498db',
                    'sound': 'default'
                },
                'high': {
                    'name': 'Élevée',
                    'description': 'Notifications importantes',
                    'color': '#f39c12',
                    'sound': 'long'
                },
                'urgent': {
                    'name': 'Urgent',
                    'description': 'Notifications critiques',
                    'color': '#e74c3c',
                    'sound': 'urgent'
                }
            },
            'actions': {
                'vote': {
                    'name': 'Nouveau vote',
                    'category': 'signalement',
                    'template': '{voter_name} a voté {vote_type} sur votre signalement',
                    'icon': '👍',
                    'priority': 'normal'
                },
                'signature': {
                    'name': 'Nouvelle signature',
                    'category': 'petition',
                    'template': '{signer_name} a signé votre pétition "{petition_title}"',
                    'icon': '✍️',
                    'priority': 'normal'
                },
                'comment_signalement': {
                    'name': 'Commentaire signalement',
                    'category': 'signalement',
                    'template': '{commenter_name} a commenté votre signalement',
                    'icon': '💬',
                    'priority': 'normal'
                },
                'comment_petition': {
                    'name': 'Commentaire pétition',
                    'category': 'petition',
                    'template': '{commenter_name} a commenté votre pétition',
                    'icon': '💬',
                    'priority': 'normal'
                },
                'authority_response': {
                    'name': 'Réponse officielle',
                    'category': 'publication',
                    'template': '{authority_name} a publié une réponse à votre signalement',
                    'icon': '📢',
                    'priority': 'high'
                },
                'follow': {
                    'name': 'Nouveau suiveur',
                    'category': 'social',
                    'template': '{follower_name} vous suit maintenant',
                    'icon': '👤',
                    'priority': 'low'
                },
                'status_change': {
                    'name': 'Changement de statut',
                    'category': 'status',
                    'template': 'Votre {content_type} est maintenant {new_status}',
                    'icon': '📋',
                    'priority': 'high'
                },
                'mention': {
                    'name': 'Mention',
                    'category': 'social',
                    'template': '{mentioner_name} vous a mentionné',
                    'icon': '@',
                    'priority': 'normal'
                }
            }
        }
        
        return jsonify({
            'success': True,
            'notification_types': notification_types,
            'total_categories': len(notification_types['categories']),
            'total_actions': len(notification_types['actions']),
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"[GET-TYPES] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération types notifications'}), 500

@notification_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_notification_templates():
    """
    Récupérer les templates de notifications disponibles
    """
    try:
        from app.models import NotificationTemplate
        
        templates = NotificationTemplate.query.filter_by(is_active=True).all()
        
        templates_data = []
        for template in templates:
            templates_data.append({
                'id': template.id,
                'name': template.name,
                'title_template': template.title_template,
                'message_template': template.message_template,
                'category': template.category,
                'priority': template.priority,
                'icon_url': template.icon_url,
                'variables': json.loads(template.variables) if template.variables else [],
                'preview_title': template.title_template.replace('{', '').replace('}', ''),
                'preview_message': template.message_template.replace('{', '').replace('}', '')
            })
        
        return jsonify({
            'success': True,
            'templates': templates_data,
            'count': len(templates_data)
        }), 200
        
    except Exception as e:
        logger.error(f"[GET-TEMPLATES] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération templates'}), 500

@notification_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_notifications():
    """
    Récupérer les notifications récentes (dernières 24h)
    """
    try:
        user_id = get_jwt_identity()
        
        # Dernières 24 heures
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        recent_notifications = NotificationHistory.query.filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.created_at >= twenty_four_hours_ago
        ).order_by(NotificationHistory.created_at.desc()).limit(50).all()
        
        notifications_data = []
        for notif in recent_notifications:
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'category': notif.category,
                'priority': notif.priority,
                'is_read': notif.is_read,
                'entity_type': notif.entity_type,
                'entity_id': notif.entity_id,
                'created_at': notif.created_at.isoformat(),
                'delivery_method': notif.delivery_method,
                'sent_successfully': notif.sent_successfully,
                'time_ago': _calculate_time_ago(notif.created_at)
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications_data,
            'count': len(notifications_data),
            'period': '24h'
        }), 200
        
    except Exception as e:
        logger.error(f"[RECENT] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération notifications récentes'}), 500

def _calculate_time_ago(created_at):
    """Calcule le temps écoulé depuis la création"""
    try:
        now = datetime.utcnow()
        diff = now - created_at
        
        if diff.days > 0:
            return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "à l'instant"
    except:
        return "récemment"


# app/routes/notification_route.py - ENDPOINTS SUPPLÉMENTAIRES

# =======================================
# NOUVEAUX ENDPOINTS À AJOUTER
# =======================================

@notification_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_notification_categories():
    """
    Récupère les catégories de notifications disponibles avec compteurs
    """
    try:
        user_id = get_jwt_identity()
        
        # Compter par catégorie
        categories_stats = db.session.execute(text("""
            SELECT 
                category,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_read = false) as unread
            FROM notification_history 
            WHERE user_id = :user_id
            GROUP BY category
            ORDER BY total DESC
        """), {'user_id': user_id}).fetchall()
        
        categories = []
        for stat in categories_stats:
            categories.append({
                'name': stat.category,
                'total': stat.total,
                'unread': stat.unread,
                'icon': _get_category_icon(stat.category),
                'display_name': _get_category_display_name(stat.category)
            })
        
        return jsonify({
            'success': True,
            'categories': categories
        }), 200
        
    except Exception as e:
        logger.error(f"[CATEGORIES] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération catégories'}), 500

@notification_bp.route('/history/category/<category>', methods=['GET'])
@jwt_required()
def get_notifications_by_category(category):
    """
    Récupère les notifications d'une catégorie spécifique
    """
    try:
        user_id = get_jwt_identity()
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(max(1, request.args.get('per_page', 20, type=int)), 100)
        
        notifications = NotificationHistory.query.filter_by(
            user_id=user_id,
            category=category
        ).order_by(NotificationHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'category': category,
            'notifications': [n.to_dict() for n in notifications.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': notifications.total,
                'pages': notifications.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[CATEGORY-HISTORY] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération notifications'}), 500

@notification_bp.route('/batch-mark-read', methods=['POST'])
@jwt_required()
def batch_mark_read():
    """
    Marquer plusieurs notifications comme lues en une fois
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'notification_ids' not in data:
            return jsonify({'error': 'Liste des IDs requise'}), 400
        
        notification_ids = data['notification_ids']
        
        if not isinstance(notification_ids, list) or len(notification_ids) == 0:
            return jsonify({'error': 'Liste des IDs invalide'}), 400
        
        # Marquer comme lues
        updated_count = NotificationHistory.query.filter(
            NotificationHistory.id.in_(notification_ids),
            NotificationHistory.user_id == user_id,
            NotificationHistory.is_read == False
        ).update({
            'is_read': True,
            'clicked_at': db.func.now()
        }, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} notification(s) marquée(s) comme lue(s)',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        logger.error(f"[BATCH-MARK-READ] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur marquage batch'}), 500

@notification_bp.route('/search', methods=['GET'])
@jwt_required()
def search_notifications():
    """
    Rechercher dans les notifications
    """
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'error': 'Requête de recherche trop courte'}), 400
        
        # Recherche dans titre et message
        notifications = NotificationHistory.query.filter(
            NotificationHistory.user_id == user_id,
            db.or_(
                NotificationHistory.title.ilike(f'%{query}%'),
                NotificationHistory.message.ilike(f'%{query}%')
            )
        ).order_by(NotificationHistory.created_at.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'query': query,
            'results': [n.to_dict() for n in notifications],
            'count': len(notifications)
        }), 200
        
    except Exception as e:
        logger.error(f"[SEARCH] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur recherche'}), 500

@notification_bp.route('/admin/notification-templates', methods=['GET'])
@jwt_required()
def admin_get_notification_templates():
    """
    Récupère les templates de notifications disponibles (admin uniquement)
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({'error': 'Accès admin requis'}), 403

        templates = NotificationTemplate.query.filter_by(is_active=True).all()

        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates]
        }), 200

    except Exception as e:
        logger.error(f"[ADMIN-TEMPLATES] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur récupération templates'}), 500


@notification_bp.route('/send-to-followers', methods=['POST'])
@jwt_required()
def send_to_followers():
    """
    Envoyer notification à tous ses abonnés (pour autorités/influenceurs)
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        title = data.get('title')
        message = data.get('message')
        category = data.get('category', 'social')
        priority = data.get('priority', 'normal')
        
        if not all([title, message]):
            return jsonify({'error': 'Title et message requis'}), 400
        
        # Récupérer les abonnés
        followers = db.session.execute(text("""
            SELECT suiveurID as user_id
            FROM suivres 
            WHERE suivisID = :user_id AND is_deleted = false
        """), {'user_id': user_id}).fetchall()
        
        if not followers:
            return jsonify({'error': 'Aucun abonné trouvé'}), 404
        
        follower_ids = [f.user_id for f in followers]
        
        # Envoyer les notifications
        success_count = send_to_multiple_users(
            user_ids=follower_ids,
            title=title,
            message=message,
            priority=priority,
            category=category,
            data={'sender_id': str(user_id), 'type': 'follower_notification'}
        )
        
        return jsonify({
            'success': True,
            'message': f'Notifications envoyées à {success_count}/{len(follower_ids)} abonné(s)',
            'sent_count': success_count,
            'total_followers': len(follower_ids)
        }), 200
        
    except Exception as e:
        logger.error(f"[SEND-TO-FOLLOWERS] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur envoi aux abonnés'}), 500

@notification_bp.route('/schedule', methods=['POST'])
@jwt_required()
def schedule_notification():
    """
    Programmer une notification pour plus tard (admin uniquement)
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Accès admin requis'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        # Validation des champs
        required_fields = ['target_user_ids', 'title', 'message', 'scheduled_at']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Champs requis manquants'}), 400
        
        # Créer l'entrée en base pour la programmation
        # Note: Vous devrez créer une table ScheduledNotification
        scheduled_notification = {
            'target_user_ids': json.dumps(data['target_user_ids']),
            'title': data['title'],
            'message': data['message'],
            'scheduled_at': data['scheduled_at'],
            'priority': data.get('priority', 'normal'),
            'category': data.get('category', 'scheduled'),
            'created_by': user_id,
            'status': 'pending'
        }
        
        # Ici vous devrez ajouter la logique de programmation
        # avec une tâche cron ou un worker background
        
        return jsonify({
            'success': True,
            'message': 'Notification programmée avec succès',
            'scheduled_at': data['scheduled_at']
        }), 201
        
    except Exception as e:
        logger.error(f"[SCHEDULE] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur programmation notification'}), 500

@notification_bp.route('/digest/weekly', methods=['GET'])
@jwt_required()
def get_weekly_digest():
    """
    Récupère le digest hebdomadaire des notifications
    """
    try:
        user_id = get_jwt_identity()
        
        # Calculer la semaine dernière
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Statistiques de la semaine
        stats = db.session.execute(text("""
            SELECT 
                category,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE priority = 'urgent') as urgent_count
            FROM notification_history 
            WHERE user_id = :user_id 
            AND created_at BETWEEN :start_date AND :end_date
            GROUP BY category
            ORDER BY count DESC
        """), {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        }).fetchall()
        
        # Notifications les plus importantes de la semaine
        important_notifications = NotificationHistory.query.filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.created_at.between(start_date, end_date),
            NotificationHistory.priority.in_(['urgent', 'high'])
        ).order_by(NotificationHistory.created_at.desc()).limit(10).all()
        
        digest = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'stats_by_category': [
                {
                    'category': stat.category,
                    'count': stat.count,
                    'urgent_count': stat.urgent_count
                } for stat in stats
            ],
            'important_notifications': [n.to_dict() for n in important_notifications],
            'total_notifications': sum(stat.count for stat in stats)
        }
        
        return jsonify({
            'success': True,
            'weekly_digest': digest
        }), 200
        
    except Exception as e:
        logger.error(f"[WEEKLY-DIGEST] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur génération digest'}), 500

@notification_bp.route('/export', methods=['GET'])
@jwt_required()
def export_notifications():
    """
    Exporter l'historique des notifications en JSON
    """
    try:
        user_id = get_jwt_identity()
        
        # Paramètres d'export
        days = min(request.args.get('days', 30, type=int), 365)  # Max 1 an
        format_type = request.args.get('format', 'json')  # json ou csv
        
        # Calculer la période
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Récupérer les notifications
        notifications = NotificationHistory.query.filter(
            NotificationHistory.user_id == user_id,
            NotificationHistory.created_at.between(start_date, end_date)
        ).order_by(NotificationHistory.created_at.desc()).all()
        
        if format_type == 'json':
            export_data = {
                'export_info': {
                    'user_id': user_id,
                    'period_days': days,
                    'exported_at': datetime.utcnow().isoformat(),
                    'total_notifications': len(notifications)
                },
                'notifications': [n.to_dict() for n in notifications]
            }
            
            return jsonify({
                'success': True,
                'export_data': export_data
            }), 200
        
        else:
            return jsonify({'error': 'Format non supporté'}), 400
        
    except Exception as e:
        logger.error(f"[EXPORT] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur export notifications'}), 500

# =======================================
# FONCTIONS UTILITAIRES
# =======================================

def _get_category_icon(category):
    """Retourne l'icône pour une catégorie"""
    icons = {
        'signalement': '🚨',
        'petition': '📜',
        'publication': '📢',
        'social': '👥',
        'system': '⚙️',
        'admin_message': '👮‍♂️',
        'moderation': '🛡️',
        'security': '🔒',
        'maintenance': '🔧',
        'achievement': '🏆'
    }
    return icons.get(category, '🔔')

def _get_category_display_name(category):
    """Retourne le nom d'affichage pour une catégorie"""
    names = {
        'signalement': 'Signalements',
        'petition': 'Pétitions',
        'publication': 'Publications',
        'social': 'Social',
        'system': 'Système',
        'admin_message': 'Messages Admin',
        'moderation': 'Modération',
        'security': 'Sécurité',
        'maintenance': 'Maintenance',
        'achievement': 'Récompenses'
    }
    return names.get(category, category.title())

# =======================================
# WEBHOOKS (OPTIONNEL)
# =======================================

@notification_bp.route('/webhook/onesignal', methods=['POST'])
def onesignal_webhook():
    """
    Webhook OneSignal pour tracking des notifications
    """
    try:
        data = request.get_json()
        
        # Vérifier l'authenticité du webhook
        # (Vous devrez implémenter la vérification de signature)
        
        # Traiter les événements OneSignal
        if data.get('event') == 'notification.delivered':
            # Notification livrée
            notification_id = data.get('notification_id')
            # Mettre à jour le statut en base
            
        elif data.get('event') == 'notification.clicked':
            # Notification cliquée
            # Enregistrer les métriques
            pass
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"[ONESIGNAL-WEBHOOK] Erreur: {str(e)}")
        return jsonify({'error': 'Erreur webhook'}), 500