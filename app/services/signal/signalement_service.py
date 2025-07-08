from app import db
from sqlalchemy import or_
from app.models import Signalement
from datetime import datetime
from app.supabase_media_service import SupabaseMediaService

# Initialiser le service média pour le serveur
from app.supabase_media_service import get_media_service
from model_priorisation.priorite import CONTENT_SCORES, GRAVITY_SCORES, LOCATION_SCORES, URGENCY_SCORES, WEIGHTS
media_service = get_media_service()  


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
    id_moderateur,
    location_data=None,
    priorite=None
   
):
    """
    Création de signalement avec Supabase Storage et géolocalisation
    """
    print(f"🚀 Création signalement avec Supabase pour citoyen {citoyen_id}")
    print(f"📊 Éléments reçus: {len(elements)}")
    print(f"📍 Localisation: {'OUI' if location_data else 'NON'}")
    
    media_metadata = []
    failed_uploads = []
    
    # ✅ CORRECTION: Traitement des médias avec gestion d'erreurs améliorée
    for i, media in enumerate(elements):
        try:
            print(f"📤 Traitement média {i+1}/{len(elements)}")
            
            # ✅ CORRECTION: Ne pas logger le nom du fichier qui peut contenir des caractères problématiques
            filename = media.get('filename', f'file_{i}')
            safe_filename = filename.encode('ascii', 'ignore').decode('ascii') if filename else f'file_{i}'
            print(f"📤 Fichier: {safe_filename}")
            
            # ✅ CORRECTION: Validation plus stricte des données
            if 'data' in media and media['data']:
                print("📥 Upload normal avec données binaires")
                
                file_data = media['data']
                file_name = media['filename']
                mimetype = media.get('mimetype', 'application/octet-stream')
                file_size = len(file_data) if isinstance(file_data, bytes) else 0
                
                # ✅ VALIDATION: Vérifier que c'est bien du binaire
                if not isinstance(file_data, bytes):
                    print(f"❌ Données non binaires pour {safe_filename}")
                    failed_uploads.append({
                        'filename': file_name,
                        'error': 'Données non binaires'
                    })
                    continue
                
                if file_size == 0:
                    print(f"❌ Fichier vide: {safe_filename}")
                    failed_uploads.append({
                        'filename': file_name,
                        'error': 'Fichier vide'
                    })
                    continue
                
                print(f"📊 Taille: {file_size} bytes, Type: {mimetype}")
                
                # ✅ CORRECTION: Vérification de la taille de fichier
                MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
                if file_size > MAX_FILE_SIZE:
                    print(f"❌ Fichier trop volumineux: {safe_filename} ({file_size} bytes)")
                    failed_uploads.append({
                        'filename': file_name,
                        'error': f'Fichier trop volumineux ({file_size} bytes > {MAX_FILE_SIZE} bytes)'
                    })
                    continue
                
                try:
                    metadata = media_service.upload_media(
                        file_data=file_data,
                        original_filename=file_name,
                        mimetype=mimetype,
                        citoyen_id=citoyen_id
                    )
                    
                    # ✅ CORRECTION: Validation du retour de l'upload
                    if metadata and 'url' in metadata:
                        media_metadata.append(metadata)
                        print(f"✅ Upload réussi: {safe_filename}")
                    else:
                        print(f"❌ Métadonnées invalides pour {safe_filename}")
                        failed_uploads.append({
                            'filename': file_name,
                            'error': 'Métadonnées invalides retournées par le service'
                        })
                        
                except Exception as upload_error:
                    print(f"❌ Erreur upload {safe_filename}: {upload_error}")
                    failed_uploads.append({
                        'filename': file_name,
                        'error': str(upload_error)
                    })
                    continue
                
            elif 'url' in media and 'storage_path' in media:
                # Republication avec métadonnées existantes
                print("🔄 Republication - médias déjà uploadés sur Supabase")
                
                # ✅ CORRECTION: Validation des métadonnées de republication
                required_fields = ['filename', 'storage_path', 'url']
                missing_fields = [field for field in required_fields if not media.get(field)]
                
                if missing_fields:
                    print(f"❌ Métadonnées republication incomplètes: {missing_fields}")
                    failed_uploads.append({
                        'filename': media.get('filename', 'unknown'),
                        'error': f'Champs manquants: {missing_fields}'
                    })
                    continue
                
                republication_metadata = {
                    'filename': media.get('filename'),
                    'storage_path': media.get('storage_path'),
                    'url': media.get('url'),
                    'display_url': media.get('display_url', media.get('url')),
                    'download_url': media.get('download_url', media.get('url')),
                    'thumbnail_url': media.get('thumbnail_url'),
                    'preview_url': media.get('preview_url'),
                    'mimetype': media.get('mimetype', 'application/octet-stream'),
                    'category': media.get('category', 'others'),
                    'size': media.get('size', 0),
                    'hash': media.get('hash'),
                    'uploaded_at': media.get('upload_date', datetime.utcnow().isoformat()),
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
                print(f"✅ Métadonnées republication conservées: {safe_filename}")
                
            elif 'url' in media:
                # URL simple (fallback)
                print("🔗 URL simple - création métadonnées basiques")
                
                # ✅ CORRECTION: Validation de l'URL
                url = media.get('url')
                if not url or not url.startswith(('http://', 'https://')):
                    print(f"❌ URL invalide: {url}")
                    failed_uploads.append({
                        'filename': media.get('filename', 'unknown'),
                        'error': 'URL invalide'
                    })
                    continue
                
                basic_metadata = {
                    'filename': media.get('filename', 'unknown'),
                    'url': url,
                    'display_url': media.get('display_url', url),
                    'download_url': media.get('download_url', url),
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
                print(f"✅ Métadonnées basiques créées: {safe_filename}")
                
            else:
                print(f"❌ Format de média non reconnu")
                print(f"❌ Clés disponibles: {list(media.keys())}")
                failed_uploads.append({
                    'filename': media.get('filename', 'unknown'),
                    'error': 'Format de données non reconnu'
                })
                continue
            
        except Exception as e:
            print(f"❌ Erreur traitement média {i}: {e}")
            failed_uploads.append({
                'filename': media.get('filename', f'unknown_{i}'),
                'error': str(e)
            })
            continue
    
    # ========== CRÉATION DU SIGNALEMENT ==========
    try:
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
            statut='en_attente',
            dateCreated=datetime.utcnow(),
            priorite=priorite
        )
        
        # ========== AJOUT DES DONNÉES DE LOCALISATION ==========
        if location_data:
            success = nouveau_signalement.set_location_data(location_data)
            if success:
                print(f"✅ Données GPS ajoutées au signalement")
                print(f"📍 Coordonnées: {location_data.get('latitude')}, {location_data.get('longitude')}")
            else:
                print(f"⚠️ Échec ajout données GPS")
        
        # Sauvegarder les métadonnées des médias réussis
        if media_metadata:
            nouveau_signalement.set_elements(media_metadata)
            print(f"💾 Métadonnées sauvegardées: {len(media_metadata)} médias")
        
        db.session.add(nouveau_signalement)
        db.session.commit()
        
        print(f"✅ Signalement créé: ID {nouveau_signalement.IDsignalement}")
        print(f"📊 Statut: {nouveau_signalement.statut}")
        print(f"📊 Médias sauvegardés: {len(media_metadata)}/{len(elements)}")
        print(f"📍 Localisation: {nouveau_signalement.has_location}")
        
        if failed_uploads:
            print(f"⚠️ Uploads échoués: {len(failed_uploads)}")
            for failed in failed_uploads:
                safe_name = failed['filename'].encode('ascii', 'ignore').decode('ascii')
                print(f"   - {safe_name}: {failed['error']}")
        
        successful_uploads = len(media_metadata)
        
        return {
            'signalement': nouveau_signalement,
            'uploaded_media': successful_uploads,
            'failed_uploads': failed_uploads
        }
        
    except Exception as db_error:
        print(f"❌ Erreur DB: {db_error}")
        
        # En cas d'erreur DB, nettoyer les médias uploadés (seulement pour les nouveaux uploads)
        cleanup_count = 0
        for metadata in media_metadata:
            if (metadata.get('upload_context') != 'republication' and 
                metadata.get('storage_path')):
                try:
                    media_service.delete_media(metadata['storage_path'])
                    cleanup_count += 1
                    print(f"🧹 Nettoyage: {metadata.get('filename', 'unknown')}")
                except Exception as cleanup_error:
                    print(f"⚠️ Erreur nettoyage: {cleanup_error}")
        
        if cleanup_count > 0:
            print(f"🧹 {cleanup_count} médias nettoyés suite à l'erreur DB")
        
        db.session.rollback()
        raise db_error

# ========== AJOUT SERVICES POUR LA GÉOLOCALISATION ==========

def get_signalements_by_location(latitude, longitude, radius_km=5):
    """Récupère les signalements dans un rayon donné (en km)"""
    try:
        from sqlalchemy import func
        
        # Formule haversine en SQL pour calculer la distance
        haversine = func.acos(
            func.cos(func.radians(latitude)) *
            func.cos(func.radians(Signalement.latitude)) *
            func.cos(func.radians(Signalement.longitude) - func.radians(longitude)) +
            func.sin(func.radians(latitude)) *
            func.sin(func.radians(Signalement.latitude))
        ) * 6371  # Rayon de la Terre en km
        
        return Signalement.query.filter(
            Signalement.has_location == True,
            Signalement.is_deleted == False,
            haversine <= radius_km
        ).all()
        
    except Exception as e:
        print(f"❌ Erreur recherche par localisation: {e}")
        return []

def get_signalements_with_location():
    """Récupère tous les signalements ayant une localisation"""
    return Signalement.query.filter(
        Signalement.has_location == True,
        Signalement.is_deleted == False
    ).all()

def get_location_statistics():
    """Statistiques sur l'utilisation de la géolocalisation"""
    total_signalements = Signalement.query.filter_by(is_deleted=False).count()
    with_location = Signalement.query.filter_by(has_location=True, is_deleted=False).count()
    
    return {
        'total_signalements': total_signalements,
        'with_location': with_location,
        'without_location': total_signalements - with_location,
        'location_usage_rate': round((with_location / total_signalements * 100), 2) if total_signalements > 0 else 0
    }    
    
# Remplacez votre fonction update_signalement par celle-ci :

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
    republierPar=None,
    location_data=None,  # ← AJOUT PARAMÈTRE LOCALISATION
    priorite=None
):
    """
    Met à jour un signalement avec Supabase Storage et géolocalisation
    """
    signalement = Signalement.query.get(signalement_id)
    if not signalement or signalement.is_deleted:
        return None

    print(f"🔄 Mise à jour signalement {signalement_id}")

    # ========== GESTION DE LA LOCALISATION ==========
    if location_data is not None:
        if location_data == 'REMOVE':
            # Supprimer la localisation
            print("🗑️ Suppression de la localisation")
            signalement.latitude = None
            signalement.longitude = None
            signalement.accuracy = None
            signalement.altitude = None
            signalement.heading = None
            signalement.speed = None
            signalement.location_timestamp = None
            signalement.location_address = None
            signalement.has_location = False
        elif isinstance(location_data, dict):
            # Mettre à jour la localisation
            print(f"📍 Mise à jour localisation: {location_data.get('latitude')}, {location_data.get('longitude')}")
            success = signalement.set_location_data(location_data)
            if not success:
                print("❌ Échec mise à jour localisation")

    # ========== GESTION DES MÉDIAS ==========
    if elements is not None:
        print(f"📎 Mise à jour des médias: {len(elements)} éléments")
        
        # Récupérer les anciens éléments pour supprimer les fichiers
        old_elements = signalement.get_elements()
        for old_element in old_elements:
            if 'storage_path' in old_element:
                try:
                    media_service.delete_media(old_element['storage_path'])
                    print(f"🗑️ Ancien média supprimé: {old_element.get('filename')}")
                except Exception as e:
                    print(f"⚠️ Erreur suppression ancien média: {e}")
        
        # Traiter les nouveaux éléments
        media_metadata = []
        failed_uploads = []
        
        for i, media in enumerate(elements):
            try:
                if 'data' in media:
                    # Nouveau fichier à uploader
                    file_data = media['data']
                    file_name = media['filename']
                    mimetype = media.get('mimetype', 'application/octet-stream')
                    
                    print(f"📤 Upload nouveau média {i+1}: {file_name}")
                    
                    # Upload vers Supabase
                    metadata = media_service.upload_media(
                        file_data=file_data,
                        original_filename=file_name,
                        mimetype=mimetype,
                        citoyen_id=signalement.citoyenID
                    )
                    
                    media_metadata.append(metadata)
                    print(f"✅ Upload réussi: {file_name}")
                    
                elif 'url' in media and 'storage_path' in media:
                    # Média existant (republication)
                    print(f"🔄 Conservation média existant: {media.get('filename')}")
                    
                    existing_metadata = {
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
                        'upload_context': 'update',
                        'provider': 'supabase',
                        'bucket': 'signalements',
                        'citoyen_id': signalement.citoyenID,
                        'is_image': media.get('is_image', False),
                        'is_video': media.get('is_video', False),
                        'is_document': media.get('is_document', False),
                        'is_audio': media.get('is_audio', False)
                    }
                    
                    media_metadata.append(existing_metadata)
                
            except Exception as e:
                print(f"❌ Erreur traitement média lors de la mise à jour: {e}")
                failed_uploads.append({
                    'filename': media.get('filename', 'unknown'),
                    'error': str(e)
                })
                continue
        
        # Sauvegarder les nouveaux métadonnées
        signalement.set_elements(media_metadata)
        print(f"💾 Médias mis à jour: {len(media_metadata)} éléments")
        
        if failed_uploads:
            print(f"⚠️ Échecs upload: {len(failed_uploads)}")

    # ========== MISE À JOUR DES AUTRES CHAMPS ==========
    updated_fields = []
    
    if typeSignalement is not None:
        signalement.typeSignalement = typeSignalement
        updated_fields.append('typeSignalement')
    if description is not None:
        signalement.description = description
        updated_fields.append('description')
    if statut is not None:
        old_status = signalement.statut
        signalement.statut = statut
        updated_fields.append('statut')
        print(f"📊 Statut: {old_status} → {statut}")
    if nb_vote_positif is not None:
        signalement.nbVotePositif = nb_vote_positif
        updated_fields.append('nbVotePositif')
    if nb_vote_negatif is not None:
        signalement.nbVoteNegatif = nb_vote_negatif
        updated_fields.append('nbVoteNegatif')
    if cible is not None:
        signalement.cible = cible
        updated_fields.append('cible')
    if id_moderateur is not None:
        signalement.IDmoderateur = id_moderateur
        updated_fields.append('IDmoderateur')
    if republierPar is not None:
        signalement.republierPar = republierPar
        updated_fields.append('republierPar')
    if priorite is not None:
        signalement.priorite = priorite
        updated_fields.append('priorite')

    try:
        db.session.commit()
        print(f"✅ Signalement {signalement_id} mis à jour")
        print(f"📊 Champs modifiés: {updated_fields}")
        return signalement
        
    except Exception as e:
        print(f"❌ Erreur DB lors de la mise à jour: {e}")
        db.session.rollback()
        raise e
    
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


# Ajoutez ces fonctions à la fin de votre fichier services.py

def get_signalements_by_status_with_location(statut):
    """Récupère les signalements par statut avec informations de localisation"""
    return Signalement.query.filter_by(
        statut=statut, 
        is_deleted=False, 
        has_location=True
    ).all()

def update_signalement_location(signalement_id, location_data):
    """Met à jour uniquement la localisation d'un signalement"""
    try:
        signalement = Signalement.query.get(signalement_id)
        if not signalement or signalement.is_deleted:
            return None
        
        success = signalement.set_location_data(location_data)
        if success:
            db.session.commit()
            print(f"✅ Localisation mise à jour pour signalement {signalement_id}")
            return signalement
        else:
            print(f"❌ Échec mise à jour localisation pour signalement {signalement_id}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur update_signalement_location: {e}")
        db.session.rollback()
        return None

def get_signalements_nearby_count(latitude, longitude, radius_km=1):
    """Compte les signalements dans un rayon donné (pour éviter les doublons)"""
    try:
        signalements = get_signalements_by_location(latitude, longitude, radius_km)
        return len(signalements)
    except:
        return 0

def get_hotspots_analysis(min_signalements=3, radius_km=1):
    """Analyse des zones à forte concentration de signalements"""
    try:
        # Récupérer tous les signalements avec localisation
        signalements = get_signalements_with_location()
        
        hotspots = []
        processed_signalements = set()
        
        for signalement in signalements:
            if signalement.IDsignalement in processed_signalements:
                continue
                
            location_data = signalement.get_location_data()
            if not location_data:
                continue
                
            lat = location_data['latitude']
            lng = location_data['longitude']
            
            # Compter les signalements dans la zone
            nearby = get_signalements_by_location(lat, lng, radius_km)
            
            if len(nearby) >= min_signalements:
                # Marquer ces signalements comme traités
                for nearby_sig in nearby:
                    processed_signalements.add(nearby_sig.IDsignalement)
                
                # Calculer le centre de gravité
                total_lat = sum(s.get_location_data()['latitude'] for s in nearby if s.get_location_data())
                total_lng = sum(s.get_location_data()['longitude'] for s in nearby if s.get_location_data())
                center_lat = total_lat / len(nearby)
                center_lng = total_lng / len(nearby)
                
                # Analyser les types de signalements
                types_count = {}
                status_count = {}
                for sig in nearby:
                    types_count[sig.typeSignalement] = types_count.get(sig.typeSignalement, 0) + 1
                    status_count[sig.statut] = status_count.get(sig.statut, 0) + 1
                
                hotspots.append({
                    'center': {'latitude': center_lat, 'longitude': center_lng},
                    'radius_km': radius_km,
                    'signalements_count': len(nearby),
                    'types_distribution': types_count,
                    'status_distribution': status_count,
                    'signalement_ids': [s.IDsignalement for s in nearby],
                    'most_common_type': max(types_count.items(), key=lambda x: x[1])[0],
                    'google_maps_url': f"https://www.google.com/maps?q={center_lat},{center_lng}"
                })
        
        # Trier par nombre de signalements
        hotspots.sort(key=lambda x: x['signalements_count'], reverse=True)
        
        return hotspots
        
    except Exception as e:
        print(f"❌ Erreur hotspots_analysis: {e}")
        return []

# Statistiques avancées
def get_advanced_signalement_stats():
    """Statistiques avancées incluant la géolocalisation"""
    basic_stats = get_signalement_stats()
    location_stats = get_location_statistics()
    
    # Statistiques par type avec localisation
    types_with_location = {}
    all_signalements = get_all_signalements()
    
    for signalement in all_signalements:
        type_sig = signalement.typeSignalement
        if type_sig not in types_with_location:
            types_with_location[type_sig] = {'total': 0, 'with_location': 0}
        
        types_with_location[type_sig]['total'] += 1
        if signalement.has_location:
            types_with_location[type_sig]['with_location'] += 1
    
    # Calculer les pourcentages
    for type_sig in types_with_location:
        data = types_with_location[type_sig]
        data['location_rate'] = round(
            (data['with_location'] / data['total'] * 100), 2
        ) if data['total'] > 0 else 0
    
    return {
        **basic_stats,
        'location': location_stats,
        'types_location_breakdown': types_with_location,
        'hotspots_count': len(get_hotspots_analysis()),
        'generated_at': datetime.utcnow().isoformat()
    }

def export_signalements_geojson(include_private=False):
    """Exporte les signalements au format GeoJSON pour cartographie"""
    try:
        query = Signalement.query.filter(
            Signalement.has_location == True,
            Signalement.is_deleted == False
        )
        
        if not include_private:
            query = query.filter(Signalement.cible == 'public')
        
        signalements = query.all()
        
        features = []
        for s in signalements:
            if s.is_location_valid():
                location_data = s.get_location_data()
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            location_data['longitude'], 
                            location_data['latitude']
                        ]
                    },
                    "properties": {
                        "id": s.IDsignalement,
                        "type": s.typeSignalement,
                        "statut": s.statut,
                        "description": s.description,
                        "date": s.dateCreated.isoformat() if s.dateCreated else None,
                        "anonymat": s.anonymat,
                        "accuracy": location_data.get('accuracy'),
                        "has_media": s.has_media(),
                        "media_count": s.get_media_count(),
                        "votes_positifs": s.nbVotePositif,
                        "votes_negatifs": s.nbVoteNegatif
                    }
                }
                features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_features": len(features),
                "generated_at": datetime.utcnow().isoformat(),
                "include_private": include_private
            }
        }
        
        return geojson
        
    except Exception as e:
        print(f"❌ Erreur export GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}
  