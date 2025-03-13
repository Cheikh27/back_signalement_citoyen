from flask_caching import Cache
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
cache = Cache()

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

    app.config['CACHE_TYPE'] = os.getenv('CACHE_TYPE', 'simple')
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt = JWTManager(app)
    cache.init_app(app)

    # Import models to ensure they are registered with SQLAlchemy
    from app.models import (
        Appartenir, Groupe, CommentairePetition, CommentairePublication,
        CommentaireSignalement, PartagerPetition, PartagerPublication,
        PartagerSignalement, Appreciation, Signature, Vote, Petition,
        Publication, Signalement, Admin, Authorite, Citoyen, Moderateur, User
    )

    # Register blueprints
    from app.routes import (
        admin_bp, autorite_bp, citoyen_bp, moderateur_bp, appartenir_bp,
        groupe_bp, commentaire_petition_bp, commentaire_publication_bp,
        commentaire_signalement_bp, partager_petition_bp, partager_publication_bp,
        partager_signalement_bp, appreciation_bp, signature_bp, vote_bp,
        petition_bp, publication_bp, signalement_bp
    )

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

    return app
