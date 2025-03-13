import pytest # type: ignore
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.models.users.moderateur_model import Moderateur
from app.services.users.moderateur_service import (
    create_moderateur, get_moderateur_by_id, get_all_moderateurs,
    update_moderateur, delete_moderateur, authenticate_moderateur
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

# Fixture pour créer un modérateur de test
@pytest.fixture
def sample_moderateur(app):
    with app.app_context():
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

# Test de création d'un modérateur
def test_create_moderateur(app, sample_moderateur):
    with app.app_context():
        new_moderateur, access_token = create_moderateur(
            nom="Jane",
            adresse="456 Rue Test",
            password="password123",
            role="admin",
            username="janedoe",
            image="image2.jpg",
            telephone="0987654321",
            prenom="Jane"
        )
        assert new_moderateur is not None
        assert access_token is not None
        assert new_moderateur.nom == "Jane"
        assert new_moderateur.username == "janedoe"

# Test de récupération d'un modérateur par ID
def test_get_moderateur_by_id(app, sample_moderateur):
    with app.app_context():
        moderateur = get_moderateur_by_id(sample_moderateur.IDuser)
        assert moderateur is not None
        assert moderateur.nom == "Doe"
        assert moderateur.username == "johndoe"

# Test de récupération de tous les modérateurs
def test_get_all_moderateurs(app, sample_moderateur):
    with app.app_context():
        moderateurs = get_all_moderateurs()
        assert len(moderateurs) == 1
        assert moderateurs[0].nom == "Doe"

# Test de mise à jour d'un modérateur
def test_update_moderateur(app, sample_moderateur):
    with app.app_context():
        updated_moderateur = update_moderateur(
            sample_moderateur.IDuser,
            nom="John Updated",
            adresse="456 Rue Updated",
            password="newpassword123",
            role="superadmin",
            username="johnupdated",
            image="updated.jpg",
            telephone="1111111111",
            prenom="John Updated"
        )
        assert updated_moderateur is not None
        assert updated_moderateur.nom == "John Updated"
        assert updated_moderateur.username == "johnupdated"

# Test de suppression d'un modérateur
def test_delete_moderateur(app, sample_moderateur):
    with app.app_context():
        success = delete_moderateur(sample_moderateur.IDuser)
        assert success is True
        moderateur = get_moderateur_by_id(sample_moderateur.IDuser)
        assert moderateur.is_deleted is True

# Test d'authentification d'un modérateur
def test_authenticate_moderateur(app, sample_moderateur):
    with app.app_context():
        moderateur = authenticate_moderateur("johndoe", "password123")
        assert moderateur is not None
        assert moderateur.nom == "Doe"

# Test d'authentification avec des identifiants invalides
def test_authenticate_moderateur_invalid_credentials(app, sample_moderateur):
    with app.app_context():
        moderateur = authenticate_moderateur("johndoe", "wrongpassword")
        assert moderateur is None

# Test de la route protégée avec JWT
def test_protected_route(app, client, sample_moderateur):
    with app.app_context():
        # Créer un token JWT pour le modérateur
        access_token = create_access_token(identity=sample_moderateur.IDuser)
        # Tester la route protégée
        response = client.get('/moderateurs/protected', headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        assert response.json['id'] == sample_moderateur.IDuser
        assert response.json['nom'] == "Doe"

# Test de la route de connexion
def test_login_route(app, client, sample_moderateur):
    with app.app_context():
        response = client.post('/moderateurs/login', json={
            'username': 'johndoe',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json

# Test de la route de déconnexion
def test_logout_route(app, client, sample_moderateur):
    with app.app_context():
        # Créer un token JWT pour le modérateur
        access_token = create_access_token(identity=sample_moderateur.IDuser)
        # Tester la route de déconnexion
        response = client.post('/moderateurs/logout', headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        assert response.json['message'] == 'Logout successful'

# Test de la route d'inscription
def test_register_route(app, client):
    with app.app_context():
        response = client.post('/moderateurs/register', json={
            'nom': 'Jane',
            'adresse': '456 Rue Test',
            'password': 'password123',
            'role': 'admin',
            'username': 'janedoe',
            'image': 'image2.jpg',
            'telephone': '0987654321',
            'prenom': 'Jane',
            'user_type': 'moderateur'
        })
        assert response.status_code == 201
        assert 'access_token' in response.json
        assert response.json['message'] == 'Moderateur registered successfully'