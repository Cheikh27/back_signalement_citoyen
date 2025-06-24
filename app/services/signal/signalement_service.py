from app import db
from sqlalchemy import or_
from app.models import Signalement
from datetime import datetime
from app.supabase_media_service import SupabaseMediaService

# Initialiser le service média pour le serveur
from app.supabase_media_service import get_media_service
media_service = get_media_service()  # Utilise automatiquement SERVICE_ROLE

# def create_signalement(
#     citoyen_id,
#     typeSignalement,
#     description,
#     elements,
#     anonymat,
#     nb_vote_positif,
#     nb_vote_negatif,
#     cible,
#     republierPar,
#     id_moderateur
# ):
#     """
#     Création de signalement avec Supabase Storage
#     """
#     print(f"🚀 Création signalement avec Supabase pour citoyen {citoyen_id}")
    
#     media_metadata = []
#     failed_uploads = []
    
#     # Traitement des médias
#     for i, media in enumerate(elements):
#         try:
#             # Extraire les données
#             file_data = media['data']
#             file_name = media['filename']
#             mimetype = media.get('mimetype', 'application/octet-stream')
            
#             print(f"📤 Upload {i+1}/{len(elements)}: {file_name}")
            
#             # Upload vers Supabase
#             metadata = media_service.upload_media(
#                 file_data=file_data,
#                 original_filename=file_name,
#                 mimetype=mimetype,
#                 citoyen_id=citoyen_id
#             )
            
#             media_metadata.append(metadata)
#             print(f"✅ Upload réussi: {file_name}")
            
#         except Exception as e:
#             print(f"❌ Erreur upload {media.get('filename', 'unknown')}: {e}")
#             failed_uploads.append({
#                 'filename': media.get('filename', 'unknown'),
#                 'error': str(e)
#             })
#             continue
    
#     # Créer le signalement même si certains uploads ont échoué
#     nouveau_signalement = Signalement(
#         typeSignalement=typeSignalement,
#         description=description,
#         cible=cible,
#         citoyenID=citoyen_id,
#         anonymat=anonymat,
#         nbVotePositif=nb_vote_positif,
#         nbVoteNegatif=nb_vote_negatif,
#         republierPar=republierPar,
#         IDmoderateur=id_moderateur,
#         dateCreated=datetime.utcnow()
#     )
    
#     # Sauvegarder les métadonnées des médias réussis
#     if media_metadata:
#         nouveau_signalement.set_elements(media_metadata)
    
#     try:
#         db.session.add(nouveau_signalement)
#         db.session.commit()
        
#         print(f"✅ Signalement créé: ID {nouveau_signalement.IDsignalement}")
#         print(f"📊 Médias uploadés: {len(media_metadata)}/{len(elements)}")
        
#         if failed_uploads:
#             print(f"⚠️ Uploads échoués: {len(failed_uploads)}")
#             for failed in failed_uploads:
#                 print(f"   - {failed['filename']}: {failed['error']}")
        
#         return {
#             'signalement': nouveau_signalement,
#             'uploaded_media': len(media_metadata),
#             'failed_uploads': failed_uploads
#         }
        
#     except Exception as e:
#         # En cas d'erreur DB, nettoyer les médias uploadés
#         print(f"❌ Erreur DB, nettoyage des médias uploadés")
#         for metadata in media_metadata:
#             if 'storage_path' in metadata:
#                 media_service.delete_media(metadata['storage_path'])
        
#         db.session.rollback()
#         raise e


# Dans services.py - CORRECTION de create_signalement pour les republications

def create_signalement(
    citoyen_id,
    typeSignalement,
    description,
    elements,
    anonymat,
    nb_vote_positif,
    nb_vote_negatif,
    cible,
    republierPar,
    id_moderateur
):
    """
    Création de signalement avec Supabase Storage - CORRIGÉ pour republications
    """
    print(f"🚀 Création signalement avec Supabase pour citoyen {citoyen_id}")
    print(f"📊 Éléments reçus: {len(elements)}")
    
    media_metadata = []
    failed_uploads = []
    
    # Traitement des médias
    for i, media in enumerate(elements):
        try:
            print(f"📤 Traitement média {i+1}/{len(elements)}: {media.get('filename', 'unknown')}")
            print(f"🔍 Clés disponibles: {list(media.keys())}")
            
            # ✅ CORRECTION: Distinction entre upload normal et republication
            if 'data' in media:
                # ═══ CAS 1: Upload normal avec données binaires ═══
                print("📥 Upload normal avec données binaires")
                
                file_data = media['data']
                file_name = media['filename']
                mimetype = media.get('mimetype', 'application/octet-stream')
                
                print(f"📤 Upload {i+1}/{len(elements)}: {file_name}")
                
                # Upload vers Supabase
                metadata = media_service.upload_media(
                    file_data=file_data,
                    original_filename=file_name,
                    mimetype=mimetype,
                    citoyen_id=citoyen_id
                )
                
                media_metadata.append(metadata)
                print(f"✅ Upload réussi: {file_name}")
                
            elif 'url' in media and 'storage_path' in media:
                # ═══ CAS 2: Republication avec métadonnées existantes ═══
                print("🔄 Republication - médias déjà uploadés sur Supabase")
                
                # Les médias sont déjà sur Supabase, on garde les métadonnées
                republication_metadata = {
                    'filename': media.get('filename'),
                    'storage_path': media.get('storage_path'),
                    'url': media.get('url'),
                    'display_url': media.get('display_url'),
                    'download_url': media.get('download_url'),
                    'thumbnail_url': media.get('thumbnail_url'),
                    'preview_url': media.get('preview_url'),
                    'mimetype': media.get('mimetype'),
                    'category': media.get('category', 'others'),
                    'size': media.get('size'),
                    'hash': media.get('hash'),
                    'uploaded_at': media.get('upload_date'),
                    'upload_context': 'republication',
                    'provider': 'supabase',
                    'bucket': 'signalements',
                    'citoyen_id': citoyen_id,
                    'file_extension': media.get('filename', '').split('.')[-1] if '.' in media.get('filename', '') else '',
                    'is_image': media.get('is_image', False),
                    'is_video': media.get('is_video', False),
                    'is_document': media.get('is_document', False),
                    'is_audio': media.get('is_audio', False)
                }
                
                media_metadata.append(republication_metadata)
                print(f"✅ Métadonnées republication conservées: {media.get('filename')}")
                
            elif 'url' in media:
                # ═══ CAS 3: URL simple (fallback) ═══
                print("🔗 URL simple - création métadonnées basiques")
                
                basic_metadata = {
                    'filename': media.get('filename', 'unknown'),
                    'url': media.get('url'),
                    'display_url': media.get('display_url', media.get('url')),
                    'download_url': media.get('download_url', media.get('url')),
                    'mimetype': media.get('mimetype', 'application/octet-stream'),
                    'category': media.get('category', 'others'),
                    'size': media.get('size', 0),
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'upload_context': 'external_url',
                    'provider': 'external',
                    'citoyen_id': citoyen_id,
                    'is_image': media.get('is_image', False),
                    'is_video': media.get('is_video', False),
                    'is_document': media.get('is_document', False),
                    'is_audio': media.get('is_audio', False)
                }
                
                media_metadata.append(basic_metadata)
                print(f"✅ Métadonnées basiques créées: {media.get('filename')}")
                
            else:
                # ═══ CAS 4: Format non reconnu ═══
                print(f"❌ Format de média non reconnu: {media}")
                failed_uploads.append({
                    'filename': media.get('filename', 'unknown'),
                    'error': 'Format de données non reconnu'
                })
                continue
            
        except Exception as e:
            print(f"❌ Erreur traitement {media.get('filename', 'unknown')}: {e}")
            failed_uploads.append({
                'filename': media.get('filename', 'unknown'),
                'error': str(e)
            })
            continue
    
    # Créer le signalement même si certains uploads ont échoué
    nouveau_signalement = Signalement(
        typeSignalement=typeSignalement,
        description=description,
        cible=cible,
        citoyenID=citoyen_id,
        anonymat=anonymat,
        nbVotePositif=nb_vote_positif,
        nbVoteNegatif=nb_vote_negatif,
        republierPar=republierPar,
        IDmoderateur=id_moderateur,
        dateCreated=datetime.utcnow()
    )
    
    # Sauvegarder les métadonnées des médias réussis
    if media_metadata:
        nouveau_signalement.set_elements(media_metadata)
        print(f"💾 Métadonnées sauvegardées: {len(media_metadata)} médias")
    
    try:
        db.session.add(nouveau_signalement)
        db.session.commit()
        
        print(f"✅ Signalement créé: ID {nouveau_signalement.IDsignalement}")
        print(f"📊 Médias sauvegardés: {len(media_metadata)}/{len(elements)}")
        
        if failed_uploads:
            print(f"⚠️ Uploads échoués: {len(failed_uploads)}")
            for failed in failed_uploads:
                print(f"   - {failed['filename']}: {failed['error']}")
        
        # ✅ CORRECTION: Compter correctement les médias uploadés
        successful_uploads = len(media_metadata)
        
        return {
            'signalement': nouveau_signalement,
            'uploaded_media': successful_uploads,  # ← CORRECTION: compter les métadonnées sauvées
            'failed_uploads': failed_uploads
        }
        
    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        
        # En cas d'erreur DB, nettoyer les médias uploadés (seulement pour les nouveaux uploads)
        for metadata in media_metadata:
            if (metadata.get('upload_context') != 'republication' and 
                metadata.get('storage_path')):
                try:
                    media_service.delete_media(metadata['storage_path'])
                    print(f"🧹 Nettoyage: {metadata['filename']}")
                except:
                    pass
        
        db.session.rollback()
        raise e
    
    
def update_signalement(
    signalement_id,
    typeSignalement=None,
    description=None,
    elements=None,
    statut=None,
    nb_vote_positif=None,
    nb_vote_negatif=None,
    cible=None,
    id_moderateur=None,
    republierPar=None
):
    """
    Met à jour un signalement avec Supabase Storage
    """
    signalement = Signalement.query.get(signalement_id)
    if not signalement:
        return None

    # Si on met à jour les éléments, supprimer les anciens médias de Supabase
    if elements is not None:
        # Récupérer les anciens éléments pour supprimer les fichiers
        old_elements = signalement.get_elements()
        for old_element in old_elements:
            if 'storage_path' in old_element:
                media_service.delete_media(old_element['storage_path'])
        
        # Traiter les nouveaux éléments
        media_metadata = []
        for media in elements:
            try:
                file_data = media['data']
                file_name = media['filename']
                mimetype = media.get('mimetype', 'application/octet-stream')
                
                # Upload vers Supabase
                metadata = media_service.upload_media(
                    file_data=file_data,
                    original_filename=file_name,
                    mimetype=mimetype,
                    citoyen_id=signalement.citoyenID
                )
                
                media_metadata.append(metadata)
                
            except Exception as e:
                print(f"❌ Erreur upload lors de la mise à jour: {e}")
                continue
        
        signalement.set_elements(media_metadata)

    # Mettre à jour les autres champs
    if typeSignalement is not None:
        signalement.typeSignalement = typeSignalement
    if description is not None:
        signalement.description = description
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
    if republierPar is not None:
        signalement.republierPar = republierPar

    db.session.commit()
    return signalement

def get_signalement_with_fresh_urls(signalement_id):
    """Récupère un signalement avec URLs de téléchargement actualisées"""
    signalement = Signalement.query.get(signalement_id)
    if not signalement or signalement.is_deleted:
        return None
    
    # Générer des URLs fraîches
    fresh_elements = signalement.get_fresh_download_urls()
    
    return {
        'signalement': signalement,
        'elements': fresh_elements
    }

def delete_signalement(signalement_id):
    """Supprime un signalement et ses médias associés (soft delete)"""
    signalement = Signalement.query.get(signalement_id)
    if not signalement:
        return False
    
    # Supprimer les médias de Supabase
    signalement.cleanup_media()
    
    # Marquer comme supprimé (soft delete)
    signalement.is_deleted = True
    signalement.dateDeleted = datetime.utcnow()
    
    db.session.commit()
    return True

def hard_delete_signalement(signalement_id):
    """Suppression définitive d'un signalement"""
    signalement = Signalement.query.get(signalement_id)
    if not signalement:
        return False
    
    # Supprimer les médias de Supabase
    signalement.cleanup_media()
    
    # Suppression définitive de la base de données
    db.session.delete(signalement)
    db.session.commit()
    return True

# Services de lecture
def get_signalement_by_id(signalement_id):
    """Récupère un signalement par son ID"""
    return Signalement.query.get(signalement_id)

def get_all_signalements():
    """Récupère tous les signalements non supprimés"""
    return Signalement.query.filter_by(is_deleted=False).order_by(Signalement.dateCreated.desc()).all()

def get_signalements_by_citoyen(citoyen_id):
    """Récupère les signalements d'un citoyen"""
    return Signalement.query.filter_by(citoyenID=citoyen_id, is_deleted=False).all()

def get_signalements_by_status(statut):
    """Récupère les signalements par statut"""
    return Signalement.query.filter_by(statut=statut, is_deleted=False).all()

def get_signalements_by_type(type_signalement):
    """Récupère les signalements par type"""
    return Signalement.query.filter_by(typeSignalement=type_signalement, is_deleted=False).all()

# Service de recherche
def search_signalements_by_keyword(keyword):
    """Recherche des signalements par mot-clé"""
    return Signalement.query.filter(
        or_(
            Signalement.description.ilike(f"%{keyword}%"),
            Signalement.cible.ilike(f"%{keyword}%"),
            Signalement.typeSignalement.ilike(f"%{keyword}%")
        ),
        Signalement.is_deleted == False
    ).all()

# Statistiques
def get_signalement_stats():
    """Retourne les statistiques des signalements"""
    total = Signalement.query.filter_by(is_deleted=False).count()
    en_cours = Signalement.query.filter_by(statut='en_cours', is_deleted=False).count()
    resolus = Signalement.query.filter_by(statut='resolu', is_deleted=False).count()
    rejetes = Signalement.query.filter_by(statut='rejete', is_deleted=False).count()
    
    return {
        'total': total,
        'en_cours': en_cours,
        'resolus': resolus,
        'rejetes': rejetes,
        'taux_resolution': round((resolus / total * 100), 2) if total > 0 else 0
    }

def get_user_signalement_stats(citoyen_id):
    """Statistiques des signalements d'un utilisateur"""
    signalements = get_signalements_by_citoyen(citoyen_id)
    
    total = len(signalements)
    en_cours = len([s for s in signalements if s.statut == 'en_cours'])
    resolus = len([s for s in signalements if s.statut == 'resolu'])
    total_votes_positifs = sum(s.nbVotePositif for s in signalements)
    total_votes_negatifs = sum(s.nbVoteNegatif for s in signalements)
    total_media = sum(s.get_media_count() for s in signalements)
    
    return {
        'total_signalements': total,
        'en_cours': en_cours,
        'resolus': resolus,
        'total_votes_positifs': total_votes_positifs,
        'total_votes_negatifs': total_votes_negatifs,
        'total_media_uploads': total_media,
        'moyenne_votes_positifs': round(total_votes_positifs / total, 2) if total > 0 else 0
    }