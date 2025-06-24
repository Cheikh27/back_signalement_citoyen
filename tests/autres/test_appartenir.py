import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Appartenir

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


def test_add_appartenir(client: FlaskClient):
    # Test pour ajouter un nouvel enregistrement
    test_data = {
        'citoyen_id': 1,
        'groupe_id': 1
    }
    response = client.post('/api/appartenir/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    appartenir = Appartenir.query.get(response_json['id'])
    assert appartenir is not None
    assert appartenir.citoyenID == test_data['citoyen_id']
    assert appartenir.groupeID == test_data['groupe_id']

def test_add_appartenir_incomplete_data(client: FlaskClient):
    # Test pour ajouter un enregistrement avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/appartenir/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_appartenir(client: FlaskClient):
    # Test pour récupérer un enregistrement par ID
    appartenir = Appartenir(citoyenID=1, groupeID=1)
    db.session.add(appartenir)
    db.session.commit()
    response = client.get(f'/api/appartenir/{appartenir.IDappartenir}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == appartenir.IDappartenir

def test_get_appartenir_not_found(client: FlaskClient):
    # Test pour récupérer un enregistrement inexistant
    response = client.get('/api/appartenir/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_appartenirs(client: FlaskClient):
    # Test pour lister tous les enregistrements
    appartenir1 = Appartenir(citoyenID=1, groupeID=1)
    appartenir2 = Appartenir(citoyenID=2, groupeID=2)
    db.session.add(appartenir1)
    db.session.add(appartenir2)
    db.session.commit()
    response = client.get('/api/appartenir/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_appartenirs_by_citoyen(client: FlaskClient):
    # Test pour lister les enregistrements par citoyen
    appartenir = Appartenir(citoyenID=1, groupeID=1)
    db.session.add(appartenir)
    db.session.commit()
    response = client.get('/api/appartenir/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_appartenirs_by_groupe(client: FlaskClient):
    # Test pour lister les enregistrements par groupe
    appartenir = Appartenir(citoyenID=1, groupeID=1)
    db.session.add(appartenir)
    db.session.commit()
    response = client.get('/api/appartenir/1/groupes')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['groupe_id'] == 1

def test_modify_appartenir(client: FlaskClient):
    # Test pour modifier un enregistrement
    appartenir = Appartenir(citoyenID=1, groupeID=1)
    db.session.add(appartenir)
    db.session.commit()
    test_data = {
        'citoyen_id': 2,
        'groupe_id': 2
    }
    response = client.put(f'/api/appartenir/update/{appartenir.IDappartenir}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_appartenir = Appartenir.query.get(response_json['id'])
    assert updated_appartenir.citoyenID == test_data['citoyen_id']
    assert updated_appartenir.groupeID == test_data['groupe_id']

def test_modify_appartenir_not_found(client: FlaskClient):
    # Test pour modifier un enregistrement inexistant
    test_data = {
        'citoyen_id': 2,
        'groupe_id': 2
    }
    response = client.put('/api/appartenir/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_appartenir(client: FlaskClient):
    # Test pour supprimer un enregistrement
    appartenir = Appartenir(citoyenID=1, groupeID=1)
    db.session.add(appartenir)
    db.session.commit()
    response = client.delete(f'/api/appartenir/delete/{appartenir.IDappartenir}')
    assert response.status_code == 204
    deleted_appartenir = Appartenir.query.get(appartenir.IDappartenir)
    assert deleted_appartenir is None

def test_remove_appartenir_not_found(client: FlaskClient):
    # Test pour supprimer un enregistrement inexistant
    response = client.delete('/api/appartenir/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
