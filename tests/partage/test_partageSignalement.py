import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import PartagerSignalement

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


def test_add_partager_signalement(client: FlaskClient):
    # Test pour ajouter un nouveau partage de signalement
    test_data = {
        'citoyen_id': 1,
        'signalement_id': 1,
        'nb_partage': 0
    }
    response = client.post('/api/partager_signalement/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    partager = PartagerSignalement.query.get(response_json['id'])
    assert partager is not None
    assert partager.citoyenID == test_data['citoyen_id']
    assert partager.SignalementID == test_data['signalement_id']
    assert partager.nbPartage == test_data['nb_partage']

def test_add_partager_signalement_incomplete_data(client: FlaskClient):
    # Test pour ajouter un partage de signalement avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/partager_signalement/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_partager_signalement(client: FlaskClient):
    # Test pour récupérer un partage de signalement par ID
    partager = PartagerSignalement(citoyenID=1, SignalementID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get(f'/api/partager_signalement/{partager.IDpartager}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == partager.IDpartager

def test_get_partager_signalement_not_found(client: FlaskClient):
    # Test pour récupérer un partage de signalement inexistant
    response = client.get('/api/partager_signalement/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_partager_signalements(client: FlaskClient):
    # Test pour lister tous les partages de signalement
    partager1 = PartagerSignalement(citoyenID=1, SignalementID=1, nbPartage=0)
    partager2 = PartagerSignalement(citoyenID=2, SignalementID=2, nbPartage=0)
    db.session.add(partager1)
    db.session.add(partager2)
    db.session.commit()
    response = client.get('/api/partager_signalement/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_partager_signalements_by_citoyen(client: FlaskClient):
    # Test pour lister les partages de signalement par citoyen
    partager = PartagerSignalement(citoyenID=1, SignalementID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get('/api/partager_signalement/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_partager_signalements_by_signalement(client: FlaskClient):
    # Test pour lister les partages de signalement par signalement
    partager = PartagerSignalement(citoyenID=1, SignalementID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get('/api/partager_signalement/1/signalements')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['signalement_id'] == 1

def test_modify_partager_signalement(client: FlaskClient):
    # Test pour modifier un partage de signalement
    partager = PartagerSignalement(citoyenID=1, SignalementID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    test_data = {
        'nb_partage': 1
    }
    response = client.put(f'/api/partager_signalement/update/{partager.IDpartager}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_partager = PartagerSignalement.query.get(response_json['id'])
    assert updated_partager.nbPartage == test_data['nb_partage']

def test_modify_partager_signalement_not_found(client: FlaskClient):
    # Test pour modifier un partage de signalement inexistant
    test_data = {
        'nb_partage': 1
    }
    response = client.put('/api/partager_signalement/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_partager_signalement(client: FlaskClient):
    # Test pour supprimer un partage de signalement
    partager = PartagerSignalement(citoyenID=1, SignalementID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.delete(f'/api/partager_signalement/delete/{partager.IDpartager}')
    assert response.status_code == 204
    deleted_partager = PartagerSignalement.query.get(partager.IDpartager)
    assert deleted_partager is None

def test_remove_partager_signalement_not_found(client: FlaskClient):
    # Test pour supprimer un partage de signalement inexistant
    response = client.delete('/api/partager_signalement/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
