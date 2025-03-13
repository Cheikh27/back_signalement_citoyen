import pytest # type: ignore
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.models.users.citoyen_model import Citoyen
from app.services.users.citoyen_service import (
    create_citoyen, get_citoyen_by_id, get_all_citoyens,
    update_citoyen, delete_citoyen, authenticate_citoyen
)

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

# Test de création d'un citoyen
def test_create_citoyen(app, sample_citoyen):
    with app.app_context():
        new_citoyen, access_token = create_citoyen(
            nom="Jane",
            adresse="456 Rue Test",
            password="password123",
            role="user",
            username="janedoe",
            image="image2.jpg",
            telephone="0987654321",
            prenom="Jane"
        )
        assert new_citoyen is not None
        assert access_token is not None
        assert new_citoyen.nom == "Jane"
        assert new_citoyen.username == "janedoe"

# Test de récupération d'un citoyen par ID
def test_get_citoyen_by_id(app, sample_citoyen):
    with app.app_context():
        citoyen = get_citoyen_by_id(sample_citoyen.IDuser)
        assert citoyen is not None
        assert citoyen.nom == "Doe"
        assert citoyen.username == "johndoe"

# Test de récupération de tous les citoyens
def test_get_all_citoyens(app, sample_citoyen):
    with app.app_context():
        citoyens = get_all_citoyens()
        assert len(citoyens) == 1
        assert citoyens[0].nom == "Doe"

# Test de mise à jour d'un citoyen
def test_update_citoyen(app, sample_citoyen):
    with app.app_context():
        updated_citoyen = update_citoyen(
            sample_citoyen.IDuser,
            nom="John Updated",
            adresse="456 Rue Updated",
            password="newpassword123",
            role="admin",
            username="johnupdated",
            image="updated.jpg",
            telephone="1111111111",
            prenom="John Updated"
        )
        assert updated_citoyen is not None
        assert updated_citoyen.nom == "John Updated"
        assert updated_citoyen.username == "johnupdated"

# Test de suppression d'un citoyen
def test_delete_citoyen(app, sample_citoyen):
    with app.app_context():
        success = delete_citoyen(sample_citoyen.IDuser)
        assert success is True
        citoyen = get_citoyen_by_id(sample_citoyen.IDuser)
        assert citoyen.is_deleted is True

# Test d'authentification d'un citoyen
def test_authenticate_citoyen(app, sample_citoyen):
    with app.app_context():
        citoyen = authenticate_citoyen("johndoe", "password123")
        assert citoyen is not None
        assert citoyen.nom == "Doe"

# Test d'authentification avec des identifiants invalides
def test_authenticate_citoyen_invalid_credentials(app, sample_citoyen):
    with app.app_context():
        citoyen = authenticate_citoyen("johndoe", "wrongpassword")
        assert citoyen is None

# Test de la route protégée avec JWT
def test_protected_route(app, client, sample_citoyen):
    with app.app_context():
        # Créer un token JWT pour le citoyen
        access_token = create_access_token(identity=sample_citoyen.IDuser)
        # Tester la route protégée
        response = client.get('/citoyens/protected', headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        assert response.json['id'] == sample_citoyen.IDuser
        assert response.json['nom'] == "Doe"

# Test de la route de connexion
def test_login_route(app, client, sample_citoyen):
    with app.app_context():
        response = client.post('/citoyens/login', json={
            'username': 'johndoe',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json

# Test de la route de déconnexion
def test_logout_route(app, client, sample_citoyen):
    with app.app_context():
        # Créer un token JWT pour le citoyen
        access_token = create_access_token(identity=sample_citoyen.IDuser)
        # Tester la route de déconnexion
        response = client.post('/citoyens/logout', headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        assert response.json['message'] == 'Logout successful'

# Test de la route d'inscription
def test_register_route(app, client):
    with app.app_context():
        response = client.post('/citoyens/register', json={
            'nom': 'Jane',
            'adresse': '456 Rue Test',
            'password': 'password123',
            'role': 'user',
            'username': 'janedoe',
            'image': 'image2.jpg',
            'telephone': '0987654321',
            'prenom': 'Jane',
            'user_type': 'citoyen'
        })
        assert response.status_code == 201
        assert 'access_token' in response.json
        assert response.json['message'] == 'Citoyen registered successfully'