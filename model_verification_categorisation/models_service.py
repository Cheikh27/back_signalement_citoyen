from flask import Flask, request, jsonify
from transformers import BertTokenizer, BertModel
import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
import os
import base64
import io
import logging
import tempfile
from werkzeug.utils import secure_filename
import mimetypes

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# ========== CONFIGURATION DES MODÈLES ==========
def load_models():
    """Charge les modèles avec gestion d'erreur"""
    try:
        # Modèle de texte
        print("📚 Chargement du modèle BERT...")
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        text_model = BertModel.from_pretrained('bert-base-uncased')
        text_model.eval()
        
        # Modèle d'image
        print("🖼️ Chargement du modèle ResNet50...")
        image_model = models.resnet50(pretrained=True)
        # Supprimer la dernière couche pour obtenir les features
        image_model = torch.nn.Sequential(*list(image_model.children())[:-1])
        image_model.eval()
        
        print("✅ Modèles chargés avec succès")
        return tokenizer, text_model, image_model
        
    except Exception as e:
        logger.error(f"❌ Erreur chargement modèles: {e}")
        raise

# Charger les modèles
tokenizer, text_model, image_model = load_models()

# Transformation pour les images
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# ========== CATÉGORIES AMÉLIORÉES ==========
CATEGORIES = {
    "Voirie & Transports": {
        "keywords": ["route", "trou", "nid", "poule", "asphalte", "circulation", "feu", "signalisation", "transport", "bus", "taxi", "embouteillage", "accident"],
        "weight": 1.2
    },
    "Propreté": {
        "keywords": ["déchet", "ordure", "poubelle", "sale", "nettoyer", "balayer", "détritus", "caniveau", "égout", "smell", "odeur"],
        "weight": 1.1
    },
    "Espaces Verts": {
        "keywords": ["arbre", "parc", "jardin", "fleur", "herbe", "entretien", "élagage", "plantation", "vert", "nature"],
        "weight": 1.0
    },
    "Sécurité": {
        "keywords": ["danger", "sécurité", "vol", "agression", "éclairage", "lampadaire", "police", "criminalité", "violence"],
        "weight": 1.3
    },
    "Environnement": {
        "keywords": ["pollution", "bruit", "eau", "air", "environnement", "écologie", "nuisance", "fumée", "chimique"],
        "weight": 1.1
    },
    "Événements": {
        "keywords": ["événement", "manifestation", "fête", "concert", "rassemblement", "célébration", "festival"],
        "weight": 0.9
    },
    "Services Publics": {
        "keywords": ["administration", "mairie", "service", "public", "bureau", "document", "carte", "identité"],
        "weight": 1.0
    },
    "Animalier": {
        "keywords": ["animal", "chien", "chat", "errant", "abandon", "maltraitance", "vétérinaire", "refuge"],
        "weight": 1.0
    },
    "Urbanisme": {
        "keywords": ["construction", "bâtiment", "permis", "urbanisme", "architecture", "rénovation", "démolition"],
        "weight": 1.0
    },
    "Social & Solidarité": {
        "keywords": ["aide", "social", "solidarité", "pauvreté", "mendicité", "association", "humanitaire"],
        "weight": 1.0
    },
    "Autres": {
        "keywords": [],
        "weight": 0.5
    }
}

# ========== UTILITAIRES ==========
def save_temp_file(file_data, filename):
    """Sauvegarde temporaire sécurisée d'un fichier"""
    try:
        # Créer un fichier temporaire
        suffix = os.path.splitext(filename)[1] if filename else '.tmp'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(file_data)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        logger.error(f"Erreur sauvegarde temporaire: {e}")
        return None

def cleanup_temp_file(filepath):
    """Supprime un fichier temporaire"""
    try:
        if filepath and os.path.exists(filepath):
            os.unlink(filepath)
    except:
        pass

def decode_base64_file(base64_data):
    """Décode un fichier base64"""
    try:
        if ',' in base64_data:
            header, data = base64_data.split(',', 1)
        else:
            data = base64_data
        
        file_data = base64.b64decode(data)
        return file_data
    except Exception as e:
        logger.error(f"Erreur décodage base64: {e}")
        return None

# ========== ENDPOINTS AMÉLIORÉS ==========

@app.route('/process_text', methods=['POST'])
def process_text():
    """Traitement de texte amélioré avec gestion d'erreur"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Texte requis'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Texte vide'}), 400
        
        # Limitation de longueur
        if len(text) > 5000:
            text = text[:5000]
            logger.warning("Texte tronqué à 5000 caractères")
        
        # Tokenisation
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        with torch.no_grad():
            outputs = text_model(**inputs)
        
        # Extraction des features (moyenne des embeddings)
        features = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
        
        # Normalisation
        features = features / np.linalg.norm(features)
        
        logger.info(f"✅ Texte traité: {len(text)} caractères -> {len(features)} features")
        return jsonify({
            'features': features.tolist(),
            'text_length': len(text),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur process_text: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process_image', methods=['POST'])
def process_image():
    """Traitement d'image amélioré avec plusieurs sources possibles"""
    temp_file = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        img = None
        
        # ========== MÉTHODE 1: Chemin de fichier ==========
        if 'path' in data and data['path']:
            image_path = data['path']
            if os.path.exists(image_path):
                img = Image.open(image_path)
                logger.info(f"📁 Image chargée depuis: {image_path}")
            else:
                logger.warning(f"⚠️ Fichier introuvable: {image_path}")
        
        # ========== MÉTHODE 2: Données base64 ==========
        elif 'base64' in data and data['base64']:
            try:
                file_data = decode_base64_file(data['base64'])
                if file_data:
                    img = Image.open(io.BytesIO(file_data))
                    logger.info("📊 Image chargée depuis base64")
            except Exception as b64_error:
                logger.error(f"Erreur base64: {b64_error}")
        
        # ========== MÉTHODE 3: URL ou nom de fichier ==========
        elif 'filename' in data and data['filename']:
            # Essayer de trouver le fichier dans différents dossiers
            filename = data['filename']
            possible_paths = [
                filename,
                os.path.join('uploads', filename),
                os.path.join('temp', filename),
                os.path.join('media', filename)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    logger.info(f"📁 Image trouvée: {path}")
                    break
        
        if img is None:
            return jsonify({'error': 'Image non trouvée ou format invalide'}), 404
        
        # ========== TRAITEMENT DE L'IMAGE ==========
        
        # Convertir en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Préprocessing
        img_tensor = preprocess(img)
        batch_tensor = torch.unsqueeze(img_tensor, 0)
        
        # Extraction des features
        with torch.no_grad():
            features = image_model(batch_tensor)
        
        # Aplatir et normaliser
        features = features.squeeze().numpy()
        features = features / np.linalg.norm(features)
        
        logger.info(f"✅ Image traitée: {img.size} -> {len(features)} features")
        
        return jsonify({
            'features': features.tolist(),
            'image_size': img.size,
            'image_mode': img.mode,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur process_image: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if temp_file:
            cleanup_temp_file(temp_file)

@app.route('/process_video', methods=['POST'])
def process_video():
    """Traitement vidéo amélioré avec sampling intelligent"""
    temp_file = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        video_path = None
        
        # ========== GESTION DES SOURCES VIDÉO ==========
        if 'path' in data and data['path']:
            if os.path.exists(data['path']):
                video_path = data['path']
            else:
                return jsonify({'error': f'Fichier vidéo non trouvé: {data["path"]}'}), 404
        
        elif 'base64' in data and data['base64']:
            try:
                file_data = decode_base64_file(data['base64'])
                if file_data:
                    temp_file = save_temp_file(file_data, 'video.mp4')
                    video_path = temp_file
            except Exception as e:
                return jsonify({'error': f'Erreur décodage vidéo: {e}'}), 400
        
        if not video_path:
            return jsonify({'error': 'Source vidéo requise'}), 400
        
        # ========== TRAITEMENT VIDÉO ==========
        features_list = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return jsonify({'error': 'Impossible d\'ouvrir la vidéo'}), 400
        
        # Informations sur la vidéo
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        # Sampling intelligent: prendre 1 frame par seconde, max 30 frames
        max_frames = min(30, int(duration) if duration > 0 else 10)
        frame_interval = max(1, total_frames // max_frames) if total_frames > 0 else 1
        
        frame_count = 0
        processed_frames = 0
        
        logger.info(f"🎬 Traitement vidéo: {total_frames} frames, {duration:.1f}s, sampling chaque {frame_interval} frames")
        
        while cap.isOpened() and processed_frames < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Prendre seulement certaines frames
            if frame_count % frame_interval == 0:
                try:
                    # Convertir BGR -> RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    
                    # Préprocessing
                    img_tensor = preprocess(img)
                    batch_tensor = torch.unsqueeze(img_tensor, 0)
                    
                    # Extraction features
                    with torch.no_grad():
                        frame_features = image_model(batch_tensor)
                    
                    features_list.append(frame_features.squeeze().numpy())
                    processed_frames += 1
                    
                except Exception as frame_error:
                    logger.warning(f"Erreur traitement frame {frame_count}: {frame_error}")
                    continue
            
            frame_count += 1
        
        cap.release()
        
        if not features_list:
            return jsonify({'error': 'Aucune frame traitée avec succès'}), 500
        
        # Moyenne des features de toutes les frames
        video_features = np.mean(features_list, axis=0)
        video_features = video_features / np.linalg.norm(video_features)
        
        logger.info(f"✅ Vidéo traitée: {processed_frames} frames -> {len(video_features)} features")
        
        return jsonify({
            'features': video_features.tolist(),
            'video_info': {
                'total_frames': total_frames,
                'processed_frames': processed_frames,
                'duration_seconds': duration,
                'fps': fps
            },
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur process_video: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if temp_file:
            cleanup_temp_file(temp_file)

@app.route('/validate', methods=['POST'])
def validate():
    """Validation améliorée de cohérence texte-média"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        text_features = np.array(data.get('text_features', []))
        media_features = np.array(data.get('media_features', []))
        
        if len(text_features) == 0 or len(media_features) == 0:
            return jsonify({'error': 'Features texte et média requis'}), 400
        
        # Calcul de similarité cosinus
        similarity = cosine_similarity([text_features], [media_features])[0][0]
        
        # Seuils adaptatifs selon le type de contenu
        thresholds = {
            'strict': 0.7,    # Pour contenu très spécifique
            'normal': 0.5,    # Seuil par défaut
            'relaxed': 0.3    # Pour contenu général
        }
        
        validation_mode = data.get('mode', 'normal')
        threshold = thresholds.get(validation_mode, thresholds['normal'])
        
        is_valid = similarity > threshold
        
        # Niveau de confiance
        confidence = min(1.0, similarity / threshold) if threshold > 0 else 0.0
        
        logger.info(f"🔍 Validation: similarité={similarity:.3f}, seuil={threshold}, valide={is_valid}")
        
        return jsonify({
            'is_valid': is_valid,
            'similarity_score': round(similarity, 3),
            'confidence': round(confidence, 3),
            'threshold_used': threshold,
            'validation_mode': validation_mode,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur validation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/categorize', methods=['POST'])
def categorize():
    """Catégorisation intelligente basée sur les features et mots-clés"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400
        
        features = np.array(data.get('features', []))
        text = data.get('text', '').lower()
        
        if len(features) == 0:
            return jsonify({'error': 'Features requis'}), 400
        
        # ========== CATÉGORISATION PAR MOTS-CLÉS ==========
        category_scores = {}
        
        for category, info in CATEGORIES.items():
            score = 0.0
            keywords = info['keywords']
            weight = info['weight']
            
            # Compter les occurrences de mots-clés
            keyword_matches = 0
            for keyword in keywords:
                if keyword in text:
                    keyword_matches += text.count(keyword)
            
            # Calculer le score basé sur les mots-clés
            if keyword_matches > 0:
                score = (keyword_matches / len(keywords)) * weight if keywords else 0
            
            category_scores[category] = score
        
        # ========== CATÉGORISATION PAR FEATURES (SIMPLIFIÉE) ==========
        # Pour une vraie implémentation, il faudrait un modèle entraîné
        # Ici on utilise une heuristique basée sur la magnitude des features
        
        feature_magnitude = np.linalg.norm(features)
        
        # Ajustement basé sur la complexité du contenu
        if feature_magnitude > 100:  # Contenu complexe/riche
            category_scores["Urbanisme"] += 0.2
            category_scores["Événements"] += 0.2
        elif feature_magnitude > 50:  # Contenu moyen
            category_scores["Voirie & Transports"] += 0.1
            category_scores["Propreté"] += 0.1
        
        # ========== SÉLECTION DE LA MEILLEURE CATÉGORIE ==========
        if not any(score > 0 for score in category_scores.values()):
            # Aucune catégorie détectée -> "Autres"
            predicted_category = "Autres"
            confidence = 0.5
        else:
            # Prendre la catégorie avec le meilleur score
            predicted_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[predicted_category]
            confidence = min(1.0, max_score)
        
        logger.info(f"🎯 Catégorie prédite: {predicted_category} (confiance: {confidence:.2f})")
        
        return jsonify({
            'category': predicted_category,
            'confidence': round(confidence, 3),
            'all_scores': {k: round(v, 3) for k, v in category_scores.items()},
            'feature_magnitude': round(feature_magnitude, 2),
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur catégorisation: {e}")
        return jsonify({'error': str(e)}), 500

# ========== ENDPOINTS DE SANTÉ ET DEBUG ==========

@app.route('/health', methods=['GET'])
def health_check():
    """Vérification de l'état du service"""
    try:
        # Test rapide des modèles
        test_text = "test"
        test_inputs = tokenizer(test_text, return_tensors="pt", max_length=10)
        
        with torch.no_grad():
            _ = text_model(**test_inputs)
        
        return jsonify({
            'status': 'healthy',
            'models_loaded': True,
            'endpoints': ['/process_text', '/process_image', '/process_video', '/validate', '/categorize'],
            'timestamp': str(torch.cuda.get_device_name(0)) if torch.cuda.is_available() else 'CPU'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/info', methods=['GET'])
def service_info():
    """Informations sur le service"""
    return jsonify({
        'service': 'AI Validation & Categorization Service',
        'version': '2.0',
        'models': {
            'text': 'bert-base-uncased',
            'image': 'resnet50',
            'video': 'resnet50 (frame sampling)'
        },
        'categories': list(CATEGORIES.keys()),
        'max_file_size': '50MB',
        'supported_formats': {
            'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
            'videos': ['mp4', 'avi', 'mov', 'mkv'],
            'text': 'max 5000 characters'
        }
    })

# ========== GESTION D'ERREURS ==========

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Fichier trop volumineux (max 50MB)'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint non trouvé'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    print("🚀 Démarrage du modèle de validation et catégorisation amélioré")
    print("📡 Accessible sur:")
    print("   - http://127.0.0.1:5001")
    print("   - Endpoints disponibles:")
    print("     * POST /process_text")
    print("     * POST /process_image") 
    print("     * POST /process_video")
    print("     * POST /validate")
    print("     * POST /categorize")
    print("     * GET /health")
    print("     * GET /info")
    print("🔥 Serveur prêt pour les requêtes !")
    
    app.run(host='0.0.0.0', port=5001, debug=True)