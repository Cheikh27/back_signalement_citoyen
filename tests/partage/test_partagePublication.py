import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import PartagerPublication

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


def test_add_partager_publication(client: FlaskClient):
    # Test pour ajouter un nouveau partage de publication
    test_data = {
        'citoyen_id': 1,
        'publication_id': 1,
        'nb_partage': 0
    }
    response = client.post('/api/partager_publication/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    partager = PartagerPublication.query.get(response_json['id'])
    assert partager is not None
    assert partager.citoyenID == test_data['citoyen_id']
    assert partager.publicationID == test_data['publication_id']
    assert partager.nbPartage == test_data['nb_partage']

def test_add_partager_publication_incomplete_data(client: FlaskClient):
    # Test pour ajouter un partage de publication avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/partager_publication/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_partager_publication(client: FlaskClient):
    # Test pour récupérer un partage de publication par ID
    partager = PartagerPublication(citoyenID=1, publicationID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get(f'/api/partager_publication/{partager.IDpartager}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == partager.IDpartager

def test_get_partager_publication_not_found(client: FlaskClient):
    # Test pour récupérer un partage de publication inexistant
    response = client.get('/api/partager_publication/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_partager_publications(client: FlaskClient):
    # Test pour lister tous les partages de publication
    partager1 = PartagerPublication(citoyenID=1, publicationID=1, nbPartage=0)
    partager2 = PartagerPublication(citoyenID=2, publicationID=2, nbPartage=0)
    db.session.add(partager1)
    db.session.add(partager2)
    db.session.commit()
    response = client.get('/api/partager_publication/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_partager_publications_by_citoyen(client: FlaskClient):
    # Test pour lister les partages de publication par citoyen
    partager = PartagerPublication(citoyenID=1, publicationID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get('/api/partager_publication/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_partager_publications_by_publication(client: FlaskClient):
    # Test pour lister les partages de publication par publication
    partager = PartagerPublication(citoyenID=1, publicationID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.get('/api/partager_publication/1/publications')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['publication_id'] == 1

def test_modify_partager_publication(client: FlaskClient):
    # Test pour modifier un partage de publication
    partager = PartagerPublication(citoyenID=1, publicationID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    test_data = {
        'nb_partage': 1
    }
    response = client.put(f'/api/partager_publication/update/{partager.IDpartager}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_partager = PartagerPublication.query.get(response_json['id'])
    assert updated_partager.nbPartage == test_data['nb_partage']

def test_modify_partager_publication_not_found(client: FlaskClient):
    # Test pour modifier un partage de publication inexistant
    test_data = {
        'nb_partage': 1
    }
    response = client.put('/api/partager_publication/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_partager_publication(client: FlaskClient):
    # Test pour supprimer un partage de publication
    partager = PartagerPublication(citoyenID=1, publicationID=1, nbPartage=0)
    db.session.add(partager)
    db.session.commit()
    response = client.delete(f'/api/partager_publication/delete/{partager.IDpartager}')
    assert response.status_code == 204
    deleted_partager = PartagerPublication.query.get(partager.IDpartager)
    assert deleted_partager is None

def test_remove_partager_publication_not_found(client: FlaskClient):
    # Test pour supprimer un partage de publication inexistant
    response = client.delete('/api/partager_publication/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
