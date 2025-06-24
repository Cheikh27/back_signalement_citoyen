from flask_caching import logger
from app import db
from app.models import Vote
from datetime import datetime

def create_vote(citoyen_id, signalement_id, types):
    """
    Crée un vote s’il n’existe pas déjà un vote actif.

    """
    try:
        existing_vote = Vote.query.filter_by(
            citoyenID=citoyen_id,
            signalementID=signalement_id,
            is_deleted=False
        ).first()

        if existing_vote:
            return existing_vote, False

        nouveau_vote = Vote(
            citoyenID=citoyen_id,
            signalementID=signalement_id,
            types=types,
            dateCreated=datetime.utcnow(),
            is_deleted=False
        )

        db.session.add(nouveau_vote)
        db.session.commit()
        return nouveau_vote, True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création du vote: {str(e)}")
        raise



# Service de Lecture
def get_vote_by_id(vote_id):
    return Vote.query.get(vote_id)

def get_all_votes():
    return Vote.query.filter_by(is_deleted=False).all()

def get_votes_by_citoyen(citoyen_id):
    return Vote.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def get_votes_by_signalement(signalement_id):
    return Vote.query.filter_by(signalementID=signalement_id, is_deleted=False).all()

# Service de Suppression Logique
def delete_vote(vote_id):
    vote = Vote.query.get(vote_id)
    if vote:
        vote.is_deleted = True
        vote.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False



# Service de Mise à Jour
def update_vote(vote_id, types=None):
    vote = Vote.query.get(vote_id)
    if not vote:
        return None

    if types is not None:
        vote.types = types

    db.session.commit()
    return vote

def get_user_vote_for_signalement(citoyen_id, signalement_id):
    """
    Récupère le vote actif (non supprimé) d’un citoyen pour un signalement.
    """
    try:
        vote = Vote.query.filter_by(
            citoyenID=citoyen_id,
            signalementID=signalement_id,
            is_deleted=False
        ).first()
        
        logger.info(f"Vote récupéré pour citoyenID={citoyen_id}, signalementID={signalement_id} => {vote}")
        return vote

    except Exception as e:
        logger.error(f"Erreur dans get_user_vote_for_signalement: {str(e)}")
        return None
