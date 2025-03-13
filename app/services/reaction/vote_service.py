# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Vote
from datetime import datetime

# Service de Création
def create_vote(citoyen_id, signalement_id):
    nouveau_vote = Vote(
        citoyenID=citoyen_id,
        signalementID=signalement_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_vote)
    db.session.commit()
    return nouveau_vote

# Service de Lecture
def get_vote_by_id(vote_id):
    return Vote.query.get(vote_id)

def get_all_votes():
    return Vote.query.all()

def get_votes_by_citoyen(citoyen_id):
    return Vote.query.filter_by(citoyenID=citoyen_id).all()

def get_votes_by_signalement(signalement_id):
    return Vote.query.filter_by(signalementID=signalement_id).all()

# Service de Suppression
def delete_vote(vote_id):
    vote = Vote.query.get(vote_id)
    if vote:
        db.session.delete(vote)
        db.session.commit()
        return True
    return False
