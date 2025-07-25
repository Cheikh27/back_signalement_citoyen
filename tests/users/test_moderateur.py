from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Moderateur
import pytest

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


def test_add_moderateur(client: FlaskClient):
    # Test pour ajouter un nouveau modérateur
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'moderateur',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'prenom': 'Jean'
    }
    response = client.post('/api/moderateur/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    moderateur = Moderateur.query.get(response_json['id'])
    assert moderateur is not None
    assert moderateur.nom == test_data['nom']
    assert moderateur.adresse == test_data['adresse']
    assert moderateur.role == test_data['role']
    assert moderateur.username == test_data['username']
    assert moderateur.image == test_data['image']
    assert moderateur.telephone == test_data['telephone']
    assert moderateur.prenom == test_data['prenom']

def test_add_moderateur_incomplete_data(client: FlaskClient):
    # Test pour ajouter un modérateur avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/moderateur/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_moderateur(client: FlaskClient):
    # Test pour récupérer un modérateur par ID
    moderateur = Moderateur(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur)
    db.session.commit()
    response = client.get(f'/api/moderateur/{moderateur.IDuser}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == moderateur.IDuser

def test_get_moderateur_not_found(client: FlaskClient):
    # Test pour récupérer un modérateur inexistant
    response = client.get('/api/moderateur/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_moderateurs(client: FlaskClient):
    # Test pour lister tous les modérateurs
    moderateur1 = Moderateur(
        nom='Moderateur 1',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='moderateur1',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    moderateur2 = Moderateur(
        nom='Moderateur 2',
        adresse='456 Rue Exemple',
        password='password123',
        role='moderateur',
        username='moderateur2',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur1)
    db.session.add(moderateur2)
    db.session.commit()
    response = client.get('/api/moderateur/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_modify_moderateur(client: FlaskClient):
    # Test pour modifier un modérateur
    moderateur = Moderateur(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur)
    db.session.commit()
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse',
        'password': 'newpassword123',
        'image': 'url_to_new_image',
        'prenom': 'Nouveau Prénom'
    }
    response = client.put(f'/api/moderateur/update/{moderateur.IDuser}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_moderateur = Moderateur.query.get(response_json['id'])
    assert updated_moderateur.nom == test_data['nom']
    assert updated_moderateur.adresse == test_data['adresse']
    assert updated_moderateur.image == test_data['image']
    assert updated_moderateur.prenom == test_data['prenom']

def test_modify_moderateur_not_found(client: FlaskClient):
    # Test pour modifier un modérateur inexistant
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse'
    }
    response = client.put('/api/moderateur/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_moderateur(client: FlaskClient):
    # Test pour supprimer un modérateur
    moderateur = Moderateur(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur)
    db.session.commit()
    response = client.delete(f'/api/moderateur/delete/{moderateur.IDuser}')
    assert response.status_code == 204
    deleted_moderateur = Moderateur.query.get(moderateur.IDuser)
    assert deleted_moderateur is None

def test_remove_moderateur_not_found(client: FlaskClient):
    # Test pour supprimer un modérateur inexistant
    response = client.delete('/api/moderateur/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_register_moderateur(client: FlaskClient):
    # Test pour enregistrer un nouveau modérateur
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'moderateur',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'prenom': 'Jean'
    }
    response = client.post('/api/moderateur/register', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert response_json['message'] == 'Moderateur registered successfully'
    assert 'access_token' in response_json

def test_register_moderateur_incomplete_data(client: FlaskClient):
    # Test pour enregistrer un modérateur avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/moderateur/register', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_login_moderateur(client: FlaskClient):
    # Test pour connecter un modérateur
    moderateur = Moderateur(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    response = client.post('/api/moderateur/login', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'access_token' in response_json

def test_login_moderateur_invalid_credentials(client: FlaskClient):
    # Test pour connecter un modérateur avec des identifiants invalides
    test_data = {
        'username': 'dupont',
        'password': 'wrongpassword'
    }
    response = client.post('/api/moderateur/login', json=test_data)
    assert response.status_code == 401
    response_json = response.get_json()
    assert response_json['message'] == 'Invalid credentials'

def test_logout_moderateur(client: FlaskClient):
    # Test pour déconnecter un modérateur
    moderateur = Moderateur(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/moderateur/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/api/moderateur/logout', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['message'] == 'Logout successful'

def test_protected_moderateur(client: FlaskClient):
    # Test pour accéder à une route protégée
    moderateur = Moderateur(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='moderateur',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        prenom='Jean'
    )
    db.session.add(moderateur)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/moderateur/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/api/moderateur/protected', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == moderateur.IDuser
    assert response_json['nom'] == moderateur.nom
    assert response_json['role'] == moderateur.role
    assert response_json['username'] == moderateur.username
