from app import db
from sqlalchemy import or_
from app.models import Petition
from datetime import datetime

def create_petition(
    contact,
    destinataire,
    elements,
    anonymat,
    description,
    nb_commentaire,
    nb_signature,
    nb_partage,
    date_fin,
    objectif_signature,
    titre,
    republierPar,
    cible,
    id_moderateur,
    citoyen_id
):
    media_metadata = []
    for media in elements:
        file_data = media['data']
        file_name = media['filename']
        file_url = upload_to_bunnycdn(file_data, file_name, media['mimetype']) # type: ignore
        media_metadata.append({
            'filename': file_name,
            'url': file_url,
            'mimetype': media['mimetype']
        })

    nouvelle_petition = Petition(
        contact=contact,
        destinataire=destinataire,
        description=description,
        nbSignature=nb_signature,
        nbPartage=nb_partage,
        nbCommetaire=nb_commentaire,
        dateFin=date_fin,
        objectifSignature=objectif_signature,
        titre=titre,
        cible=cible,
        republierPar=republierPar,
        IDmoderateur=id_moderateur,
        citoyenID=citoyen_id,
        dateCreated=datetime.utcnow(),
        anonymat=anonymat
    )

    if media_metadata:
        nouvelle_petition.set_elements(media_metadata)

    db.session.add(nouvelle_petition)
    db.session.commit()
    return nouvelle_petition

def get_petition_by_id(petition_id):
    return Petition.query.get(petition_id)

def get_all_petitions():
    return Petition.query.filter_by(is_deleted=False).order_by(Petition.dateCreated.desc()).all()


def get_petitions_by_citoyen(citoyen_id):
    return Petition.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def update_petition(
    petition_id,
    contact=None,
    destinataire=None,
    elements=None,
    anonymat=None,
    description=None,
    nb_signature=None,
    nb_commentaire=None,
    nb_partage=None,
    date_fin=None,
    objectif_signature=None,
    titre=None,
    republierPar=None,
    cible=None,
    id_moderateur=None
):
    petition = Petition.query.get(petition_id)
    if not petition:
        return None

    if contact is not None:
        petition.contact = contact
    if destinataire is not None:
        petition.destinataire = destinataire
    if elements is not None:
        media_metadata = []
        for media in elements:
            file_data = media['data']
            file_name = media['filename']
            file_url = upload_to_bunnycdn(file_data, file_name, media['mimetype']) # type: ignore
            media_metadata.append({
                'filename': file_name,
                'url': file_url,
                'mimetype': media['mimetype']
            })
        petition.set_elements(media_metadata)
    if anonymat is not None:
        petition.anonymat = anonymat
    if description is not None:
        petition.description = description
    if nb_signature is not None:
        petition.nbSignature = nb_signature
    if nb_commentaire is not None:
        petition.nbCommentaire = nb_commentaire
    if nb_partage is not None:
        petition.nbPartage = nb_partage
    if date_fin is not None:
        petition.dateFin = date_fin
    if objectif_signature is not None:
        petition.objectifSignature = objectif_signature
    if titre is not None:
        petition.titre = titre
    if cible is not None:
        petition.cible = cible
    if republierPar is not None:
        petition.republierPar = republierPar
    if id_moderateur is not None:
        petition.IDmoderateur = id_moderateur

    db.session.commit()
    return petition

def delete_petition(petition_id):
    petition = Petition.query.get(petition_id)
    if petition:
        petition.is_deleted = True
        db.session.commit()
        return True
    return False

def search_petition_by_keyword(keyword):
    return Petition.query.filter(
        or_(
            Petition.description.ilike(f"%{keyword}%"),
            Petition.titre.ilike(f"%{keyword}%")
        )
    ).all()
