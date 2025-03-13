import pytest # type: ignore
from app import create_app, db
from app.models.users.autorite_model import Authorite
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app('testing')  # Assurez-vous d'avoir une config pour le mode test
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    with app.app_context():
        authorite = Authorite(
            nom='Admin',
            adresse='Dakar',
            password=generate_password_hash('password123'),
            role='admin',
            username='admin_user',
            image='',
            telephone='777123456',
            typeAuthorite='Police',
            description='Superviseur'
        )
        db.session.add(authorite)
        db.session.commit()
        token = create_access_token(identity=authorite.IDuser)
        return {'Authorization': f'Bearer {token}'}

# Test de création d'une autorité
def test_add_authorite(client):
    response = client.post('/authorites/add', json={
        'nom': 'Test Autorite',
        'adresse': 'Dakar',
        'password': 'password123',
        'role': 'agent',
        'username': 'test_user',
        'image': '',
        'telephone': '778888999',
        'typeAuthorite': 'Douane',
        'description': 'Agent de contrôle'
    })
    assert response.status_code == 201
    assert 'id' in response.get_json()

# Test de récupération d'une autorité par ID
def test_get_authorite(client, auth_headers):
    response = client.get('/authorites/1', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['nom'] == 'Admin'

# Test de mise à jour d'une autorité
def test_update_authorite(client, auth_headers):
    response = client.put('/authorites/update/1', json={'nom': 'Updated Name'}, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['id'] == 1

# Test de suppression d'une autorité
def test_delete_authorite(client, auth_headers):
    response = client.delete('/authorites/delete/1', headers=auth_headers)
    assert response.status_code == 204

# Test d'authentification
def test_login(client):
    response = client.post('/authorites/login', json={'username': 'admin_user', 'password': 'password123'})
    assert response.status_code == 200
    assert 'access_token' in response.get_json()
