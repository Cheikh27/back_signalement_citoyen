from flask import Flask, request, jsonify
import spacy
from PIL import Image
import io
import base64
from transformers import pipeline
import logging

# Initialiser l'application Flask
app = Flask(__name__)

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger le modèle spaCy pour le traitement du texte
nlp = spacy.load("fr_core_news_sm")

# Charger un modèle de classification d'images pré-entraîné
image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

def moderer_texte(description):
    doc = nlp(description)
    mots_interdits = {"insulte", "gros mot", "haine"}  # Utilisation d'un ensemble pour une recherche plus rapide

    if any(token.text.lower() in mots_interdits for token in doc):
        return False, "Contenu inapproprié détecté"

    return True, "Contenu valide"

def moderer_media(media_data):
    try:
        # Décoder et ouvrir l'image
        image_data = base64.b64decode(media_data)
        image = Image.open(io.BytesIO(image_data))

        # Utiliser un modèle de classification d'images pour détecter du contenu inapproprié
        results = image_classifier(image)

        # Exemple de logique de modération : vérifier si l'image contient des éléments inappropriés
        for result in results:
            if result['label'] in ["weapons", "adult content"]:  # Ajoutez vos propres labels inappropriés
                return False, f"Contenu inapproprié détecté: {result['label']}"

        return True, "Média valide"
    except Exception as e:
        logger.error(f"Erreur lors de la modération du média: {str(e)}")
        return False, f"Erreur lors de la modération du média: {str(e)}"

def moderer_signalement(type_signalement, description, media_list):
    types_valides = {"Voirie & Transports", "Propreté", "Sécurité", "Espaces Verts", "Environnement", "Services Publics", "Animalier", "Urbanisme", "Social & Solidarité"}

    if type_signalement not in types_valides:
        return False, "Type de signalement invalide"

    texte_valide, message_texte = moderer_texte(description)
    if not texte_valide:
        return False, message_texte

    for media in media_list:
        media_valide, message_media = moderer_media(media)
        if not media_valide:
            return False, message_media

    return True, "Signalement valide"

@app.route('/moderate', methods=['POST'])
def moderate():
    data = request.get_json()

    type_signalement = data.get('type_signalement')
    description = data.get('description')
    media_list = data.get('media_list', [])

    is_valid, message = moderer_signalement(type_signalement, description, media_list)

    if is_valid:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
