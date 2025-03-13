import pytest # type: ignore
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.models.users.user_model import User
from app.services.users.user_service import (
    create_user, get_user_by_id, get_all_users,
    update_user, delete_user, authenticate_user
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

# Fixture pour créer un utilisateur de test
@pytest.fixture
def sample_user(app):
    with app.app_context():
        user = User(
            nom="Doe",
            adresse="123 Rue Test",
            password=generate_password_hash("password123"),
            role="admin",
            username="johndoe",
            image="image.jpg",
            telephone="1234567890",
            prenom="John",
            dateCreated=datetime.utcnow(),
            type_user="admin"
        )
        app.db.session.add(user)
        app.db.session.commit()
        return user

# Test de création d'un utilisateur
def test_create_user(app):
    with app.app_context():
        new_user, access_token = create_user(
            nom="Jane",
            adresse="456 Rue Test",
            password="password123",
            role="admin",
            username="janedoe",
            image="image2.jpg",
            telephone="0987654321",
            prenom="Jane",
            user_type="admin"
        )
        assert new_user is not None
        assert access_token is not None
        assert new_user.nom == "Jane"
        assert new_user.username == "janedoe"

# Test de récupération d'un utilisateur par ID
def test_get_user_by_id(app, sample_user):
    with app.app_context():
        user = get_user_by_id(sample_user.IDuser)
        assert user is not None
        assert user.nom == "Doe"
        assert user.username == "johndoe"

# Test de récupération de tous les utilisateurs
def test_get_all_users(app, sample_user):
    with app.app_context():
        users = get_all_users()
        assert len(users) == 1
        assert users[0].nom == "Doe"

# Test de mise à jour d'un utilisateur
def test_update_user(app, sample_user):
    with app.app_context():
        updated_user = update_user(
            sample_user.IDuser,
            nom="John Updated",
            adresse="456 Rue Updated",
            password="newpassword123",
            role="superadmin",
            username="johnupdated",
            image="updated.jpg",
            telephone="1111111111",
            prenom="John Updated"
        )
        assert updated_user is not None
        assert updated_user.nom == "John Updated"
        assert updated_user.username == "johnupdated"

# Test de suppression d'un utilisateur
def test_delete_user(app, sample_user):
    with app.app_context():
        success = delete_user(sample_user.IDuser)
        assert success is True
        user = get_user_by_id(sample_user.IDuser)
        assert user.is_deleted is True

# Test d'authentification d'un utilisateur
def test_authenticate_user(app, sample_user):
    with app.app_context():
        user = authenticate_user("johndoe", "password123")
        assert user is not None
        assert user.nom == "Doe"

# Test d'authentification avec des identifiants invalides
def test_authenticate_user_invalid_credentials(app, sample_user):
    with app.app_context():
        user = authenticate_user("johndoe", "wrongpassword")
        assert user is None

# Test de la route protégée avec JWT
def test_protected_route(app, client, sample_user):
    with app.app_context():
        # Créer un token JWT pour l'utilisateur
        access_token = create_access_token(identity=sample_user.IDuser)
        # Tester la route protégée
        response = client.get('/users/protected', headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        assert response.json['id'] == sample_user.IDuser
        assert response.json['nom'] == "Doe"

# Test de la route de connexion
def test_login_route(app, client, sample_user):
    with app.app_context():
        response = client.post('/users/login', json={
            'username': 'johndoe',
            'password': 'password123'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json

# Test de la route de déconnexion
def test_logout_route(app, client, sample_user):
    with app.app_context():
        # Créer un token JWT pour l'utilisateur
        access_token = create_access_token(identity=sample_user.IDuser)
        # Tester la route de déconnexion
        response = client.post('/users/logout', headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200
        assert response.json['message'] == 'Logout successful'

# Test de la route d'inscription
def test_register_route(app, client):
    with app.app_context():
        response = client.post('/users/register', json={
            'nom': 'Jane',
            'adresse': '456 Rue Test',
            'password': 'password123',
            'role': 'admin',
            'username': 'janedoe',
            'image': 'image2.jpg',
            'telephone': '0987654321',
            'prenom': 'Jane',
            'user_type': 'admin'
        })
        assert response.status_code == 201
        assert 'access_token' in response.json
        assert response.json['message'] == 'User registered successfully'
