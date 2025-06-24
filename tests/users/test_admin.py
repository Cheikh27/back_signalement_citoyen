import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Admin

# @pytest.fixture
# def client() -> FlaskClient: # type: ignore
#     app = create_app(config_name='testing')
#     with app.test_client() as client:
#         with app.app_context():
#             db.create_all()
#         yield client
#         with app.app_context():
#             db.session.remove()
#             db.drop_all()
@pytest.fixture
def client() -> FlaskClient: # type: ignore
    """Fixture pour configurer l'application de test."""
    app = create_app()

    # Appliquer une configuration spécifique pour les tests
    app.config.from_mapping(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",  # Utilisation d'une BD temporaire
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Création des tables
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()  # Nettoyage de la base après chaque test


def test_add_admin(client: FlaskClient):
    # Test pour ajouter un nouvel administrateur
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'prenom': 'Jean'
    }
    response = client.post('/api/admin/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    admin = Admin.query.get(response_json['id'])
    assert admin is not None
    assert admin.nom == test_data['nom']
    assert admin.adresse == test_data['adresse']
    assert admin.role == test_data['role']
    assert admin.username == test_data['username']
    assert admin.image == test_data['image']
    assert admin.telephone == test_data['telephone']
    assert admin.prenom == test_data['prenom']

def test_add_admin_incomplete_data(client: FlaskClient):
    # Test pour ajouter un administrateur avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/admin/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_admin(client: FlaskClient):
    # Test pour récupérer un administrateur par ID
    admin = Admin(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin)
    db.session.commit()
    response = client.get(f'/api/admin/{admin.IDuser}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == admin.IDuser

def test_get_admin_not_found(client: FlaskClient):
    # Test pour récupérer un administrateur inexistant
    response = client.get('/api/admin/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_admins(client: FlaskClient):
    # Test pour lister tous les administrateurs
    admin1 = Admin(
        nom='Admin 1',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='admin1',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    admin2 = Admin(
        nom='Admin 2',
        adresse='456 Rue Exemple',
        password='password123',
        role='admin',
        username='admin2',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin1)
    db.session.add(admin2)
    db.session.commit()
    response = client.get('/api/admin/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_modify_admin(client: FlaskClient):
    # Test pour modifier un administrateur
    admin = Admin(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin)
    db.session.commit()
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse',
        'password': 'newpassword123',
        'image': 'url_to_new_image',
        'prenom': 'Nouveau Prénom'
    }
    response = client.put(f'/api/admin/update/{admin.IDuser}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_admin = Admin.query.get(response_json['id'])
    assert updated_admin.nom == test_data['nom']
    assert updated_admin.adresse == test_data['adresse']
    assert updated_admin.image == test_data['image']
    assert updated_admin.prenom == test_data['prenom']

def test_modify_admin_not_found(client: FlaskClient):
    # Test pour modifier un administrateur inexistant
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse'
    }
    response = client.put('/api/admin/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_admin(client: FlaskClient):
    # Test pour supprimer un administrateur
    admin = Admin(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin)
    db.session.commit()
    response = client.delete(f'/api/admin/delete/{admin.IDuser}')
    assert response.status_code == 204
    deleted_admin = Admin.query.get(admin.IDuser)
    assert deleted_admin is None

def test_remove_admin_not_found(client: FlaskClient):
    # Test pour supprimer un administrateur inexistant
    response = client.delete('/api/admin/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_register_admin(client: FlaskClient):
    # Test pour enregistrer un nouvel administrateur
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'prenom': 'Jean'
    }
    response = client.post('/api/admin/register', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert response_json['message'] == 'Admin registered successfully'
    assert 'access_token' in response_json

def test_register_admin_incomplete_data(client: FlaskClient):
    # Test pour enregistrer un administrateur avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/admin/register', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_login_admin(client: FlaskClient):
    # Test pour connecter un administrateur
    admin = Admin(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    response = client.post('/api/admin/login', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'access_token' in response_json

def test_login_admin_invalid_credentials(client: FlaskClient):
    # Test pour connecter un administrateur avec des identifiants invalides
    test_data = {
        'username': 'dupont',
        'password': 'wrongpassword'
    }
    response = client.post('/api/admin/login', json=test_data)
    assert response.status_code == 401
    response_json = response.get_json()
    assert response_json['message'] == 'Invalid credentials'

def test_logout_admin(client: FlaskClient):
    # Test pour déconnecter un administrateur
    admin = Admin(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/admin/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/api/admin/logout', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['message'] == 'Logout successful'

def test_protected_admin(client: FlaskClient):
    # Test pour accéder à une route protégée
    admin = Admin(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(admin)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/admin/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/api/admin/protected', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == admin.IDuser
    assert response_json['nom'] == admin.nom
    assert response_json['role'] == admin.role
    assert response_json['username'] == admin.username
