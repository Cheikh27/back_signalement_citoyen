import os
import re
import unicodedata
import uuid
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import mimetypes
from typing import Optional, Dict, List

load_dotenv()

# Import conditionnel de Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("⚠️ Supabase non installé - pip install supabase")
    SUPABASE_AVAILABLE = False
    Client = None

class SupabaseMediaService:
    """Service principal pour la gestion des médias avec Supabase"""
    
    def __init__(self, use_service_role: bool = True):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase non disponible - installez avec: pip install supabase")
        
        url = os.getenv('SUPABASE_URL')
        if not url:
            raise ValueError("SUPABASE_URL non définie dans l'environnement")
        
        if use_service_role:
            key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            if not key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY non définie dans l'environnement")
            print("🔐 Utilisation de la clé SERVICE_ROLE pour les uploads serveur")
        else:
            key = os.getenv('SUPABASE_ANON_KEY')
            if not key:
                raise ValueError("SUPABASE_ANON_KEY non définie dans l'environnement")
            print("🔓 Utilisation de la clé ANON pour les opérations frontend")
            
        self.supabase: Client = create_client(url, key) # type: ignore
        self.bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'signalements')
        self.use_service_role = use_service_role
        
        # Limites de sécurité
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))
        self.allowed_mimetypes = {
            'image/': ['jpeg', 'jpg', 'png', 'gif', 'webp', 'bmp'],
            'video/': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'],
            'audio/': ['mp3', 'wav', 'ogg', 'aac', 'm4a'],
            'application/pdf': ['pdf'],
            'application/msword': ['doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
            'text/': ['txt', 'csv', 'json']
        }
        
        # Classification des types de fichiers
        self.file_categories = {
            'images': ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'],
            'videos': ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv', 'video/webm'],
            'audios': ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/m4a'],
            'documents': [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/plain',
                'text/csv'
            ]
        }
    
    def get_file_category(self, mimetype: str) -> str:
        """Détermine la catégorie d'un fichier selon son type MIME"""
        for category, types in self.file_categories.items():
            if mimetype.lower() in types or any(mimetype.lower().startswith(t.split('/')[0] + '/') for t in types):
                return category
        return 'others'  # Catégorie par défaut
    
    def create_bucket_if_not_exists(self):
        """Créer le bucket s'il n'existe pas"""
        try:
            # Vérifier si le bucket existe
            buckets = self.supabase.storage.list_buckets()
            bucket_exists = any(b.name == self.bucket_name for b in buckets)
            
            if not bucket_exists:
                # Créer le bucket public
                try:
                    result = self.supabase.storage.create_bucket(
                        self.bucket_name,
                        {"public": True}
                    )
                    print(f"✅ Bucket '{self.bucket_name}' créé")
                except Exception as create_error:
                    # Vérifier si le bucket existe maintenant
                    buckets_after = self.supabase.storage.list_buckets()
                    bucket_exists_after = any(b.name == self.bucket_name for b in buckets_after)
                    
                    if bucket_exists_after:
                        print(f"ℹ️ Bucket '{self.bucket_name}' existe déjà")
                    else:
                        print(f"❌ Erreur création bucket: {create_error}")
            else:
                print(f"ℹ️ Bucket '{self.bucket_name}' existe déjà")
                
        except Exception as e:
            print(f"❌ Erreur vérification bucket: {e}")
    
    def generate_unique_path(self, original_filename: str, citoyen_id: int, mimetype: str) -> str:
        """Génère un chemin unique organisé par type de fichier avec nettoyage amélioré"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Déterminer la catégorie du fichier
        category = self.get_file_category(mimetype)
        
        # 🔧 NETTOYAGE AMÉLIORÉ du nom de fichier
        safe_name = self._clean_filename_advanced(original_filename)
        
        # Structure organisée: users/{citoyen_id}/{category}/{timestamp}_{uuid}_{filename}
        if '.' in safe_name:
            name_part, extension = safe_name.rsplit('.', 1)
            # Limiter la longueur du nom pour éviter les URLs trop longues
            safe_filename = f"{timestamp}_{unique_id}_{name_part[:30]}.{extension}"
        else:
            safe_filename = f"{timestamp}_{unique_id}_{safe_name[:30]}"
        
        return f"users/{citoyen_id}/{category}/{safe_filename}"

    def _clean_filename_advanced(self, filename: str) -> str:
        """Nettoyage avancé du nom de fichier pour Supabase"""
        # 1. Normaliser les caractères Unicode (ç -> c, à -> a, etc.)
        filename = unicodedata.normalize('NFD', filename)
        filename = ''.join(c for c in filename if unicodedata.category(c) != 'Mn')
        
        # 2. Remplacer les caractères spéciaux par des underscores
        # Garde seulement : lettres, chiffres, points, tirets, underscores
        filename = re.sub(r'[^a-zA-Z0-9.\-_]', '_', filename)
        
        # 3. Supprimer les underscores multiples
        filename = re.sub(r'_+', '_', filename)
        
        # 4. Supprimer les underscores en début/fin
        filename = filename.strip('_')
        
        # 5. Limiter la longueur totale
        if len(filename) > 100:
            name_part, extension = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = f"{name_part[:90]}.{extension}" if extension else name_part[:100]
        
        # 6. Fallback si le nom devient vide
        if not filename or filename == '.':
            filename = "file"
        
        print(f"🧹 Nom nettoyé: '{filename}'")
        return filename
    
    def _clean_filename_strict(self, filename: str) -> str:
        """Nettoyage ultra-strict pour éviter tous problèmes"""
        # Garder seulement lettres, chiffres et extension
        # Remplacer tout le reste par underscore
        clean = re.sub(r'[^a-zA-Z0-9.]', '_', filename)
        
        # Supprimer underscores multiples
        clean = re.sub(r'_+', '_', clean)
        clean = clean.strip('_')
        
        # Limiter à 50 caractères max
        if len(clean) > 50:
            if '.' in clean:
                name, ext = clean.rsplit('.', 1)
                clean = f"{name[:45]}.{ext}"
            else:
                clean = clean[:50]
        
        return clean or "file"

    def _clean_filename_simple(self, filename: str) -> str:
        """Version ultra-simple qui garde seulement les caractères sûrs"""
        # Garder seulement lettres, chiffres, points, tirets et underscores
        safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Nettoyer les underscores multiples
        safe_chars = re.sub(r'_+', '_', safe_chars)
        
        # Nettoyer début et fin
        safe_chars = safe_chars.strip('_.-')
        
        # Fallback
        if not safe_chars:
            safe_chars = f"file_{str(uuid.uuid4())[:8]}"
        
        return safe_chars
    
    def test_filename_cleaning(self):
        """Test des noms de fichiers problématiques"""
        test_files = [
            "Essayez De Ne Pas RIRE en Regardant Ça... (999,99% IMPOSSIBLE!).mp4",
            "word_table_des_matières_16122014 (1).pdf",
            "How to Plug a Tire.mp4",
            "fichier avec des espaces.jpg",
            "café-à-paris.png"
        ]
        
        print("🧪 TEST NETTOYAGE NOMS DE FICHIERS:")
        for original in test_files:
            cleaned = self._clean_filename_advanced(original)
            print(f"   '{original}' → '{cleaned}'")
        
        return True

    def upload_media(self, file_data: bytes, original_filename: str, mimetype: str, citoyen_id: int, upload_context: str = 'standard') -> Dict[str, any]:
        """Upload un média avec classification automatique et contexte"""
        if not self.use_service_role:
            raise ValueError("Les uploads nécessitent la clé SERVICE_ROLE")
        
        try:
            print(f"📤 Upload Supabase: {original_filename} (contexte: {upload_context})")
            
            # Validation
            if len(file_data) > self.max_file_size:
                raise ValueError(f"Fichier trop volumineux: {len(file_data)} bytes")
            
            if len(file_data) == 0:
                raise ValueError("Fichier vide")
            
            # S'assurer que le bucket existe
            self.create_bucket_if_not_exists()
            
            # Détecter le mimetype si nécessaire
            if not mimetype or mimetype == 'application/octet-stream':
                detected_type, _ = mimetypes.guess_type(original_filename)
                if detected_type:
                    mimetype = detected_type
            
            # Générer le chemin selon le contexte
            if upload_context in ['republication', 'republication_base64']:
                storage_path = self._generate_republication_path(original_filename, citoyen_id, mimetype)
            else:
                storage_path = self.generate_unique_path(original_filename, citoyen_id, mimetype)
            
            category = self.get_file_category(mimetype)
            
            print(f"📁 Catégorie: {category}, Chemin: {storage_path}")
            
            # Options de fichier simplifiées
            file_options = {
                "content-type": mimetype,
                "upsert": False,
                "cache-control": "3600"
            }
            
            # Upload vers Supabase
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_data,
                file_options=file_options
            )
            
            # Vérifier le succès
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Erreur upload: {response.error}")
            
            print(f"✅ Upload Supabase réussi pour {original_filename}")
            
            # Générer URL publique
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
            
            # URLs optimisées
            urls = self._generate_optimized_urls(storage_path, mimetype, public_url)
            
            # Métadonnées enrichies
            metadata = {
                'filename': original_filename,
                'storage_path': storage_path,
                'url': public_url,
                'display_url': urls.get('display', public_url),
                'download_url': urls.get('download', f"{public_url}?download=true"),
                'preview_url': urls.get('preview'),
                'thumbnail_url': urls.get('thumbnail'),
                'mimetype': mimetype,
                'category': category,
                'size': len(file_data),
                'hash': hashlib.md5(file_data).hexdigest(),
                'uploaded_at': datetime.utcnow().isoformat(),
                'upload_context': upload_context,
                'provider': 'supabase',
                'bucket': self.bucket_name,
                'citoyen_id': citoyen_id,
                'file_extension': original_filename.split('.')[-1] if '.' in original_filename else '',
                'is_image': category == 'images',
                'is_video': category == 'videos',
                'is_document': category == 'documents',
                'is_audio': category == 'audios'
            }
            
            return metadata
            
        except Exception as e:
            print(f"❌ Erreur upload détaillée: {e}")
            import traceback
            print(f"❌ Stack trace: {traceback.format_exc()}")
            raise

    def _generate_republication_path(self, original_filename: str, citoyen_id: int, mimetype: str) -> str:
        """Génère un chemin spécial pour les republications"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        category = self.get_file_category(mimetype)
        safe_name = self._clean_filename_advanced(original_filename)
        
        if '.' in safe_name:
            name_part, extension = safe_name.rsplit('.', 1)
            safe_filename = f"republish_{timestamp}_{unique_id}_{name_part[:20]}.{extension}"
        else:
            safe_filename = f"republish_{timestamp}_{unique_id}_{safe_name[:20]}"
        
        return f"republications/{citoyen_id}/{category}/{safe_filename}"

    def _generate_optimized_urls(self, storage_path: str, mimetype: str, base_url: str) -> Dict[str, str]:
        """Génère des URLs optimisées selon le type de fichier"""
        urls = {
            'display': base_url,
            'download': f"{base_url}?download=true",
            'preview': None,
            'thumbnail': None
        }
        
        if mimetype.startswith('image/'):
            urls['thumbnail'] = f"{base_url}?width=150&height=150&resize=cover&quality=80"
            urls['display'] = f"{base_url}?width=800&quality=85"
            urls['preview'] = f"{base_url}?width=400&quality=75"
        
        return urls

    def delete_media(self, storage_path: str) -> bool:
        """Supprime un média"""
        if not self.use_service_role:
            print("❌ La suppression nécessite la clé SERVICE_ROLE")
            return False
        
        try:
            response = self.supabase.storage.from_(self.bucket_name).remove([storage_path])
            if hasattr(response, 'error') and response.error:
                print(f"❌ Erreur suppression: {response.error}")
                return False
            return True
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
            return False

    def get_media_info(self, storage_path: str) -> Dict[str, any]:
        """Récupère les informations d'un média avec URLs optimisées"""
        try:
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(storage_path)
            
            # Détecter la catégorie depuis le chemin
            path_parts = storage_path.split('/')
            category = 'others'
            if len(path_parts) >= 3:
                category = path_parts[2]  # users/{id}/{category}/file
            
            return {
                'exists': True,
                'public_url': public_url,
                'storage_path': storage_path,
                'download_url': f"{public_url}?download=true",
                'preview_url': public_url if category == 'images' else None,
                'thumbnail_url': f"{public_url}?width=300&height=300" if category == 'images' else None,
                'category': category
            }
        except Exception as e:
            return {
                'exists': False, 
                'error': str(e),
                'storage_path': storage_path
            }

    def list_user_files_by_category(self, citoyen_id: int, category: str = None) -> List[Dict]:
        """Liste les fichiers d'un utilisateur par catégorie"""
        try:
            if category:
                folder_path = f"users/{citoyen_id}/{category}"
            else:
                folder_path = f"users/{citoyen_id}"
                
            files = self.supabase.storage.from_(self.bucket_name).list(
                path=folder_path,
                limit=100
            )
            
            enriched_files = []
            for file in files:
                file_path = f"{folder_path}/{file['name']}"
                public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
                
                enriched_files.append({
                    'name': file['name'],
                    'path': file_path,
                    'category': category or 'unknown',
                    'size': file.get('metadata', {}).get('size', 0),
                    'created_at': file.get('created_at'),
                    'url': public_url,
                    'preview_url': public_url if category == 'images' else None
                })
            
            return enriched_files
            
        except Exception as e:
            print(f"❌ Erreur listing fichiers: {e}")
            return []


class SupabaseServiceFactory:
    """Factory pour créer les instances appropriées"""
    
    @staticmethod
    def create_server_service():
        """Service pour operations serveur"""
        return SupabaseMediaService(use_service_role=True)
    
    @staticmethod  
    def create_client_service():
        """Service pour operations frontend"""
        return SupabaseMediaService(use_service_role=False)

def get_media_service():
    """Retourne le service approprié selon le contexte"""
    if not SUPABASE_AVAILABLE:
        raise ImportError("Supabase non disponible")
    return SupabaseServiceFactory.create_server_service()

# Test d'intégrité
if __name__ == "__main__":
    print("🧪 Test du module supabase_media_service")
    if SUPABASE_AVAILABLE:
        print("✅ Supabase disponible")
        try:
            service = get_media_service()
            print(f"✅ Service créé: {service.bucket_name}")
            
            # Test de classification
            test_files = [
                ('image.jpg', 'image/jpeg'),
                ('video.mp4', 'video/mp4'),
                ('document.pdf', 'application/pdf')
            ]
            
            for filename, mimetype in test_files:
                category = service.get_file_category(mimetype)
                path = service.generate_unique_path(filename, 1, mimetype)
                print(f"📁 {filename} ({mimetype}) -> {category} -> {path}")
                
        except Exception as e:
            print(f"❌ Erreur création service: {e}")
    else:
        print("❌ Supabase non disponible")