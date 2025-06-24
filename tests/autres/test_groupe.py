import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Groupe

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


def test_add_groupe(client: FlaskClient):
    # Test pour ajouter un nouveau groupe
    test_data = {
        'nom': 'Nouveau Groupe',
        'description': 'Description du groupe',
        'image': 'http://example.com/image.png',
        'admin': 1
    }
    response = client.post('/api/groupe/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    groupe = Groupe.query.get(response_json['id'])
    assert groupe is not None
    assert groupe.nom == test_data['nom']
    assert groupe.description == test_data['description']
    assert groupe.image == test_data['image']
    assert groupe.admin == test_data['admin']

def test_add_groupe_incomplete_data(client: FlaskClient):
    # Test pour ajouter un groupe avec des données incomplètes
    test_data = {
        'nom': 'Nouveau Groupe',
        'description': 'Description du groupe'
    }
    response = client.post('/api/groupe/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_groupe(client: FlaskClient):
    # Test pour récupérer un groupe par ID
    groupe = Groupe(nom='Groupe Test', description='Description', image='http://example.com/image.png', admin=1)
    db.session.add(groupe)
    db.session.commit()
    response = client.get(f'/api/groupe/{groupe.IDgroupe}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == groupe.IDgroupe

def test_get_groupe_not_found(client: FlaskClient):
    # Test pour récupérer un groupe inexistant
    response = client.get('/api/groupe/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_groupes(client: FlaskClient):
    # Test pour lister tous les groupes
    groupe1 = Groupe(nom='Groupe 1', description='Description 1', image='http://example.com/image1.png', admin=1)
    groupe2 = Groupe(nom='Groupe 2', description='Description 2', image='http://example.com/image2.png', admin=2)
    db.session.add(groupe1)
    db.session.add(groupe2)
    db.session.commit()
    response = client.get('/api/groupe/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_modify_groupe(client: FlaskClient):
    # Test pour modifier un groupe
    groupe = Groupe(nom='Groupe Test', description='Description', image='http://example.com/image.png', admin=1)
    db.session.add(groupe)
    db.session.commit()
    test_data = {
        'nom': 'Nouveau Nom',
        'description': 'Nouvelle Description',
        'image': 'http://example.com/new_image.png',
        'admin': 2
    }
    response = client.put(f'/api/groupe/update/{groupe.IDgroupe}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_groupe = Groupe.query.get(response_json['id'])
    assert updated_groupe.nom == test_data['nom']
    assert updated_groupe.description == test_data['description']
    assert updated_groupe.image == test_data['image']
    assert updated_groupe.admin == test_data['admin']

def test_modify_groupe_not_found(client: FlaskClient):
    # Test pour modifier un groupe inexistant
    test_data = {
        'nom': 'Nouveau Nom',
        'description': 'Nouvelle Description',
        'image': 'http://example.com/new_image.png',
        'admin': 2
    }
    response = client.put('/api/groupe/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_groupe(client: FlaskClient):
    # Test pour supprimer un groupe
    groupe = Groupe(nom='Groupe Test', description='Description', image='http://example.com/image.png', admin=1)
    db.session.add(groupe)
    db.session.commit()
    response = client.delete(f'/api/groupe/delete/{groupe.IDgroupe}')
    assert response.status_code == 204
    deleted_groupe = Groupe.query.get(groupe.IDgroupe)
    assert deleted_groupe is None

def test_remove_groupe_not_found(client: FlaskClient):
    # Test pour supprimer un groupe inexistant
    response = client.delete('/api/groupe/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
