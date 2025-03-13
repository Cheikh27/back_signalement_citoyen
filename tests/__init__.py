# tests/__init__.py

from datetime import datetime
import pytest # type: ignore
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash

# Configuration de l'application Flask pour les tests
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test_secret_key"
    })
    JWTManager(app)
    db = SQLAlchemy(app)
    app.db = db

    with app.app_context():
        db.create_all()
    yield app

    with app.app_context():
        db.drop_all()

# Client de test
@pytest.fixture
def client(app):
    return app.test_client()

# Fixture pour créer un citoyen de test
@pytest.fixture
def sample_citoyen(app):
    with app.app_context():
        from app.models.users.citoyen_model import Citoyen
        citoyen = Citoyen(
            nom="Doe",
            adresse="123 Rue Test",
            password=generate_password_hash("password123"),
            role="user",
            username="johndoe",
            image="image.jpg",
            telephone="1234567890",
            prenom="John",
            dateCreated=datetime.utcnow(),
            type_user="citoyen"
        )
        app.db.session.add(citoyen)
        app.db.session.commit()
        return citoyen

# Fixture pour créer un modérateur de test
@pytest.fixture
def sample_moderateur(app):
    with app.app_context():
        from app.models.users.moderateur_model import Moderateur
        moderateur = Moderateur(
            nom="Doe",
            adresse="123 Rue Test",
            password=generate_password_hash("password123"),
            role="admin",
            username="johndoe",
            image="image.jpg",
            telephone="1234567890",
            prenom="John",
            dateCreated=datetime.utcnow(),
            type_user="moderateur"
        )
        app.db.session.add(moderateur)
        app.db.session.commit()
        return moderateur

# Importer les fichiers de test pour les rendre accessibles
from .autres.test_appartenir import *
from .autres.test_groupe import *


from .commentaire.test_commentaireSignalement import *
from .commentaire.test_commentairePublication import *
from .commentaire.test_commentairePetition import *

from .partage.test_partagePetition import *
from .partage.test_partagePublication import *
from .partage.test_partageSignalement import *

from .reaction.test_appreciation import *
from .reaction.test_signature import *
from .reaction.test_vote import *

from .signal.test_petition import *
from .signal.test_publication import *
from .signal.test_signalement import *

from .users.test_admin import *
from .users.test_autorite import *
from .users.test_citoyen import *
from .users.test_moderateur import *
from .users.user_service import *
