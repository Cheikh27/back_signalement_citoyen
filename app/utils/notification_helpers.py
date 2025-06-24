# app/utils/notification_helpers.py
from app.services import send_notification, send_to_multiple_users, create_notification_from_template
from app.models import User, Citoyen, Authorite
from typing import List

class NotificationHelpers:
    """Classe helper pour simplifier l'envoi de notifications contextuelles"""

    @staticmethod
    def get_users_by_location(location: str, user_type: str = None) -> List[int]:
        """Récupère les utilisateurs par localisation"""
        try:
            query = User.query.filter(
                User.adresse.contains(location), 
                User.is_deleted == False
            )
            
            if user_type:
                query = query.filter(User.type_user == user_type)
            
            users = query.with_entities(User.IDuser).all()
            return [u.IDuser for u in users]
        except Exception as e:
            print(f"Erreur récupération utilisateurs par location: {e}")
            return []

    @staticmethod
    def get_all_authorities() -> List[int]:
        """Récupère toutes les autorités actives"""
        try:
            authorities = Authorite.query.filter_by(is_deleted=False).with_entities(Authorite.IDauthorite).all()
            return [a.IDauthorite for a in authorities]
        except Exception as e:
            print(f"Erreur récupération autorités: {e}")
            return []

    @staticmethod
    def get_all_citizens() -> List[int]:
        """Récupère tous les citoyens actifs"""
        try:
            citizens = Citoyen.query.filter_by(is_deleted=False).with_entities(Citoyen.IDcitoyen).all()
            return [c.IDcitoyen for c in citizens]
        except Exception as e:
            print(f"Erreur récupération citoyens: {e}")
            return []

    @staticmethod
    def get_signalement_followers(signalement_id: int) -> List[int]:
        """Récupère les utilisateurs qui suivent un signalement"""
        try:
            from app.models import CommentaireSignalement, Vote
            
            # Commenteurs
            commenters = CommentaireSignalement.query.filter_by(
                signalementID=signalement_id,
                is_deleted=False
            ).with_entities(CommentaireSignalement.citoyenID).distinct().all()
            
            # Votants
            voters = Vote.query.filter_by(
                signalementID=signalement_id,
                is_deleted=False
            ).with_entities(Vote.citoyenID).distinct().all()
            
            # Combiner et dédupliquer
            followers = list(set([c.citoyenID for c in commenters] + [v.citoyenID for v in voters]))
            return followers
        except Exception as e:
            print(f"Erreur récupération followers signalement: {e}")
            return []

    @staticmethod
    def get_petition_followers(petition_id: int) -> List[int]:
        """Récupère les utilisateurs qui suivent une pétition"""
        try:
            from app.models import CommentairePetition, Signature
            
            # Commenteurs
            commenters = CommentairePetition.query.filter_by(
                petitionID=petition_id,
                is_deleted=False
            ).with_entities(CommentairePetition.citoyenID).distinct().all()
            
            # Signataires
            signers = Signature.query.filter_by(
                petitionID=petition_id,
                is_deleted=False
            ).with_entities(Signature.citoyenID).distinct().all()
            
            # Combiner et dédupliquer
            followers = list(set([c.citoyenID for c in commenters] + [s.citoyenID for s in signers]))
            return followers
        except Exception as e:
            print(f"Erreur récupération followers pétition: {e}")
            return []

    @staticmethod
    def get_publication_followers(publication_id: int) -> List[int]:
        """Récupère les utilisateurs qui suivent une publication"""
        try:
            from app.models import CommentairePublication, Appreciation
            
            # Commenteurs
            commenters = CommentairePublication.query.filter_by(
                publicationID=publication_id,
                is_deleted=False
            ).with_entities(CommentairePublication.citoyenID).distinct().all()
            
            # Utilisateurs qui ont apprécié
            appreciators = Appreciation.query.filter_by(
                PublicationID=publication_id
            ).with_entities(Appreciation.citoyenID).distinct().all()
            
            # Combiner et dédupliquer
            followers = list(set([c.citoyenID for c in commenters] + [a.citoyenID for a in appreciators]))
            return followers
        except Exception as e:
            print(f"Erreur récupération followers publication: {e}")
            return []

# =====================================
# FONCTIONS DE NOTIFICATION SPÉCIFIQUES
# =====================================

def notify_new_signalement(signalement):
    """Notifie la création d'un nouveau signalement"""
    try:
        # Notifier les autorités de la zone
        location = signalement.cible
        recipients = NotificationHelpers.get_users_by_location(location, 'authorite')
        
        if not recipients:
            # Fallback : toutes les autorités
            recipients = NotificationHelpers.get_all_authorities()
        
        # Limiter à 50 pour éviter le spam
        recipients = recipients[:50]
        
        if recipients:
            success_count = send_to_multiple_users(
                user_ids=recipients,
                title=f"Nouveau signalement: {signalement.typeSignalement}",
                message=f"Un signalement de type '{signalement.typeSignalement}' a été créé dans la zone {location}.",
                entity_type='signalement',
                entity_id=signalement.IDsignalement,
                priority='normal',
                category='signalement',
                data={
                    'signalement_id': str(signalement.IDsignalement),
                    'type_signalement': signalement.typeSignalement,
                    'location': location
                }
            )
            print(f"✅ Notification nouveau signalement envoyée à {success_count} autorités")
        
    except Exception as e:
        print(f"❌ Erreur notification nouveau signalement: {e}")

def notify_signalement_comment(commentaire, signalement):
    """Notifie un nouveau commentaire sur signalement"""
    try:
        # Destinataires : créateur + autres commenteurs/votants
        recipients = [signalement.citoyenID]  # Créateur
        recipients.extend(NotificationHelpers.get_signalement_followers(signalement.IDsignalement))
        
        # Supprimer le commenteur actuel et dédupliquer
        recipients = list(set(recipients))
        if commentaire.citoyenID in recipients:
            recipients.remove(commentaire.citoyenID)
        
        if recipients:
            success_count = send_to_multiple_users(
                user_ids=recipients,
                title="Nouveau commentaire sur signalement",
                message="Un nouveau commentaire a été ajouté sur un signalement que vous suivez.",
                entity_type='signalement',
                entity_id=signalement.IDsignalement,
                priority='normal',
                category='signalement',
                data={
                    'signalement_id': str(signalement.IDsignalement),
                    'comment_id': str(commentaire.IDcommentaire)
                }
            )
            print(f"✅ Notification commentaire signalement envoyée à {success_count} utilisateurs")
            
    except Exception as e:
        print(f"❌ Erreur notification commentaire signalement: {e}")

def notify_new_petition(petition):
    """Notifie la création d'une nouvelle pétition"""
    try:
        # Notifier les citoyens de la zone (limité pour éviter le spam)
        location = getattr(petition, 'cible', 'public')
        if location != 'public':
            recipients = NotificationHelpers.get_users_by_location(location, 'citoyen')[:100]
        else:
            # Pour les pétitions publiques, notifier un échantillon
            recipients = NotificationHelpers.get_all_citizens()[:50]
        
        if recipients:
            success_count = send_to_multiple_users(
                user_ids=recipients,
                title=f"Nouvelle pétition: {petition.titre}",
                message=f"Une nouvelle pétition '{petition.titre}' a été lancée et mérite votre attention.",
                entity_type='petition',
                entity_id=petition.IDpetition,
                priority='normal',
                category='petition',
                data={
                    'petition_id': str(petition.IDpetition),
                    'titre': petition.titre
                }
            )
            print(f"✅ Notification nouvelle pétition envoyée à {success_count} citoyens")
            
    except Exception as e:
        print(f"❌ Erreur notification nouvelle pétition: {e}")

def notify_petition_signature(signature, petition):
    """Notifie une nouvelle signature de pétition"""
    try:
        # Notifier seulement le créateur de la pétition
        if petition.citoyenID != signature.citoyenID:
            success = send_notification(
                user_id=petition.citoyenID,
                title="Nouvelle signature sur votre pétition",
                message=f"Votre pétition '{petition.titre}' a reçu une nouvelle signature ! Total: {petition.nbSignature or 1}",
                entity_type='petition',
                entity_id=petition.IDpetition,
                priority='normal',
                category='petition',
                data={
                    'petition_id': str(petition.IDpetition),
                    'new_signature_count': str(petition.nbSignature or 1)
                }
            )
            if success:
                print(f"✅ Notification signature pétition envoyée au créateur")
            
    except Exception as e:
        print(f"❌ Erreur notification signature pétition: {e}")

def notify_petition_comment(commentaire, petition):
    """Notifie un nouveau commentaire sur pétition"""
    try:
        # Destinataires : créateur + followers
        recipients = [petition.citoyenID]  # Créateur
        recipients.extend(NotificationHelpers.get_petition_followers(petition.IDpetition))
        
        # Supprimer le commenteur actuel et dédupliquer
        recipients = list(set(recipients))
        if commentaire.citoyenID in recipients:
            recipients.remove(commentaire.citoyenID)
        
        if recipients:
            success_count = send_to_multiple_users(
                user_ids=recipients,
                title="Nouveau commentaire sur pétition",
                message=f"Un nouveau commentaire a été ajouté sur la pétition '{petition.titre}'.",
                entity_type='petition',
                entity_id=petition.IDpetition,
                priority='normal',
                category='petition',
                data={
                    'petition_id': str(petition.IDpetition),
                    'comment_id': str(commentaire.IDcommentaire)
                }
            )
            print(f"✅ Notification commentaire pétition envoyée à {success_count} utilisateurs")
            
    except Exception as e:
        print(f"❌ Erreur notification commentaire pétition: {e}")

def notify_new_publication(publication, signalement):
    """Notifie une nouvelle publication (réponse d'autorité)"""
    try:
        # Destinataires : créateur du signalement + followers
        recipients = [signalement.citoyenID]  # Créateur du signalement
        recipients.extend(NotificationHelpers.get_signalement_followers(signalement.IDsignalement))
        
        # Supprimer l'autorité qui publie et dédupliquer
        recipients = list(set(recipients))
        if publication.autoriteID in recipients:
            recipients.remove(publication.autoriteID)
        
        if recipients:
            success_count = send_to_multiple_users(
                user_ids=recipients,
                title="Réponse officielle disponible",
                message="Une autorité a publié une réponse concernant un signalement que vous suivez.",
                entity_type='publication',
                entity_id=publication.IDpublication,
                priority='high',
                category='publication',
                data={
                    'publication_id': str(publication.IDpublication),
                    'signalement_id': str(signalement.IDsignalement)
                }
            )
            print(f"✅ Notification nouvelle publication envoyée à {success_count} utilisateurs")
            
    except Exception as e:
        print(f"❌ Erreur notification nouvelle publication: {e}")

def notify_publication_comment(commentaire, publication):
    """Notifie un nouveau commentaire sur publication"""
    try:
        # Destinataires : autorité qui a publié + followers
        recipients = [publication.autoriteID]  # Autorité
        recipients.extend(NotificationHelpers.get_publication_followers(publication.IDpublication))
        
        # Supprimer le commenteur actuel et dédupliquer
        recipients = list(set(recipients))
        if commentaire.citoyenID in recipients:
            recipients.remove(commentaire.citoyenID)
        
        if recipients:
            success_count = send_to_multiple_users(
                user_ids=recipients,
                title="Nouveau commentaire sur publication",
                message="Un nouveau commentaire a été ajouté sur une publication officielle.",
                entity_type='publication',
                entity_id=publication.IDpublication,
                priority='normal',
                category='publication',
                data={
                    'publication_id': str(publication.IDpublication),
                    'comment_id': str(commentaire.IDcommentaire)
                }
            )
            print(f"✅ Notification commentaire publication envoyée à {success_count} utilisateurs")
            
    except Exception as e:
        print(f"❌ Erreur notification commentaire publication: {e}")

def notify_vote_on_signalement(vote, signalement):
    """Notifie un nouveau vote sur signalement"""
    try:
        # Notifier seulement le créateur du signalement
        if signalement.citoyenID != vote.citoyenID:
            vote_type = "positif" if vote.types == "positif" else "négatif"
            success = send_notification(
                user_id=signalement.citoyenID,
                title=f"Nouveau vote {vote_type} sur votre signalement",
                message=f"Votre signalement a reçu un nouveau vote {vote_type}.",
                entity_type='signalement',
                entity_id=signalement.IDsignalement,
                priority='normal',
                category='signalement',
                data={
                    'signalement_id': str(signalement.IDsignalement),
                    'vote_type': vote_type,
                    'vote_id': str(vote.IDvote)
                }
            )
            if success:
                print(f"✅ Notification vote {vote_type} envoyée au créateur du signalement")
            
    except Exception as e:
        print(f"❌ Erreur notification vote signalement: {e}")

def notify_appreciation_on_publication(appreciation, publication):
    """Notifie une nouvelle appréciation sur publication"""
    try:
        # Notifier l'autorité qui a publié
        if publication.autoriteID != appreciation.citoyenID:
            success = send_notification(
                user_id=publication.autoriteID,
                title="Nouvelle appréciation sur votre publication",
                message="Votre publication a reçu une nouvelle appréciation.",
                entity_type='publication',
                entity_id=publication.IDpublication,
                priority='normal',
                category='publication',
                data={
                    'publication_id': str(publication.IDpublication),
                    'appreciation_id': str(appreciation.IDappreciation)
                }
            )
            if success:
                print(f"✅ Notification appréciation envoyée à l'autorité")
            
    except Exception as e:
        print(f"❌ Erreur notification appréciation publication: {e}")

def notify_status_change(entity_type: str, entity_id: int, old_status: str, new_status: str, user_id: int):
    """Notifie un changement de statut"""
    try:
        status_messages = {
            'en_cours': 'en cours de traitement',
            'resolu': 'résolu', 
            'rejete': 'rejeté',
            'en_attente': 'en attente de validation',
            'accepte': 'accepté',
            'ferme': 'fermé'
        }
        
        success = send_notification(
            user_id=user_id,
            title=f"Mise à jour de votre {entity_type}",
            message=f"Le statut de votre {entity_type} est maintenant: {status_messages.get(new_status, new_status)}",
            entity_type=entity_type,
            entity_id=entity_id,
            priority='high',
            category='status',
            data={
                f'{entity_type}_id': str(entity_id),
                'old_status': old_status,
                'new_status': new_status
            }
        )
        if success:
            print(f"✅ Notification changement statut {entity_type} envoyée")
        
    except Exception as e:
        print(f"❌ Erreur notification changement statut: {e}")

def notify_mention_user(mentioned_user_id: int, mentioner_id: int, content_type: str, content_id: int):
    """Notifie qu'un utilisateur a été mentionné"""
    try:
        success = send_notification(
            user_id=mentioned_user_id,
            title="Vous avez été mentionné",
            message="Vous avez été mentionné dans un commentaire.",
            entity_type=content_type,
            entity_id=content_id,
            priority='normal',
            category='social',
            data={
                'mentioner_id': str(mentioner_id),
                'content_type': content_type,
                'content_id': str(content_id)
            }
        )
        if success:
            print(f"✅ Notification mention envoyée à l'utilisateur {mentioned_user_id}")
        
    except Exception as e:
        print(f"❌ Erreur notification mention: {e}")

def notify_system_message(user_ids: List[int], title: str, message: str, priority: str = 'high'):
    """Envoie une notification système à plusieurs utilisateurs"""
    try:
        success_count = send_to_multiple_users(
            user_ids=user_ids,
            title=title,
            message=message,
            priority=priority,
            category='system',
            data={'system_message': True}
        )
        print(f"✅ Notification système envoyée à {success_count} utilisateurs")
        return success_count
        
    except Exception as e:
        print(f"❌ Erreur notification système: {e}")
        return 0