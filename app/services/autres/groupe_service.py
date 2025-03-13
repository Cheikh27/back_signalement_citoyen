# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate

# db = SQLAlchemy()
# migrate = Migrate()
from app import db


from app.models import Groupe
from datetime import datetime

# Service de Création
def create_groupe(nom, description, image, admin):
    nouveau_groupe = Groupe(
        nom=nom,
        description=description,
        image=image,
        admin=admin,
        dateCreated=datetime.utcnow()
    )
    db.session.add(nouveau_groupe)
    db.session.commit()
    return nouveau_groupe

# Service de Lecture
def get_groupe_by_id(groupe_id):
    return Groupe.query.get(groupe_id)

def get_all_groupes():
    return Groupe.query.filter_by(is_deleted=False).all()

# Service de Mise à Jour
def update_groupe(groupe_id, nom=None, description=None, statut=None, image=None, admin=None):
    groupe = Groupe.query.get(groupe_id)
    if not groupe:
        return None

    if nom is not None:
        groupe.nom = nom
    if description is not None:
        groupe.description = description
    if statut is not None:
        groupe.statut = statut
    if image is not None:
        groupe.image = image
    if admin is not None:
        groupe.admin = admin

    db.session.commit()
    return groupe

# Service de Suppression Logique
def delete_groupe(groupe_id):
    groupe = Groupe.query.get(groupe_id)
    if groupe:
        groupe.is_deleted = True
        groupe.dateDeleted = datetime.utcnow()
        db.session.commit()
        return True
    return False
