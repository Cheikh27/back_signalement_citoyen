# app/__init__.py - CONFIGURATION COMPLÈTE
from flask import Flask, request, Response
from flask_jwt_extended import JWTManager, decode_token
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_caching import Cache
# from flask_socketio import SocketIO, emit, send
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from flasgger import Swagger
from datetime import timedelta

# Charger les variables d'environnement
load_dotenv()

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
cache = Cache()
# socketio = SocketIO(cors_allowed_origins="*")

# Dictionnaire pour suivre les connexions WebSocket
# connected_users = {}

def create_app():
    app = Flask(__name__)

    # ========== CONFIGURATION FLASK CORE ==========
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
    app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'
    app.config['TESTING'] = os.getenv('TESTING', 'False').lower() == 'true'
    
    # ========== CONFIGURATION BASE DE DONNÉES ==========
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

    # ========== CONFIGURATION JWT ==========
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_jwt_key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))

    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = os.getenv('JWT_HEADER_NAME', 'Authorization')
    app.config['JWT_HEADER_TYPE'] = os.getenv('JWT_HEADER_TYPE', 'Bearer')


    # ========== CONFIGURATION CORS ==========
    app.config['CORS_ORIGINS'] = os.getenv('CORS_ORIGINS', '*')

    # ========== CONFIGURATION CACHE REDIS ==========
    app.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'RedisCache')
    app.config['CACHE_REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
    app.config['CACHE_REDIS_PORT'] = int(os.getenv('REDIS_PORT', 6379))
    app.config['CACHE_REDIS_DB'] = int(os.getenv('REDIS_DB', 0))
    app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL')
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))


    # ========== CONFIGURATION SUPABASE ==========
    app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
    app.config['SUPABASE_ANON_KEY'] = os.getenv('SUPABASE_ANON_KEY')
    app.config['SUPABASE_SERVICE_ROLE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    app.config['SUPABASE_BUCKET_NAME'] = os.getenv('SUPABASE_BUCKET_NAME', 'signalements')
    
    # ========== CONFIGURATION ONESIGNAL ==========
    app.config['ONESIGNAL_APP_ID'] = os.getenv('ONESIGNAL_APP_ID')
    app.config['ONESIGNAL_API_KEY'] = os.getenv('ONESIGNAL_API_KEY')

    # ========== INITIALISATION SUPABASE MEDIA SERVICE ==========
    media_service = None
    supabase_module = None
    
    try:
        # Import du module Supabase
        import app.supabase_media_service as sms
        supabase_module = sms
        
        # Vérification des variables critiques
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Variables Supabase manquantes: {', '.join(missing_vars)}")
        
        # Créer le service média
        media_service = sms.get_media_service()
        
        # Créer le bucket (ignore les erreurs si existe déjà)
        try:
            media_service.create_bucket_if_not_exists()
        except Exception as bucket_error:
            app.logger.warning(f"⚠️ Bucket: {bucket_error}")
        
        # Stocker dans app.config
        app.config['MEDIA_SERVICE'] = media_service
        app.config['SUPABASE_MODULE'] = supabase_module
        
        app.logger.info("✅ Service Supabase initialisé")
        
    except ImportError:
        # Fallback: Service basique
        try:
            from supabase import create_client
            
            class BasicSupabaseService:
                def __init__(self):
                    url = os.getenv('SUPABASE_URL')
                    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    if url and key:
                        self.supabase = create_client(url, key)
                        self.bucket_name = os.getenv('SUPABASE_BUCKET_NAME', 'signalements')
                        self.use_service_role = True
                
                def create_bucket_if_not_exists(self):
                    try:
                        buckets = self.supabase.storage.list_buckets()
                        bucket_exists = any(b.name == self.bucket_name for b in buckets)
                        if not bucket_exists:
                            self.supabase.storage.create_bucket(self.bucket_name, {"public": True})
                    except:
                        pass  # Ignorer les erreurs bucket
            
            media_service = BasicSupabaseService()
            media_service.create_bucket_if_not_exists()
            
            app.config['MEDIA_SERVICE'] = media_service
            app.config['SUPABASE_MODULE'] = None
            
            app.logger.info("✅ Service Supabase basique créé")
            
        except Exception as e:
            app.logger.warning(f"⚠️ Supabase non disponible: {e}")
            app.config['MEDIA_SERVICE'] = None
            app.config['SUPABASE_MODULE'] = None
    
    except Exception as e:
        app.logger.error(f"❌ Erreur Supabase: {e}")
        app.config['MEDIA_SERVICE'] = None
        app.config['SUPABASE_MODULE'] = None
    
    # Stocker les états
    app.config['SUPABASE_AVAILABLE'] = media_service is not None
    app.config['SUPABASE_MODULE_AVAILABLE'] = supabase_module is not None

    # ========== INITIALISATION DES EXTENSIONS ==========
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    cache.init_app(app)
    jwt = JWTManager(app)
    Swagger(app)

    # ========== CONFIGURATION LOGGING ==========
    setup_logging(app)

    # ========== CONFIGURATION PROMETHEUS ==========
    metrics = PrometheusMetrics(app)
    metrics.info("flask_app", "Application Flask", version="1.0.0")
    
    @app.route('/metrics')
    def metrics_endpoint():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    # ========== ROUTES DE MONITORING ==========
    
    @app.route('/health')
    def health_check():
        """État général de l'application"""
        return {
            'status': 'healthy',
            'supabase_available': app.config.get('SUPABASE_AVAILABLE', False),
            'onesignal_configured': bool(app.config.get('ONESIGNAL_APP_ID')),
            'database_configured': bool(app.config.get('SQLALCHEMY_DATABASE_URI')),
            'redis_configured': bool(app.config.get('REDIS_URL')),
            'version': '1.0.0'
        }, 200
    
    @app.route('/health/supabase')
    def supabase_health():
        """État Supabase"""
        try:
            media_service = app.config.get('MEDIA_SERVICE')
            if not media_service:
                return {'status': 'unavailable'}, 503
            
            buckets = media_service.supabase.storage.list_buckets()
            bucket_exists = any(b.name == media_service.bucket_name for b in buckets)
            
            return {
                'status': 'healthy',
                'bucket': media_service.bucket_name,
                'bucket_exists': bucket_exists
            }, 200
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

    @app.route('/health/onesignal')
    def onesignal_health():
        """État OneSignal"""
        app_id = app.config.get('ONESIGNAL_APP_ID')
        api_key = app.config.get('ONESIGNAL_API_KEY')
        
        return {
            'status': 'configured' if app_id and api_key else 'not_configured',
            'app_id_present': bool(app_id),
            'api_key_present': bool(api_key)
        }, 200

    # ========== IMPORT DES MODÈLES ==========
    from app.models import (
        Appartenir, Groupe, CommentairePetition, CommentairePublication,
        CommentaireSignalement, PartagerPetition, PartagerPublication,
        PartagerSignalement, Appreciation, Signature, Vote, Petition,
        Publication, Signalement, Admin, Authorite, Citoyen, Moderateur, User, Tutoriel
    )
    
    # Import des modèles notifications
    from app.models import FCMToken, NotificationHistory

    # ========== IMPORT ET ENREGISTREMENT DES ROUTES ==========
    from app.routes import (
        admin_bp, autorite_bp, citoyen_bp, moderateur_bp, appartenir_bp,
        groupe_bp, commentaire_petition_bp, commentaire_publication_bp,
        commentaire_signalement_bp, partager_petition_bp, partager_publication_bp,
        partager_signalement_bp, appreciation_bp, signature_bp, vote_bp,
        petition_bp, publication_bp, signalement_bp, user_bp, tutoriel_bp, suivre_bp, notification_bp
    )
    
    

    # Enregistrement des blueprints existants
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
    app.register_blueprint(tutoriel_bp, url_prefix='/api/tutoriel')
    app.register_blueprint(suivre_bp, url_prefix='/api/suivre')
    app.register_blueprint(notification_bp, url_prefix='/api/notification')

    # ========== GESTION DES CONNEXIONS WEBSOCKET ==========
    # @socketio.on("connect")
    # def handle_connect():
    #     token = request.args.get("token")
    #     if token:
    #         try:
    #             user_data = decode_token(token)
    #             user_id = user_data["sub"]
    #             connected_users[user_id] = request.sid
    #             print(f"Utilisateur {user_id} connecté avec socket_id {request.sid}")
    #         except Exception as e:
    #             print(f"Erreur WebSocket : {e}")
    #             return False

    # @socketio.on("disconnect")
    # def handle_disconnect():
    #     user_id = None
    #     for uid, socket_id in connected_users.items():
    #         if socket_id == request.sid:
    #             user_id = uid
    #             break
    #     if user_id:
    #         del connected_users[user_id]
    #         print(f"Utilisateur {user_id} déconnecté.")

    # @socketio.on("message")
    # def handle_message(data):
    #     print(f"Message reçu : {data}")
    #     send(f"Serveur : {data}", broadcast=True)

    # @socketio.on("new_comment")
    # def handle_new_comment(data):
    #     print(f"Nouveau commentaire : {data}")
    #     emit("comment_notification", {"message": "Un nouveau commentaire a été ajouté !"}, broadcast=True)

    # @socketio.on("new_message")
    # def handle_new_message(data):
    #     print(f"Nouveau message : {data}")
    #     emit("message_notification", {"message": "Vous avez reçu un nouveau message !"}, broadcast=True)

    # @socketio.on("new_notification")
    # def handle_new_notification(data):
    #     print(f"Nouvelle notification : {data}")
    #     emit("notification_alert", data, broadcast=True)

    return app

def setup_logging(app):
    """Configuration du logging"""
    if not app.debug:
        # Créer le dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Handler pour les logs généraux
        file_handler = RotatingFileHandler(
            os.getenv('LOG_FILE', 'logs/app.log'), 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
        app.logger.addHandler(file_handler)

        app.logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
        app.logger.info('Application démarrage')

# if __name__ == "__main__":
#     app = create_app()
#     socketio.run(app, host="0.0.0.0", port=5000, debug=True)
if __name__ == "__main__":
    app = create_app()
    print("🚀 Démarrage du serveur Flask...")
    print("📡 Accessible sur:")
    print("   - http://127.0.0.1:5000")
    print("   - http://192.168.1.16:5000")
    print("🔥 Serveur prêt pour les requêtes !")
    
    # ✅ Flask simple sans SocketIO
    app.run(host="0.0.0.0", port=5000, debug=True)