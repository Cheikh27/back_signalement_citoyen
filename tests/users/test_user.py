import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import User

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


def test_add_user(client: FlaskClient):
    # Test pour ajouter un nouvel utilisateur
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'user_type': 'admin'
    }
    response = client.post('/api/user/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    assert 'access_token' in response_json
    user = User.query.get(response_json['id'])
    assert user is not None
    assert user.nom == test_data['nom']
    assert user.adresse == test_data['adresse']
    assert user.role == test_data['role']
    assert user.username == test_data['username']
    assert user.image == test_data['image']
    assert user.telephone == test_data['telephone']
    assert user.type_user == test_data['user_type']

def test_add_user_incomplete_data(client: FlaskClient):
    # Test pour ajouter un utilisateur avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/user/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_user(client: FlaskClient):
    # Test pour récupérer un utilisateur par ID
    user = User(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user)
    db.session.commit()
    response = client.get(f'/api/user/{user.IDuser}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == user.IDuser

def test_get_user_not_found(client: FlaskClient):
    # Test pour récupérer un utilisateur inexistant
    response = client.get('/api/user/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Utilisateur non trouvé'

def test_list_users(client: FlaskClient):
    # Test pour lister tous les utilisateurs
    user1 = User(
        nom='User 1',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='user1',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    user2 = User(
        nom='User 2',
        adresse='456 Rue Exemple',
        password='password123',
        role='admin',
        username='user2',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    response = client.get('/api/user/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_modify_user(client: FlaskClient):
    # Test pour modifier un utilisateur
    user = User(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user)
    db.session.commit()
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse',
        'password': 'newpassword123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_new_image',
        'telephone': '0987654321',
        'user_type': 'admin'
    }
    response = client.put(f'/api/user/update/{user.IDuser}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_user = User.query.get(response_json['id'])
    assert updated_user.nom == test_data['nom']
    assert updated_user.adresse == test_data['adresse']
    assert updated_user.image == test_data['image']
    assert updated_user.telephone == test_data['telephone']
    assert updated_user.type_user == test_data['user_type']

def test_modify_user_not_found(client: FlaskClient):
    # Test pour modifier un utilisateur inexistant
    test_data = {
        'nom': 'Nouveau Nom',
        'adresse': 'Nouvelle Adresse'
    }
    response = client.put('/api/user/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Utilisateur non trouvé'

def test_remove_user(client: FlaskClient):
    # Test pour supprimer un utilisateur
    user = User(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user)
    db.session.commit()
    response = client.delete(f'/api/user/delete/{user.IDuser}')
    assert response.status_code == 204
    deleted_user = User.query.get(user.IDuser)
    assert deleted_user is None

def test_remove_user_not_found(client: FlaskClient):
    # Test pour supprimer un utilisateur inexistant
    response = client.delete('/api/user/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Utilisateur non trouvé'

def test_register_user(client: FlaskClient):
    # Test pour enregistrer un nouvel utilisateur
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple',
        'password': 'password123',
        'role': 'admin',
        'username': 'dupont',
        'image': 'url_to_image',
        'telephone': '0123456789',
        'user_type': 'admin'
    }
    response = client.post('/api/user/register', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert response_json['message'] == 'Enregistrement réussi'
    assert 'access_token' in response_json

def test_register_user_incomplete_data(client: FlaskClient):
    # Test pour enregistrer un utilisateur avec des données incomplètes
    test_data = {
        'nom': 'Dupont',
        'adresse': '123 Rue Exemple'
    }
    response = client.post('/api/user/register', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_login_user(client: FlaskClient):
    # Test pour connecter un utilisateur
    user = User(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    response = client.post('/api/user/login', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'access_token' in response_json

def test_login_user_invalid_credentials(client: FlaskClient):
    # Test pour connecter un utilisateur avec des identifiants invalides
    test_data = {
        'username': 'dupont',
        'password': 'wrongpassword'
    }
    response = client.post('/api/user/login', json=test_data)
    assert response.status_code == 401
    response_json = response.get_json()
    assert response_json['message'] == 'Identifiants invalides'

def test_logout_user(client: FlaskClient):
    # Test pour déconnecter un utilisateur
    user = User(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/user/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/api/user/logout', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['message'] == 'Déconnexion réussie'

def test_protected_user(client: FlaskClient):
    # Test pour accéder à une route protégée
    user = User(
        nom='Dupont',
        adresse='123 Rue Exemple',
        password='password123',
        role='admin',
        username='dupont',
        image='url_to_image',
        telephone='0123456789',
        type_user='admin'
    )
    db.session.add(user)
    db.session.commit()
    test_data = {
        'username': 'dupont',
        'password': 'password123'
    }
    login_response = client.post('/api/user/login', json=test_data)
    assert login_response.status_code == 200
    access_token = login_response.get_json()['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.get('/api/user/protected', headers=headers)
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == user.IDuser
    assert response_json['nom'] == user.nom
    assert response_json['role'] == user.role
    assert response_json['username'] == user.username
