# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Signalement
from datetime import datetime

# Service de Création
def create_signalement(description, elements, statut, nb_vote_positif, nb_vote_negatif, cible, id_moderateur, citoyen_id):
    nouveau_signalement = Signalement(
        description=description,
        elements=elements,
        statut=statut,
        nbVotePositif=nb_vote_positif,
        nbVoteNegatif=nb_vote_negatif,
        cible=cible,
        IDmoderateur=id_moderateur,
        citoyenID=citoyen_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_signalement)
    db.session.commit()
    return nouveau_signalement

# Service de Lecture
def get_signalement_by_id(signalement_id):
    return Signalement.query.get(signalement_id)

def get_all_signalements():
    return Signalement.query.filter_by(is_deleted=False).all()

def get_signalements_by_citoyen(citoyen_id):
    return Signalement.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

# Service de Mise à Jour
def update_signalement(signalement_id, description=None, elements=None, statut=None, nb_vote_positif=None, nb_vote_negatif=None, cible=None, id_moderateur=None):
    signalement = Signalement.query.get(signalement_id)
    if not signalement:
        return None

    if description is not None:
        signalement.description = description
    if elements is not None:
        signalement.elements = elements
    if statut is not None:
        signalement.statut = statut
    if nb_vote_positif is not None:
        signalement.nbVotePositif = nb_vote_positif
    if nb_vote_negatif is not None:
        signalement.nbVoteNegatif = nb_vote_negatif
    if cible is not None:
        signalement.cible = cible
    if id_moderateur is not None:
        signalement.IDmoderateur = id_moderateur

    db.session.commit()
    return signalement

# Service de Suppression Logique
def delete_signalement(signalement_id):
    signalement = Signalement.query.get(signalement_id)
    if signalement:
        signalement.is_deleted = True
        signalement.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False
