from app import db
from datetime import datetime
from app.models import Suivre

# Service de Création
def create_suivre(suiveur_id, suivis_id):
    nouvel_suivre = Suivre(
        suiveurID=suiveur_id,
        suivisID=suivis_id,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouvel_suivre)
    db.session.commit()
    return nouvel_suivre

# Service de Lecture
def get_suivre_by_id(suivis_id):
    return Suivre.query.get(suivis_id)

def get_all_suivres():
    return Suivre.query.filter_by(is_deleted=False).all()

def get_suiveur_by_suivis(suivis_id):
    return Suivre.query.filter_by(suivisID=suivis_id, is_deleted=False).all()

def get_suivis_by_suiveur(suiveur_id):
    return Suivre.query.filter_by(suiveurID=suiveur_id, is_deleted=False).all()

# Service de Mise à Jour
def update_suivre(suivre_id,suiveur_id=None,  suivis_id=None):
    suivre = Suivre.query.get(suivre_id)
    if not suivre:
        return None

    if suiveur_id is not None:
        suivre.suiveurID = suiveur_id
    if suivis_id is not None:
        suivre.suivisID = suivis_id

    db.session.commit()
    return suivre

# Service de Suppression
def delete_suivre(suivre_id):
    suivre = Suivre.query.filter_by(IDsuivre=suivre_id , is_deleted=False ).first()
    if suivre:
        suivre.is_deleted = True
        suivre.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False

# Fonction pour vérifier si un utilisateur suit un autre
def check_if_following(suiveur_id, suivis_id):
    """
    Vérifie si suiveur_id suit suivis_id
    """
    relation = Suivre.query.filter_by(
        suiveurID=suiveur_id,
        suivisID=suivis_id,
        is_deleted=False
    ).first()
    
    return relation is not None, relation.IDsuivre if relation else None