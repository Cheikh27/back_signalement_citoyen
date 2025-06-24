# app/services/notification_helper.py - CRÉER CE FICHIER
from supabase_notification_service import send_notification
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class NotificationHelper:
    """Helper simplifié pour déclencher les notifications dans les services"""
    
    @staticmethod
    def notify_new_vote(signalement, vote, voteur_id):
        """Notification pour nouveau vote sur signalement"""
        try:
            if signalement.citoyenID == voteur_id:
                return
                
            from app.models import Citoyen
            voteur = Citoyen.query.get(voteur_id)
            voteur_nom = f"{voteur.prenom} {voteur.nom}" if voteur else "Quelqu'un"
            
            vote_emoji = "👍" if vote.types == "positif" else "👎"
            
            success = send_notification(
                user_id=signalement.citoyenID,
                title=f"{vote_emoji} Nouveau vote sur votre signalement",
                message=f"{voteur_nom} a voté {vote.types} sur votre signalement",
                entity_type='signalement',
                entity_id=signalement.IDsignalement,
                category='signalement',
                priority='normal',
                data={'action': 'vote', 'voteur_id': voteur_id, 'vote_type': vote.types}
            )
            
            if success:
                logger.info(f"✅ Notification vote envoyée: signalement {signalement.IDsignalement} -> user {signalement.citoyenID}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification vote: {e}")

    @staticmethod
    def notify_new_signature(petition, signature, signataire_id):
        """Notification pour nouvelle signature de pétition"""
        try:
            if petition.citoyenID == signataire_id:
                return
                
            from app.models import Citoyen
            signataire = Citoyen.query.get(signataire_id)
            signataire_nom = f"{signataire.prenom} {signataire.nom}" if signataire else "Quelqu'un"
            
            success = send_notification(
                user_id=petition.citoyenID,
                title="✍️ Nouvelle signature sur votre pétition",
                message=f"{signataire_nom} a signé votre pétition '{petition.titre}'",
                entity_type='petition',
                entity_id=petition.IDpetition,
                category='petition',
                priority='normal',
                data={'action': 'signature', 'signataire_id': signataire_id}
            )
            
            if success:
                logger.info(f"✅ Notification signature envoyée: pétition {petition.IDpetition} -> user {petition.citoyenID}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification signature: {e}")

    @staticmethod
    def notify_new_comment_signalement(signalement, comment, commenteur_id):
        """Notification pour nouveau commentaire sur signalement"""
        try:
            if signalement.citoyenID == commenteur_id:
                return
                
            from app.models import Citoyen
            commenteur = Citoyen.query.get(commenteur_id)
            commenteur_nom = f"{commenteur.prenom} {commenteur.nom}" if commenteur else "Quelqu'un"
            
            success = send_notification(
                user_id=signalement.citoyenID,
                title="💬 Nouveau commentaire sur votre signalement",
                message=f"{commenteur_nom} a commenté votre signalement",
                entity_type='signalement',
                entity_id=signalement.IDsignalement,
                category='signalement',
                priority='normal',
                data={'action': 'comment', 'commenteur_id': commenteur_id}
            )
            
            if success:
                logger.info(f"✅ Notification commentaire signalement envoyée: {signalement.IDsignalement} -> user {signalement.citoyenID}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification commentaire signalement: {e}")

    @staticmethod
    def notify_new_comment_petition(petition, comment, commenteur_id):
        """Notification pour nouveau commentaire sur pétition"""
        try:
            if petition.citoyenID == commenteur_id:
                return
                
            from app.models import Citoyen
            commenteur = Citoyen.query.get(commenteur_id)
            commenteur_nom = f"{commenteur.prenom} {commenteur.nom}" if commenteur else "Quelqu'un"
            
            success = send_notification(
                user_id=petition.citoyenID,
                title="💬 Nouveau commentaire sur votre pétition",
                message=f"{commenteur_nom} a commenté votre pétition '{petition.titre}'",
                entity_type='petition',
                entity_id=petition.IDpetition,
                category='petition',
                priority='normal',
                data={'action': 'comment', 'commenteur_id': commenteur_id}
            )
            
            if success:
                logger.info(f"✅ Notification commentaire pétition envoyée: {petition.IDpetition} -> user {petition.citoyenID}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification commentaire pétition: {e}")

    @staticmethod
    def notify_new_publication(signalement, publication, autorite_id):
        """Notification pour nouvelle publication d'autorité"""
        try:
            from app.models import Authorite
            autorite = Authorite.query.get(autorite_id)
            autorite_nom = autorite.nom if autorite else "Une autorité"
            
            success = send_notification(
                user_id=signalement.citoyenID,
                title="📢 Réponse officielle à votre signalement",
                message=f"{autorite_nom} a publié une réponse à votre signalement",
                entity_type='publication',
                entity_id=publication.IDpublication,
                category='publication',
                priority='high',
                data={'action': 'authority_response', 'autorite_id': autorite_id, 'signalement_id': signalement.IDsignalement}
            )
            
            if success:
                logger.info(f"✅ Notification publication envoyée: signalement {signalement.IDsignalement} -> user {signalement.citoyenID}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification publication: {e}")

    @staticmethod
    def notify_new_follower(suivi_id, suiveur_id):
        """Notification pour nouveau suiveur"""
        try:
            from app.models import Citoyen
            suiveur = Citoyen.query.get(suiveur_id)
            suiveur_nom = f"{suiveur.prenom} {suiveur.nom}" if suiveur else "Quelqu'un"
            
            success = send_notification(
                user_id=suivi_id,
                title="👤 Nouveau suiveur",
                message=f"{suiveur_nom} vous suit maintenant",
                entity_type='suivre',
                entity_id=suiveur_id,
                category='social',
                priority='low',
                data={'action': 'follow', 'suiveur_id': suiveur_id}
            )
            
            if success:
                logger.info(f"✅ Notification suiveur envoyée: user {suivi_id}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification suiveur: {e}")

    @staticmethod
    def notify_status_change(signalement, new_status, moderateur_id=None):
        """Notification pour changement de statut"""
        try:
            status_messages = {
                'en_cours': '⏳ Votre signalement est en cours de traitement',
                'resolu': '✅ Votre signalement a été résolu',
                'rejete': '❌ Votre signalement a été rejeté',
                'valide': '✔️ Votre signalement a été validé'
            }
            
            message = status_messages.get(new_status, f'📋 Statut de votre signalement changé: {new_status}')
            priority = 'high' if new_status in ['resolu', 'rejete'] else 'normal'
            
            success = send_notification(
                user_id=signalement.citoyenID,
                title="📋 Mise à jour de votre signalement",
                message=message,
                entity_type='signalement',
                entity_id=signalement.IDsignalement,
                category='status',
                priority=priority,
                data={'action': 'status_change', 'old_status': signalement.statut, 'new_status': new_status, 'moderateur_id': moderateur_id}
            )
            
            if success:
                logger.info(f"✅ Notification changement statut envoyée: signalement {signalement.IDsignalement} -> {new_status}")
                
        except Exception as e:
            logger.error(f"❌ Erreur notification changement statut: {e}")

# =======================================
# 3. TYPES DE NOTIFICATIONS COMPLETS
# =======================================

NOTIFICATION_TYPES = {
    'CATEGORIES': {
        'signalement': {
            'name': 'Signalements',
            'description': 'Notifications liées aux signalements citoyens',
            'color': '#e74c3c',
            'icon': '📍',
            'actions': ['vote', 'comment_signalement', 'status_change']
        },
        'petition': {
            'name': 'Pétitions',
            'description': 'Notifications liées aux pétitions',
            'color': '#3498db', 
            'icon': '✍️',
            'actions': ['signature', 'comment_petition']
        },
        'publication': {
            'name': 'Publications',
            'description': 'Réponses officielles des autorités',
            'color': '#2ecc71',
            'icon': '📢',
            'actions': ['authority_response']
        },
        'social': {
            'name': 'Social',
            'description': 'Interactions sociales',
            'color': '#9b59b6',
            'icon': '👥',
            'actions': ['follow', 'mention']
        },
        'status': {
            'name': 'Statuts',
            'description': 'Changements de statut',
            'color': '#f39c12',
            'icon': '📋',
            'actions': ['status_change']
        },
        'system': {
            'name': 'Système',
            'description': 'Notifications système',
            'color': '#34495e',
            'icon': '⚙️',
            'actions': ['maintenance', 'update']
        },
        'admin': {
            'name': 'Administration',
            'description': 'Messages administratifs',
            'color': '#e67e22',
            'icon': '👑',
            'actions': ['announcement', 'warning']
        }
    },
    'PRIORITIES': {
        'low': {'name': 'Faible', 'color': '#95a5a6', 'sound': 'none'},
        'normal': {'name': 'Normal', 'color': '#3498db', 'sound': 'default'},
        'high': {'name': 'Élevée', 'color': '#f39c12', 'sound': 'long'},
        'urgent': {'name': 'Urgent', 'color': '#e74c3c', 'sound': 'urgent'}
    },
    'ACTIONS': {
        'vote': {
            'name': 'Nouveau vote',
            'category': 'signalement',
            'icon': '👍',
            'priority': 'normal',
            'template': '{voter_name} a voté {vote_type} sur votre signalement'
        },
        'signature': {
            'name': 'Nouvelle signature',
            'category': 'petition', 
            'icon': '✍️',
            'priority': 'normal',
            'template': '{signer_name} a signé votre pétition'
        },
        'comment_signalement': {
            'name': 'Commentaire signalement',
            'category': 'signalement',
            'icon': '💬',
            'priority': 'normal',
            'template': '{commenter_name} a commenté votre signalement'
        },
        'comment_petition': {
            'name': 'Commentaire pétition',
            'category': 'petition',
            'icon': '💬', 
            'priority': 'normal',
            'template': '{commenter_name} a commenté votre pétition'
        },
        'authority_response': {
            'name': 'Réponse officielle',
            'category': 'publication',
            'icon': '📢',
            'priority': 'high',
            'template': '{authority_name} a répondu à votre signalement'
        },
        'follow': {
            'name': 'Nouveau suiveur',
            'category': 'social',
            'icon': '👤',
            'priority': 'low',
            'template': '{follower_name} vous suit maintenant'
        },
        'status_change': {
            'name': 'Changement statut',
            'category': 'status',
            'icon': '📋',
            'priority': 'high',
            'template': 'Votre {content_type} est {new_status}'
        },
        'mention': {
            'name': 'Mention',
            'category': 'social',
            'icon': '@',
            'priority': 'normal',
            'template': '{mentioner_name} vous a mentionné'
        }
    }
}