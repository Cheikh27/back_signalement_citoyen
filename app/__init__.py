from flask import Flask, request, Response
from flask_jwt_extended import JWTManager, decode_token
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_caching import Cache
from flask_socketio import SocketIO, emit, send
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from flasgger import Swagger

# Charger les variables d'environnement
load_dotenv()

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
cache = Cache()
socketio = SocketIO(cors_allowed_origins="*")  # Autoriser les WebSockets

# Dictionnaire pour suivre les connexions WebSocket
connected_users = {}

def create_app():
    app = Flask(__name__)

    # Configuration de l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_jwt_key')
    app.config['CORS_ORIGINS'] = os.getenv('CORS_ORIGINS', '*')
    app.config['DEBUG'] = os.getenv('DEBUG', 'True')

    # Configuration du cache
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_HOST'] = os.getenv('REDIS_HOST')
    app.config['CACHE_REDIS_PORT'] = int(os.getenv('REDIS_PORT'))
    app.config['CACHE_REDIS_DB'] = int(os.getenv('REDIS_DB'))
    app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL')
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT'))

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    cache.init_app(app)
    jwt = JWTManager(app)
    Swagger(app)

    # Configuration du logging
    if not app.debug:
        handler = RotatingFileHandler('logs/app.log', maxBytes=1000000, backupCount=10)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

    # Configuration de Prometheus pour le monitoring de l'application
    metrics = PrometheusMetrics(app)
    metrics.info("flask_app", "Application Flask de monitoring", version="1.0.0")
    
    @app.route('/metrics')  # Route pour accéder aux metrics
    def metrics_endpoint():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    app.logger.info("PrometheusMetrics chargé avec succès")

    # Import des modèles
    from app.models import (
        Appartenir, Groupe, CommentairePetition, CommentairePublication,
        CommentaireSignalement, PartagerPetition, PartagerPublication,
        PartagerSignalement, Appreciation, Signature, Vote, Petition,
        Publication, Signalement, Admin, Authorite, Citoyen, Moderateur, User
    )

    # Import des routes
    from app.routes import (
        admin_bp, autorite_bp, citoyen_bp, moderateur_bp, appartenir_bp,
        groupe_bp, commentaire_petition_bp, commentaire_publication_bp,
        commentaire_signalement_bp, partager_petition_bp, partager_publication_bp,
        partager_signalement_bp, appreciation_bp, signature_bp, vote_bp,
        petition_bp, publication_bp, signalement_bp, user_bp
    )

    # Enregistrement des blueprints
    app.register_blueprint(appartenir_bp, url_prefix='/api/appartenir')
    app.register_blueprint(groupe_bp, url_prefix='/api/groupe')
    app.register_blueprint(commentaire_petition_bp, url_prefix='/api/commentaire_petition')
    app.register_blueprint(commentaire_publication_bp, url_prefix='/api/commentaire_publication')
    app.register_blueprint(commentaire_signalement_bp, url_prefix='/api/commentaire_signalement')
    app.register_blueprint(partager_petition_bp, url_prefix='/api/partager_petition')
    app.register_blueprint(partager_publication_bp, url_prefix='/api/partager_publication')
    app.register_blueprint(partager_signalement_bp, url_prefix='/api/partager_signalement')
    app.register_blueprint(appreciation_bp, url_prefix='/api/appreciation')
    app.register_blueprint(signature_bp, url_prefix='/api/signature')
    app.register_blueprint(vote_bp, url_prefix='/api/vote')
    app.register_blueprint(petition_bp, url_prefix='/api/petition')
    app.register_blueprint(publication_bp, url_prefix='/api/publication')
    app.register_blueprint(signalement_bp, url_prefix='/api/signalement')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(autorite_bp, url_prefix='/api/autorite')
    app.register_blueprint(citoyen_bp, url_prefix='/api/citoyen')
    app.register_blueprint(moderateur_bp, url_prefix='/api/moderateur')
    app.register_blueprint(user_bp, url_prefix='/api/user')

    # Gestion des connexions WebSocket
    @socketio.on("connect")
    def handle_connect():
        token = request.args.get("token")
        if token:
            try:
                user_data = decode_token(token)
                user_id = user_data["sub"]
                connected_users[user_id] = request.sid
                print(f"Utilisateur {user_id} connecté avec socket_id {request.sid}")
            except Exception as e:
                print(f"Erreur lors de la connexion WebSocket : {e}")
                return False

    @socketio.on("disconnect")
    def handle_disconnect():
        user_id = None
        for uid, socket_id in connected_users.items():
            if socket_id == request.sid:
                user_id = uid
                break
        if user_id:
            del connected_users[user_id]
            print(f"Utilisateur {user_id} déconnecté.")

    @socketio.on("message")
    def handle_message(data):
        print(f"Message reçu : {data}")
        send(f"Serveur : {data}", broadcast=True)

    @socketio.on("new_comment")
    def handle_new_comment(data):
        print(f"Nouveau commentaire : {data}")
        emit("comment_notification", {"message": "Un nouveau commentaire a été ajouté !"}, broadcast=True)

    @socketio.on("new_message")
    def handle_new_message(data):
        print(f"Nouveau message : {data}")
        emit("message_notification", {"message": "Vous avez reçu un nouveau message !"}, broadcast=True)

    @socketio.on("new_notification")
    def handle_new_notification(data):
        print(f"Nouvelle notification : {data}")
        emit("notification_alert", data, broadcast=True)

    return app

if __name__ == "__main__":
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)