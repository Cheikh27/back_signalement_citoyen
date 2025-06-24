# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# db = SQLAlchemy()
# migrate = Migrate()
from app import db
from app.models import Signature
from datetime import datetime

# Service de Création
def create_signature(citoyen_id, petition_id):
    from app.models import Signature, Petition
    from app import db
    from datetime import datetime
    
    # Vérifier si l'utilisateur a déjà signé (et que la signature n'est pas supprimée)
    existing_signature = get_signature_by_petition_and_citoyen(petition_id, citoyen_id)
    if existing_signature:
        raise ValueError("Vous avez déjà signé cette pétition")
    
    # Créer nouvelle signature
    nouvelle_signature = Signature(
        citoyenID=citoyen_id,
        petitionID=petition_id,
        dateCreated=datetime.utcnow(),
        is_deleted=False
    )
    
    db.session.add(nouvelle_signature)
    
    # Incrémenter le compteur de signatures dans la pétition
    petition = Petition.query.get(petition_id)
    if petition:
        petition.nbSignature = (petition.nbSignature or 0) + 1
    
    db.session.commit()
    return nouvelle_signature

# Service de Lecture
def get_signature_by_id(signature_id):
    """Récupère une signature non supprimée par son ID"""
    return Signature.query.filter_by(IDsignature=signature_id, is_deleted=False).first()

def get_all_signatures():
    """Récupère toutes les signatures non supprimées"""
    return Signature.query.filter_by(is_deleted=False).all()

def get_signatures_by_citoyen(citoyen_id):
    """Récupère toutes les signatures non supprimées d'un citoyen"""
    return Signature.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def get_signatures_by_petition(petition_id):
    """Récupère toutes les signatures non supprimées d'une pétition"""
    return Signature.query.filter_by(petitionID=petition_id, is_deleted=False).all()

# Service de Mise à Jour
def update_signature(signature_id, nb_signature=None):
    """Met à jour une signature non supprimée"""
    signature = Signature.query.filter_by(IDsignature=signature_id, is_deleted=False).first()
    if not signature:
        return None

    if nb_signature is not None:
        signature.nbSignature = nb_signature

    db.session.commit()
    return signature

# Service de Suppression Logique
def delete_signature(signature_id):
    """Suppression logique : marque la signature comme supprimée"""
    signature = Signature.query.filter_by(IDsignature=signature_id, is_deleted=False).first()
    if signature:
        # Marquer comme supprimé au lieu de supprimer physiquement
        signature.is_deleted = True
        signature.dateDeleted = datetime.utcnow()  # Optionnel : ajouter une date de suppression
        
        # Décrémenter le compteur de signatures dans la pétition
        from app.models import Petition
        petition = Petition.query.get(signature.petitionID)
        if petition and petition.nbSignature > 0:
            petition.nbSignature -= 1
        
        db.session.commit()
        return True
    return False

# Service de Suppression Physique (si nécessaire pour l'admin)
def delete_signature_permanently(signature_id):
    """Suppression physique définitive de la signature"""
    signature = Signature.query.get(signature_id)
    if signature:
        # Décrémenter le compteur si la signature n'était pas encore marquée comme supprimée
        if not signature.is_deleted:
            from app.models import Petition
            petition = Petition.query.get(signature.petitionID)
            if petition and petition.nbSignature > 0:
                petition.nbSignature -= 1
        
        db.session.delete(signature)
        db.session.commit()
        return True
    return False

# Service de Restauration
def restore_signature(signature_id):
    """Restaure une signature supprimée logiquement"""
    signature = Signature.query.filter_by(IDsignature=signature_id, is_deleted=True).first()
    if signature:
        signature.is_deleted = False
        signature.dateDeleted = None  # Optionnel : réinitialiser la date de suppression
        
        # Incrémenter à nouveau le compteur
        from app.models import Petition
        petition = Petition.query.get(signature.petitionID)
        if petition:
            petition.nbSignature = (petition.nbSignature or 0) + 1
        
        db.session.commit()
        return True
    return False

# Service de Vérification
def get_signature_by_petition_and_citoyen(petition_id, citoyen_id):
    """
    Récupère une signature non supprimée pour une pétition et un citoyen spécifiques.
    """
    from app.models import Signature
    
    return Signature.query.filter_by(
        petitionID=petition_id,
        citoyenID=citoyen_id,
        is_deleted=False
    ).first()

# Service utilitaire pour récupérer les signatures supprimées (pour l'admin)
def get_deleted_signatures():
    """Récupère toutes les signatures supprimées logiquement"""
    return Signature.query.filter_by(is_deleted=True).all()

def get_deleted_signatures_by_petition(petition_id):
    """Récupère les signatures supprimées d'une pétition spécifique"""
    return Signature.query.filter_by(petitionID=petition_id, is_deleted=True).all()