from PIL import Image
from flask import Flask, request, jsonify
from transformers import pipeline
import base64
from io import BytesIO


app = Flask(__name__)

# Exemple de contenu pour priorite.py

# Définition des scores et poids
CONTENT_SCORES = {
    'Voirie & Transports': 0.9,
    'Propreté': 0.7,
    'Sécurité': 0.8,
    # Ajoutez d'autres catégories et scores ici
}

GRAVITY_SCORES = {
    'Haute': 1.0,
    'Moyenne': 0.5,
    'Basse': 0.1,
}

LOCATION_SCORES = {
    'Urban': 0.8,
    'Rural': 0.3,
}

URGENCY_SCORES = {
    'Urgent': 1.0,
    'Normal': 0.5,
    'Faible': 0.1,
}

WEIGHTS = {
    'content': 0.4,
    'gravity': 0.3,
    'location': 0.2,
    'urgency': 0.1,
}


# Charger les modèles NLP et de vision par ordinateur
sentiment_analyzer = pipeline("sentiment-analysis")
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")
image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")



def calculate_priority(type_signalement, description, media_list):
    """
    Calcule la priorité d'un signalement en fonction du type, de la description et des médias.
    """
    # Analyser le sentiment de la description
    sentiment_result = sentiment_analyzer(description)
    sentiment_score = sentiment_result[0]['score'] if sentiment_result[0]['label'] == 'POSITIVE' else 1 - sentiment_result[0]['score']

    # Analyser les entités nommées dans la description
    ner_results = ner_pipeline(description)
    entity_score = len(ner_results) / 10  # Normaliser le nombre d'entités

    # Analyser les médias
    media_score = 0
    for media in media_list:
        if media['mimetype'].startswith('image'):
            try:
                # Décoder les données base64 si nécessaire
                if isinstance(media['data'], str):
                    # Si les données sont en base64, les décoder
                    image_data = base64.b64decode(media['data'])
                else:
                    image_data = media['data']

                # Charger et analyser l'image
                image = Image.open(BytesIO(image_data))
                image_result = image_classifier(image)
                media_score += image_result[0]['score']
            except Exception as e:
                print(f"Erreur lors de l'analyse de l'image: {e}")

    # Normaliser le score des médias
    if media_list:
        media_score /= len(media_list)

    # Poids pour chaque critère
    weights = {
        'type': 0.3,
        'sentiment': 0.3,
        'entity': 0.2,
        'media': 0.2
    }

    # Scores pour chaque type de signalement
    type_scores = {
        'Voirie & Transports': 0.9,
        'Propreté': 0.7,
        'Sécurité': 0.8,
        'Espaces Verts': 0.6,
        'Environnement': 0.8,
        'Événements': 0.5,
        'Services Publics': 0.7,
        'Animalier': 0.6,
        'Urbanisme': 0.7,
        'Social & Solidarité': 0.8,
        'Autres': 0.5
    }

    # Calcul du score de type
    type_score = type_scores.get(type_signalement, 0.5)

    # Calcul du score de priorité
    priority_score = (
        weights['type'] * type_score +
        weights['sentiment'] * sentiment_score +
        weights['entity'] * entity_score +
        weights['media'] * media_score
    )

    # Déterminer la priorité en fonction du score
    if priority_score >= 0.7:
        return "Haute"
    elif priority_score >= 0.4:
        return "Moyenne"
    else:
        return "Basse"


@app.route('/calculate_priority', methods=['POST'])
def calculate_priority_endpoint():
    data = request.get_json()
    type_signalement = data.get('type_signalement')
    description = data.get('description')
    media_list = data.get('media_list', [])

    if not type_signalement or not description:
        return jsonify({'error': 'Type de signalement et description requis'}), 400

    priority = calculate_priority(type_signalement, description, media_list)
    return jsonify({'priority': priority})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
