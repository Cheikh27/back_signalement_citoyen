import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Authorite

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


def test_add_authorite(client: FlaskClient):
    # Test pour ajouter une nouvelle autorité
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'typeAuthorite': 'type1',
        'description': 'Description de l\'autorité'
    }
    response = client.post('/api/autorite/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    authorite = Authorite.query.get(response_json['id'])
    assert authorite is not None
    assert authorite.nom == test_data['nom']
    assert authorite.adresse == test_data['adresse']
    assert authorite.role == test_data['role']
    assert authorite.username == test_data['username']
    assert authorite.image == test_data['image']
    assert authorite.telephone == test_data['telephone']
    assert authorite.typeAuthorite == test_data['typeAuthorite']
    assert authorite.description == test_data['description']

def test_add_authorite_incomplete_data(client: FlaskClient):
    # Test pour ajouter une autorité avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/autorite/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_authorite(client: FlaskClient):
    # Test pour récupérer une autorité par ID
    authorite = Authorite(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité'
    )
    db.session.add(authorite)
    db.session.commit()
    response = client.get(f'/api/autorite/{authorite.IDuser}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == authorite.IDuser

def test_get_authorite_not_found(client: FlaskClient):
    # Test pour récupérer une autorité inexistante
    response = client.get('/api/autorite/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_authorites(client: FlaskClient):
    # Test pour lister toutes les autorités
    authorite1 = Authorite(
        nom='Authorite 1',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='authorite1',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité 1'
    )
    authorite2 = Authorite(
        nom='Authorite 2',
        adresse='456 Rue Exemple',
        password='password123',
        role='admin',
        username='authorite2',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité 2'
    )
    db.session.add(authorite1)
    db.session.add(authorite2)
    db.session.commit()
    response = client.get('/api/autorite/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_modify_authorite(client: FlaskClient):
    # Test pour modifier une autorité
    authorite = Authorite(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité'
    )
    db.session.add(authorite)
    db.session.commit()
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse',
        'password': 'newpassword123',
        'image': 'url_to_new_image',
        'telephone': '0987654321',
        'typeAuthorite': 'type2',
        'description': 'Nouvelle description'
    }
    response = client.put(f'/api/autorite/update/{authorite.IDuser}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_authorite = Authorite.query.get(response_json['id'])
    assert updated_authorite.nom == test_data['nom']
    assert updated_authorite.adresse == test_data['adresse']
    assert updated_authorite.image == test_data['image']
    assert updated_authorite.telephone == test_data['telephone']
    assert updated_authorite.typeAuthorite == test_data['typeAuthorite']
    assert updated_authorite.description == test_data['description']

def test_modify_authorite_not_found(client: FlaskClient):
    # Test pour modifier une autorité inexistante
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse'
    }
    response = client.put('/api/autorite/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_authorite(client: FlaskClient):
    # Test pour supprimer une autorité
    authorite = Authorite(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité'
    )
    db.session.add(authorite)
    db.session.commit()
    response = client.delete(f'/api/autorite/delete/{authorite.IDuser}')
    assert response.status_code == 204
    deleted_authorite = Authorite.query.get(authorite.IDuser)
    assert deleted_authorite is None

def test_remove_authorite_not_found(client: FlaskClient):
    # Test pour supprimer une autorité inexistante
    response = client.delete('/api/autorite/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_register_authorite(client: FlaskClient):
    # Test pour enregistrer une nouvelle autorité
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'typeAuthorite': 'type1',
        'description': 'Description de l\'autorité'
    }
    response = client.post('/api/autorite/register', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert response_json['message'] == 'Authorite registered successfully'
    assert 'access_token' in response_json

def test_register_authorite_incomplete_data(client: FlaskClient):
    # Test pour enregistrer une autorité avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/autorite/register', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_login_authorite(client: FlaskClient):
    # Test pour connecter une autorité
    authorite = Authorite(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité'
    )
    db.session.add(authorite)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    response = client.post('/api/autorite/login', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'access_token' in response_json

def test_login_authorite_invalid_credentials(client: FlaskClient):
    # Test pour connecter une autorité avec des identifiants invalides
    test_data = {
        'username': 'dupont',
        'password': 'wrongpassword'
    }
    response = client.post('/api/autorite/login', json=test_data)
    assert response.status_code == 401
    response_json = response.get_json()
    assert response_json['message'] == 'Invalid credentials'

def test_logout_authorite(client: FlaskClient):
    # Test pour déconnecter une autorité
    authorite = Authorite(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité'
    )
    db.session.add(authorite)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/autorite/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/api/autorite/logout', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['message'] == 'Logout successful'

def test_protected_authorite(client: FlaskClient):
    # Test pour accéder à une route protégée
    authorite = Authorite(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        typeAuthorite='type1',
        description='Description de l\'autorité'
    )
    db.session.add(authorite)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/autorite/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/api/autorite/protected', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == authorite.IDuser
    assert response_json['nom'] == authorite.nom
    assert response_json['role'] == authorite.role
    assert response_json['username'] == authorite.username
