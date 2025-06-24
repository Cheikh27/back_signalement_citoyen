
# app/services/supabase_notification_service.py - VERSION FINALE
from datetime import datetime, timedelta
import requests
import json
from flask import current_app
from app.models import db
from app.models import FCMToken, NotificationHistory
from typing import List, Optional, Dict, Any
from sqlalchemy import text

# Configuration
ONESIGNAL_URL = "https://onesignal.com/api/v1/notifications"

def _get_onesignal_config():
    """Récupère la configuration OneSignal"""
    return {
        'app_id': current_app.config.get('ONESIGNAL_APP_ID'),
        'api_key': current_app.config.get('ONESIGNAL_API_KEY')
    }

def _get_supabase_client():
    """Récupère le client Supabase avec service role"""
    try:
        from supabase import create_client
        url = current_app.config.get('SUPABASE_URL')
        key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')
        return create_client(url, key) if url and key else None
    except ImportError:
        current_app.logger.error("Supabase client non disponible")
        return None

def _get_user_preferences(user_id: int) -> Dict:
    """Récupère les préférences de notification d'un utilisateur"""
    try:
        result = db.session.execute(text("""
            SELECT * FROM notification_preferences WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchone()
        
        if result:
            return dict(result._mapping)
        else:
            # Créer préférences par défaut
            db.session.execute(text("""
                INSERT INTO notification_preferences (user_id, created_at, updated_at)
                VALUES (:user_id, NOW(), NOW())
            """), {'user_id': user_id})
            db.session.commit()
            
            # Retourner les valeurs par défaut
            return {
                'notifications_push': True,
                'notifications_realtime': True,
                'notifications_email': False,
                'nouveaux_signalements': True,
                'commentaires_signalements': True,
                'nouvelles_petitions': True,
                'commentaires_petitions': True,
                'nouvelles_publications': True,
                'commentaires_publications': True,
                'votes_signatures': True,
                'reponses_autorites': True,
                'mentions': True,
                'changements_statut': True,
                'urgent_only': False,
                'quiet_hours_enabled': False,
                'location_based': True
            }
    except Exception as e:
        current_app.logger.error(f"Erreur récupération préférences: {e}")
        return {}

def _should_send_notification(category: str, priority: str, preferences: Dict) -> bool:
    """Vérifie si la notification doit être envoyée selon les préférences"""
    try:
        # Si mode urgent seulement
        if preferences.get('urgent_only', False) and priority != 'urgent':
            return False
        
        # Vérifier les préférences par catégorie
        category_mapping = {
            'signalement': preferences.get('nouveaux_signalements', True),
            'petition': preferences.get('nouvelles_petitions', True),
            'publication': preferences.get('nouvelles_publications', True),
            'status': preferences.get('changements_statut', True),
            'social': preferences.get('mentions', True),
            'system': True  # Toujours envoyer les notifications système
        }
        
        return category_mapping.get(category, True)
    except Exception:
        return True  # En cas d'erreur, envoyer par défaut

def _is_quiet_hours(preferences: Dict) -> bool:
    """Vérifie si on est dans les heures silencieuses"""
    try:
        if not preferences.get('quiet_hours_enabled', False):
            return False
        
        now = datetime.now().time()
        start_time = preferences.get('quiet_hours_start')
        end_time = preferences.get('quiet_hours_end')
        
        if start_time and end_time:
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # Période qui traverse minuit
                return now >= start_time or now <= end_time
        
        return False
    except Exception:
        return False

def _send_push_notification(user_tokens: List[str], title: str, message: str, data: Dict = None) -> bool:
    """Envoie notification push via OneSignal"""
    try:
        config = _get_onesignal_config()
        if not config['app_id'] or not config['api_key']:
            current_app.logger.warning("OneSignal non configuré")
            return False

        headers = {
            'Authorization': f'Basic {config["api_key"]}',
            'Content-Type': 'application/json'
        }

        payload = {
            'app_id': config['app_id'],
            'include_player_ids': user_tokens,
            'headings': {'en': title, 'fr': title},
            'contents': {'en': message, 'fr': message},
            'data': data or {},
            'priority': 10,
            'sound': 'default',
            'android_channel_id': 'main_channel'
        }

        response = requests.post(ONESIGNAL_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            current_app.logger.info(f"OneSignal: {result.get('recipients', 0)} notifications envoyées")
            return result.get('recipients', 0) > 0
        else:
            current_app.logger.error(f"OneSignal error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        current_app.logger.error(f"Erreur OneSignal: {e}")
        return False

def _send_realtime_notification(user_id: int, title: str, message: str, data: Dict = None, 
                               entity_type: str = None, entity_id: int = None, 
                               priority: str = 'normal', category: str = 'general') -> bool:
    """Envoie notification en temps réel via Supabase"""
    try:
        supabase = _get_supabase_client()
        if not supabase:
            current_app.logger.warning("Client Supabase non disponible")
            return False

        notification_data = {
            'user_id': user_id,
            'title': title,
            'message': message,
            'data': data or {},
            'entity_type': entity_type,
            'entity_id': entity_id,
            'priority': priority,
            'category': category
        }

        result = supabase.table('realtime_notifications').insert(notification_data).execute()
        
        success = bool(result.data)
        if success:
            current_app.logger.info(f"Supabase realtime: notification envoyée à user {user_id}")
        
        return success

    except Exception as e:
        current_app.logger.error(f"Erreur Supabase realtime: {e}")
        return False

def send_notification(user_id: int,
                     title: str,
                     message: str,
                     data: Dict[str, Any] = None,
                     entity_type: str = None,
                     entity_id: int = None,
                     priority: str = 'normal',
                     category: str = 'general') -> bool:
    """Envoie notification via Supabase Realtime + OneSignal push"""
    try:
        # Récupérer les préférences utilisateur
        preferences = _get_user_preferences(user_id)
        
        # Vérifier si la notification doit être envoyée
        if not _should_send_notification(category, priority, preferences):
            current_app.logger.info(f"Notification filtrée par préférences pour user {user_id}")
            return False
        
        # Vérifier les heures silencieuses (sauf urgent)
        if priority != 'urgent' and _is_quiet_hours(preferences):
            current_app.logger.info(f"Notification reportée (heures silencieuses) pour user {user_id}")
            return False

        success_realtime = False
        success_push = False
        delivery_methods = []

        # 1. Envoyer via Supabase Realtime si activé
        if preferences.get('notifications_realtime', True):
            success_realtime = _send_realtime_notification(
                user_id=user_id,
                title=title,
                message=message,
                data=data,
                entity_type=entity_type,
                entity_id=entity_id,
                priority=priority,
                category=category
            )
            if success_realtime:
                delivery_methods.append('supabase')

        # 2. Envoyer push notification si activé
        if preferences.get('notifications_push', True):
            tokens = FCMToken.query.filter_by(user_id=user_id, is_active=True).all()
            
            if tokens:
                player_ids = [token.token for token in tokens]
                success_push = _send_push_notification(player_ids, title, message, data)
                
                if success_push:
                    delivery_methods.append('onesignal')
                    # Mettre à jour last_used des tokens
                    for token in tokens:
                        token.last_used = datetime.utcnow()

        # 3. Enregistrer dans l'historique Flask
        delivery_method = ','.join(delivery_methods) if delivery_methods else 'failed'
        
        history = NotificationHistory(
            user_id=user_id,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            sent_successfully=success_realtime or success_push,
            delivery_method=delivery_method,
            priority=priority,
            category=category,
            metadata=json.dumps(data) if data else None
        )
        
        if success_push and delivery_methods:
            history.fcm_message_id = f"delivery_{len(delivery_methods)}_methods"

        db.session.add(history)
        db.session.commit()

        current_app.logger.info(f"Notification user {user_id}: realtime={success_realtime}, push={success_push}")
        return success_realtime or success_push

    except Exception as e:
        current_app.logger.error(f"Erreur envoi notification user {user_id}: {e}")
        db.session.rollback()
        return False

def send_to_multiple_users(user_ids: List[int],
                          title: str,
                          message: str,
                          data: Dict[str, Any] = None,
                          entity_type: str = None,
                          entity_id: int = None,
                          priority: str = 'normal',
                          category: str = 'general') -> int:
    """Envoie notification à plusieurs utilisateurs"""
    success_count = 0
    
    for user_id in user_ids:
        if send_notification(
            user_id=user_id,
            title=title,
            message=message,
            data=data,
            entity_type=entity_type,
            entity_id=entity_id,
            priority=priority,
            category=category
        ):
            success_count += 1

    current_app.logger.info(f"Notifications groupées: {success_count}/{len(user_ids)} envoyées")
    return success_count

def create_notification_from_template(template_name: str,
                                    user_id: int,
                                    variables: Dict[str, str] = None,
                                    entity_type: str = None,
                                    entity_id: int = None) -> bool:
    """Crée une notification à partir d'un template"""
    try:
        # Récupérer le template
        template = db.session.execute(text("""
            SELECT * FROM notification_templates 
            WHERE name = :name AND is_active = true
        """), {'name': template_name}).fetchone()
        
        if not template:
            current_app.logger.error(f"Template '{template_name}' non trouvé")
            return False
        
        # Remplacer les variables dans le template
        title = template.title_template
        message = template.message_template
        
        if variables:
            for key, value in variables.items():
                title = title.replace(f'{{{key}}}', str(value))
                message = message.replace(f'{{{key}}}', str(value))
        
        # Envoyer la notification
        return send_notification(
            user_id=user_id,
            title=title,
            message=message,
            data=variables,
            entity_type=entity_type,
            entity_id=entity_id,
            priority=template.priority,
            category=template.category
        )
        
    except Exception as e:
        current_app.logger.error(f"Erreur template notification: {e}")
        return False

def register_token(user_id: int,
                  token: str,
                  device_type: str,
                  device_id: str = None,
                  app_version: str = None) -> bool:
    """Enregistre un OneSignal player_id"""
    try:
        existing_token = FCMToken.query.filter_by(token=token).first()

        if existing_token:
            existing_token.user_id = user_id
            existing_token.device_type = device_type
            existing_token.device_id = device_id
            existing_token.app_version = app_version
            existing_token.is_active = True
            existing_token.last_used = datetime.utcnow()
        else:
            if device_id:
                FCMToken.query.filter_by(
                    user_id=user_id,
                    device_id=device_id
                ).update({'is_active': False})

            new_token = FCMToken(
                user_id=user_id,
                token=token,
                device_type=device_type,
                device_id=device_id,
                app_version=app_version
            )
            db.session.add(new_token)

        db.session.commit()
        current_app.logger.info(f"Player ID OneSignal enregistré pour user {user_id}")
        return True

    except Exception as e:
        current_app.logger.error(f"Erreur enregistrement player ID: {e}")
        db.session.rollback()
        return False

def get_notification_stats(user_id: int) -> Dict:
    """Récupère les statistiques de notifications d'un utilisateur"""
    try:
        stats = db.session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_read = false) as unread,
                COUNT(*) FILTER (WHERE is_read = true) as read,
                COUNT(*) FILTER (WHERE priority = 'urgent') as urgent,
                COUNT(*) FILTER (WHERE created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)) as today,
                COUNT(*) FILTER (WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY)) as week
            FROM notification_history 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchone()
        
        if stats:
            return {
                'total': stats.total or 0,
                'unread': stats.unread or 0,
                'read': stats.read or 0,
                'urgent': stats.urgent or 0,
                'today': stats.today or 0,
                'week': stats.week or 0
            }
        
        return {'total': 0, 'unread': 0, 'read': 0, 'urgent': 0, 'today': 0, 'week': 0}
        
    except Exception as e:
        current_app.logger.error(f"Erreur stats notifications: {e}")
        return {}

def update_user_preferences(user_id: int, preferences: Dict) -> bool:
    """Met à jour les préférences de notification d'un utilisateur"""
    try:
        # Construire la requête UPDATE dynamiquement
        set_clauses = []
        params = {'user_id': user_id}
        
        allowed_fields = [
            'notifications_push', 'notifications_realtime', 'notifications_email',
            'nouveaux_signalements', 'commentaires_signalements', 'nouvelles_petitions',
            'commentaires_petitions', 'nouvelles_publications', 'commentaires_publications',
            'votes_signatures', 'reponses_autorites', 'mentions', 'changements_statut',
            'urgent_only', 'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'location_based', 'location_radius_km'
        ]
        
        for field, value in preferences.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
        
        if set_clauses:
            query = f"""
                UPDATE notification_preferences 
                SET {', '.join(set_clauses)}, updated_at = NOW()
                WHERE user_id = :user_id
            """
            
            result = db.session.execute(text(query), params)
            
            if result.rowcount == 0:
                # Créer si n'existe pas
                db.session.execute(text("""
                    INSERT INTO notification_preferences (user_id, created_at, updated_at)
                    VALUES (:user_id, NOW(), NOW())
                """), {'user_id': user_id})
                
                # Réessayer l'update
                db.session.execute(text(query), params)
            
            db.session.commit()
            return True
        
        return False
        
    except Exception as e:
        current_app.logger.error(f"Erreur mise à jour préférences: {e}")
        db.session.rollback()
        return False

# Fonctions utilitaires existantes (cleanup, test, etc.)
def cleanup_invalid_tokens() -> int:
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = FCMToken.query.filter(
            FCMToken.is_active == False,
            FCMToken.last_used < cutoff_date
        ).delete()
        db.session.commit()
        return deleted_count
    except Exception as e:
        current_app.logger.error(f"Erreur nettoyage tokens: {e}")
        return 0

def send_test_notification(user_id: int, title: str = "Test Supabase + OneSignal", 
                          message: str = "Test du système de notifications") -> bool:
    return send_notification(user_id, title, message, {'test': True}, 'test', 0, 'normal', 'test')

def get_user_tokens(user_id: int) -> List[Dict]:
    try:
        tokens = FCMToken.query.filter_by(user_id=user_id).all()
        return [token.to_dict() for token in tokens]
    except:
        return []

def deactivate_token(user_id: int, token: str) -> bool:
    try:
        fcm_token = FCMToken.query.filter_by(user_id=user_id, token=token).first()
        if fcm_token:
            fcm_token.is_active = False
            db.session.commit()
            return True
        return False
    except:
        return False

def get_notification_history(user_id: int, page: int = 1, per_page: int = 20) -> Dict:
    try:
        history = NotificationHistory.query.filter_by(user_id=user_id).order_by(
            NotificationHistory.created_at.desc()
        ).paginate(page=page, per_page=min(per_page, 100), error_out=False)
        
        return {
            'notifications': [h.to_dict() for h in history.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': history.total,
                'pages': history.pages
            }
        }
    except:
        return {'notifications': [], 'pagination': {}}

def mark_notification_read(notification_id: int, user_id: int) -> bool:
    try:
        notification = NotificationHistory.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            notification.clicked_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except:
        return False