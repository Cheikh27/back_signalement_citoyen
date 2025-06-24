import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import PartagerPetition

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


def test_add_partager_petition(client: FlaskClient):
    # Test pour ajouter un nouveau partage de pétition
    test_data = {
        'citoyen_id': 1,
        'petition_id': 1,
        'nb_partage': 0
    }
    response = client.post('/api/partager_petition/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    partager = PartagerPetition.query.get(response_json['id'])
    assert partager is not None
    assert partager.citoyenID == test_data['citoyen_id']
    assert partager.petitionID == test_data['petition_id']
    assert partager.nbPartage == test_data['nb_partage']

def test_add_partager_petition_incomplete_data(client: FlaskClient):
    # Test pour ajouter un partage de pétition avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/partager_petition/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_partager_petition(client: FlaskClient):
    # Test pour récupérer un partage de pétition par ID
    partager = PartagerPetition(citoyenID=1, petitionID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get(f'/api/partager_petition/{partager.IDpartager}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == partager.IDpartager

def test_get_partager_petition_not_found(client: FlaskClient):
    # Test pour récupérer un partage de pétition inexistant
    response = client.get('/api/partager_petition/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_partager_petitions(client: FlaskClient):
    # Test pour lister tous les partages de pétition
    partager1 = PartagerPetition(citoyenID=1, petitionID=1, nbPartage=0)
    partager2 = PartagerPetition(citoyenID=2, petitionID=2, nbPartage=0)
    db.session.add(partager1)
    db.session.add(partager2)
    db.session.commit()
    response = client.get('/api/partager_petition/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_partager_petitions_by_citoyen(client: FlaskClient):
    # Test pour lister les partages de pétition par citoyen
    partager = PartagerPetition(citoyenID=1, petitionID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get('/api/partager_petition/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_partager_petitions_by_petition(client: FlaskClient):
    # Test pour lister les partages de pétition par pétition
    partager = PartagerPetition(citoyenID=1, petitionID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get('/api/partager_petition/1/petitions')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['petition_id'] == 1

def test_modify_partager_petition(client: FlaskClient):
    # Test pour modifier un partage de pétition
    partager = PartagerPetition(citoyenID=1, petitionID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    test_data = {
        'nb_partage': 1
    }
    response = client.put(f'/api/partager_petition/update/{partager.IDpartager}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_partager = PartagerPetition.query.get(response_json['id'])
    assert updated_partager.nbPartage == test_data['nb_partage']

def test_modify_partager_petition_not_found(client: FlaskClient):
    # Test pour modifier un partage de pétition inexistant
    test_data = {
        'nb_partage': 1
    }
    response = client.put('/api/partager_petition/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_partager_petition(client: FlaskClient):
    # Test pour supprimer un partage de pétition
    partager = PartagerPetition(citoyenID=1, petitionID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.delete(f'/api/partager_petition/delete/{partager.IDpartager}')
    assert response.status_code == 204
    deleted_partager = PartagerPetition.query.get(partager.IDpartager)
    assert deleted_partager is None

def test_remove_partager_petition_not_found(client: FlaskClient):
    # Test pour supprimer un partage de pétition inexistant
    response = client.delete('/api/partager_petition/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
