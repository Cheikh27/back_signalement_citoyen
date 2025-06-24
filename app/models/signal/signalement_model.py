from datetime import datetime
import json
from flask import current_app
from app import db

class Signalement(db.Model):
    __tablename__ = 'signalements'
    
    IDsignalement = db.Column(db.Integer, primary_key=True)
    typeSignalement = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    
    # Stockage des métadonnées Supabase au format JSON
    elements = db.Column(db.Text, nullable=True)
    
    statut = db.Column(db.String(20), nullable=False, default='en_cours')
    nbVotePositif = db.Column(db.Integer, nullable=True, default=0)
    nbVoteNegatif = db.Column(db.Integer, nullable=True, default=0)
    cible = db.Column(db.String(50), nullable=False)
    IDmoderateur = db.Column(db.Integer, nullable=True)
    anonymat = db.Column(db.Boolean, default=False)
    republierPar = db.Column(db.Integer, nullable=True)
    dateCreated = db.Column(db.DateTime, default=db.func.now())
    dateDeleted = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    citoyenID = db.Column(db.Integer, db.ForeignKey('citoyens.IDcitoyen'), nullable=False)

    def __repr__(self):
        return f"<Signalement ID={self.IDsignalement}, Type={self.typeSignalement}>"

    def set_elements(self, media_list):
        """Enregistre les métadonnées des médias Supabase en JSON"""
        self.elements = json.dumps(media_list)

    def get_elements(self):
        """Récupère la liste des métadonnées depuis le JSON"""
        return json.loads(self.elements or "[]")
    
   
    def _get_file_icon(self, mimetype: str) -> str:
        """Retourne l'icône appropriée selon le type de fichier"""
        if mimetype.startswith('image/'):
            return '🖼️'
        elif mimetype.startswith('video/'):
            return '🎥'
        elif mimetype.startswith('audio/'):
            return '🎵'
        elif mimetype == 'application/pdf':
            return '📄'
        elif 'word' in mimetype or 'document' in mimetype:
            return '📝'
        elif 'sheet' in mimetype or 'excel' in mimetype:
            return '📊'
        else:
            return '📎'
    
    def _get_media_service(self):
        """Récupère le service média depuis l'app context de manière sécurisée"""
        try:
            if current_app:
                media_service = current_app.config.get('MEDIA_SERVICE')
                if media_service:
                    return media_service
            
            try:
                import app.supabase_media_service as sms
                return sms.get_media_service()
            except ImportError:
                pass
            
            try:
                import os
                from supabase import create_client
                
                url = os.getenv('SUPABASE_URL')
                key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                if url and key:
                    client = create_client(url, key)
                    
                    class MinimalService:
                        def __init__(self, client):
                            self.supabase = client
                            self.bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'signalements')
                    
                    return MinimalService(client)
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur récupération service média: {e}")
            return None
    
    def get_fresh_download_urls(self):
        """Génère des URLs fraîches et optimisées"""
        try:
            media_service = self._get_media_service()
            if not media_service:
                print("⚠️ Service média non disponible")
                return self.get_elements_optimized()
            
            elements = self.get_elements()
            fresh_elements = []
            
            for element in elements:
                if 'storage_path' in element:
                    try:
                        # Régénérer l'URL publique
                        fresh_url = media_service.supabase.storage.from_(media_service.bucket_name).get_public_url(element['storage_path'])
                        
                        # Copier les métadonnées existantes
                        fresh_element = element.copy()
                        fresh_element['url'] = fresh_url
                        fresh_element['display_url'] = fresh_url
                        fresh_element['download_url'] = f"{fresh_url}?download=true"
                        
                        # URLs optimisées pour les images
                        if element.get('category') == 'images' or element.get('is_image'):
                            fresh_element['thumbnail_url'] = f"{fresh_url}?width=150&height=150&resize=cover"
                            fresh_element['preview_url'] = f"{fresh_url}?width=500&height=500&resize=contain"
                            fresh_element['full_url'] = fresh_url
                        
                        fresh_element['refreshed_at'] = json.dumps(datetime.utcnow().isoformat())
                        fresh_elements.append(fresh_element)
                        
                    except Exception as e:
                        print(f"❌ Erreur régénération URL pour {element.get('filename', 'unknown')}: {e}")
                        fresh_elements.append(element)
                else:
                    fresh_elements.append(element)
            
            return fresh_elements
            
        except Exception as e:
            print(f"❌ Erreur get_fresh_download_urls: {e}")
            return self.get_elements_optimized()
    
    def get_media_count(self):
        """Retourne le nombre de médias associés"""
        try:
            return len(self.get_elements())
        except:
            return 0
    
    # Dans votre modèle Signalement, modifiez get_elements_optimized()

    def get_elements_optimized(self):
        """Récupère les éléments avec URLs optimisées ET catégorisation automatique"""
        try:
            elements = self.get_elements()
            optimized_elements = []
            
            for element in elements:
                # Copier les données existantes
                optimized = element.copy()
                
                # 🔧 CORRECTION AUTOMATIQUE DE LA CATÉGORISATION
                mimetype = optimized.get('mimetype', '')
                current_category = optimized.get('category', 'others')
                
                # Déterminer la bonne catégorie basée sur le mimetype
                correct_category = self._determine_category_from_mimetype(mimetype)
                
                # Corriger automatiquement si nécessaire
                if current_category != correct_category:
                    optimized['category'] = correct_category
                    print(f"🔄 Auto-correction: {element.get('filename')} → {correct_category}")
                
                # Ajouter les flags booléens
                optimized['is_image'] = (correct_category == 'images')
                optimized['is_video'] = (correct_category == 'videos')
                optimized['is_audio'] = (correct_category == 'audios')
                optimized['is_document'] = (correct_category == 'documents')
                
                # Ajouter des URLs optimisées pour l'affichage
                base_url = element.get('url', '')
                if base_url:
                    optimized['display_url'] = base_url
                    optimized['download_url'] = f"{base_url}?download=true"
                    
                    # URLs pour les images avec redimensionnement
                    if correct_category == 'images':
                        optimized['thumbnail_url'] = f"{base_url}?width=150&height=150&resize=cover"
                        optimized['preview_url'] = f"{base_url}?width=500&height=500&resize=contain"
                        optimized['full_url'] = base_url
                    
                    # Informations d'affichage
                    optimized['can_preview'] = correct_category in ['images', 'videos']
                    optimized['icon'] = self._get_file_icon(mimetype)
                
                optimized_elements.append(optimized)
            
            return optimized_elements
            
        except Exception as e:
            print(f"❌ Erreur get_elements_optimized: {e}")
            return self.get_elements()

    def _determine_category_from_mimetype(self, mimetype: str) -> str:
        """Détermine la catégorie correcte basée sur le mimetype"""
        if not mimetype:
            return 'others'
        
        mimetype = mimetype.lower()
        
        if mimetype.startswith('image/'):
            return 'images'
        elif mimetype.startswith('video/'):
            return 'videos'
        elif mimetype.startswith('audio/'):
            return 'audios'
        elif mimetype in [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'text/csv'
        ]:
            return 'documents'
        else:
            return 'others'

    def get_media_summary(self):
        """Retourne un résumé des médias avec catégorisation corrigée"""
        try:
            # Utiliser les éléments optimisés qui corrigent automatiquement les catégories
            elements = self.get_elements_optimized()
            
            summary = {
                'total': len(elements),
                'images': 0,
                'videos': 0,
                'documents': 0,
                'audios': 0,
                'others': 0
            }
            
            for element in elements:
                category = element.get('category', 'others')
                if category in summary:
                    summary[category] += 1
                else:
                    summary['others'] += 1
            
            return summary
        except:
            return {'total': 0, 'images': 0, 'videos': 0, 'documents': 0, 'audios': 0, 'others': 0}

    def get_media_by_category(self, category: str):
        """Filtre les médias par catégorie avec correction automatique"""
        try:
            # Utiliser get_elements_optimized qui corrige automatiquement
            elements = self.get_elements_optimized()
            return [e for e in elements if e.get('category') == category]
        except:
            return []
    
    def get_images(self):
        """Retourne uniquement les images avec URLs optimisées"""
        return self.get_media_by_category('images')
    
    
    def get_videos(self):
        """Retourne uniquement les vidéos"""
        return self.get_media_by_category('videos')
    
    def get_documents(self):
        """Retourne les documents"""
        return self.get_media_by_category('documents')
    
    

    def has_media(self):
        """Vérifie si le signalement a des médias"""
        return self.get_media_count() > 0
    
    def cleanup_media(self):
        """Supprime tous les médias associés de Supabase"""
        try:
            media_service = self._get_media_service()
            if not media_service:
                print("⚠️ Service média non disponible pour le nettoyage")
                self.set_elements([])
                db.session.commit()
                return
            
            elements = self.get_elements()
            
            for element in elements:
                if 'storage_path' in element:
                    try:
                        response = media_service.supabase.storage.from_(media_service.bucket_name).remove([element['storage_path']])
                        if hasattr(response, 'error') and response.error:
                            print(f"❌ Erreur suppression {element['storage_path']}: {response.error}")
                        else:
                            print(f"✅ Supprimé: {element['storage_path']}")
                    except Exception as e:
                        print(f"❌ Erreur suppression {element.get('filename', 'unknown')}: {e}")
            
            self.set_elements([])
            db.session.commit()
            
        except Exception as e:
            print(f"❌ Erreur cleanup_media: {e}")
            try:
                self.set_elements([])
                db.session.commit()
            except:
                pass