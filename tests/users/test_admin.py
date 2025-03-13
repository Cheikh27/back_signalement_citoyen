import pytest # type: ignore
from flask import Flask
from flask_jwt_extended import create_access_token
from app.routes.users.admin_route import admin_bp
from app.models.users.admin_model import Admin
from app.services.users.admin_service import create_admin, get_admin_by_id, get_all_admins, update_admin, delete_admin, authenticate_admin
from app import db

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test_secret"
    db.init_app(app)
    app.register_blueprint(admin_bp, url_prefix="/api")
    
    with app.app_context():
        db.create_all()
    
    yield app
    
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin():
    return create_admin(
        nom="Test", adresse="Dakar", password="password", role="admin",
        username="testadmin", image="", telephone="777777777", prenom="User"
    )[0]

@pytest.fixture
def access_token(admin):
    return create_access_token(identity=admin.IDuser)

# Test d'ajout d'un admin
def test_add_admin(client):
    response = client.post("/api/admins/add", json={
        "nom": "John",
        "adresse": "Dakar",
        "password": "1234",
        "role": "admin",
        "username": "john123",
        "image": "",
        "telephone": "777777777",
        "prenom": "Doe"
    })
    assert response.status_code == 201
    assert "access_token" in response.get_json()

# Test de récupération d'un admin par ID
def test_get_admin(client, admin):
    response = client.get(f"/api/admins/{admin.IDuser}")
    assert response.status_code == 200
    assert response.get_json()["nom"] == "Test"

# Test de récupération de tous les admins
def test_get_all_admins(client, admin):
    response = client.get("/api/admins/all")
    assert response.status_code == 200
    assert len(response.get_json()) > 0

# Test de mise à jour d'un admin
def test_update_admin(client, admin):
    response = client.put(f"/api/admins/update/{admin.IDuser}", json={"nom": "Updated"})
    assert response.status_code == 200
    updated_admin = get_admin_by_id(admin.IDuser)
    assert updated_admin.nom == "Updated"

# Test de suppression d'un admin
def test_delete_admin(client, admin):
    response = client.delete(f"/api/admins/delete/{admin.IDuser}")
    assert response.status_code == 204
    assert get_admin_by_id(admin.IDuser) is None

# Test de connexion
def test_login(client, admin):
    response = client.post("/api/admins/login", json={
        "username": "testadmin",
        "password": "password"
    })
    assert response.status_code == 200
    assert "access_token" in response.get_json()

# Test d'accès à une route protégée
def test_protected_route(client, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/admins/protected", headers=headers)
    assert response.status_code == 200
    assert "id" in response.get_json()
