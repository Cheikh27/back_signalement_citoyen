import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Citoyen

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


def test_add_citoyen(client: FlaskClient):
    # Test pour ajouter un nouveau citoyen
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'citoyen',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'prenom': 'Jean'
    }
    response = client.post('/api/citoyen/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    citoyen = Citoyen.query.get(response_json['id'])
    assert citoyen is not None
    assert citoyen.nom == test_data['nom']
    assert citoyen.adresse == test_data['adresse']
    assert citoyen.role == test_data['role']
    assert citoyen.username == test_data['username']
    assert citoyen.image == test_data['image']
    assert citoyen.telephone == test_data['telephone']
    assert citoyen.prenom == test_data['prenom']

def test_add_citoyen_incomplete_data(client: FlaskClient):
    # Test pour ajouter un citoyen avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/citoyen/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_citoyen(client: FlaskClient):
    # Test pour récupérer un citoyen par ID
    citoyen = Citoyen(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen)
    db.session.commit()
    response = client.get(f'/api/citoyen/{citoyen.IDuser}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == citoyen.IDuser

def test_get_citoyen_not_found(client: FlaskClient):
    # Test pour récupérer un citoyen inexistant
    response = client.get('/api/citoyen/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_citoyens(client: FlaskClient):
    # Test pour lister tous les citoyens
    citoyen1 = Citoyen(
        nom='Citoyen 1',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='citoyen1',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    citoyen2 = Citoyen(
        nom='Citoyen 2',
        adresse='456 Rue Exemple',
        password='password123',
        role='citoyen',
        username='citoyen2',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen1)
    db.session.add(citoyen2)
    db.session.commit()
    response = client.get('/api/citoyen/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_modify_citoyen(client: FlaskClient):
    # Test pour modifier un citoyen
    citoyen = Citoyen(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen)
    db.session.commit()
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse',
        'password': 'newpassword123',
        'image': 'url_to_new_image',
        'telephone': '0987654321',
        'prenom': 'Nouveau Prénom'
    }
    response = client.put(f'/api/citoyen/update/{citoyen.IDuser}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_citoyen = Citoyen.query.get(response_json['id'])
    assert updated_citoyen.nom == test_data['nom']
    assert updated_citoyen.adresse == test_data['adresse']
    assert updated_citoyen.image == test_data['image']
    assert updated_citoyen.telephone == test_data['telephone']
    assert updated_citoyen.prenom == test_data['prenom']

def test_modify_citoyen_not_found(client: FlaskClient):
    # Test pour modifier un citoyen inexistant
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse'
    }
    response = client.put('/api/citoyen/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_citoyen(client: FlaskClient):
    # Test pour supprimer un citoyen
    citoyen = Citoyen(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen)
    db.session.commit()
    response = client.delete(f'/api/citoyen/delete/{citoyen.IDuser}')
    assert response.status_code == 204
    deleted_citoyen = Citoyen.query.get(citoyen.IDuser)
    assert deleted_citoyen is None

def test_remove_citoyen_not_found(client: FlaskClient):
    # Test pour supprimer un citoyen inexistant
    response = client.delete('/api/citoyen/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_register_citoyen(client: FlaskClient):
    # Test pour enregistrer un nouveau citoyen
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'citoyen',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'prenom': 'Jean'
    }
    response = client.post('/api/citoyen/register', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert response_json['message'] == 'Citoyen registered successfully'
    assert 'access_token' in response_json

def test_register_citoyen_incomplete_data(client: FlaskClient):
    # Test pour enregistrer un citoyen avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/citoyen/register', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_login_citoyen(client: FlaskClient):
    # Test pour connecter un citoyen
    citoyen = Citoyen(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    response = client.post('/api/citoyen/login', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'access_token' in response_json

def test_login_citoyen_invalid_credentials(client: FlaskClient):
    # Test pour connecter un citoyen avec des identifiants invalides
    test_data = {
        'username': 'dupont',
        'password': 'wrongpassword'
    }
    response = client.post('/api/citoyen/login', json=test_data)
    assert response.status_code == 401
    response_json = response.get_json()
    assert response_json['message'] == 'Invalid credentials'

def test_logout_citoyen(client: FlaskClient):
    # Test pour déconnecter un citoyen
    citoyen = Citoyen(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/citoyen/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/api/citoyen/logout', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['message'] == 'Logout successful'

def test_protected_citoyen(client: FlaskClient):
    # Test pour accéder à une route protégée
    citoyen = Citoyen(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='citoyen',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(citoyen)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/citoyen/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/api/citoyen/protected', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == citoyen.IDuser
    assert response_json['nom'] == citoyen.nom
    assert response_json['role'] == citoyen.role
    assert response_json['username'] == citoyen.username
