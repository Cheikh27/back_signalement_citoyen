import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Appreciation

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


def test_add_appreciation(client: FlaskClient):
    # Test pour ajouter une nouvelle appréciation
    test_data = {
        'citoyen_id': 1,
        'publication_id': 1
    }
    response = client.post('/api/appreciation/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    appreciation = Appreciation.query.get(response_json['id'])
    assert appreciation is not None
    assert appreciation.citoyenID == test_data['citoyen_id']
    assert appreciation.PublicationID == test_data['publication_id']

def test_add_appreciation_incomplete_data(client: FlaskClient):
    # Test pour ajouter une appréciation avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/appreciation/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_appreciation(client: FlaskClient):
    # Test pour récupérer une appréciation par ID
    appreciation = Appreciation(citoyenID=1, PublicationID=1)
    db.session.add(appreciation)
    db.session.commit()
    response = client.get(f'/api/appreciation/{appreciation.IDappreciation}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == appreciation.IDappreciation

def test_get_appreciation_not_found(client: FlaskClient):
    # Test pour récupérer une appréciation inexistante
    response = client.get('/api/appreciation/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_appreciations(client: FlaskClient):
    # Test pour lister toutes les appréciations
    appreciation1 = Appreciation(citoyenID=1, PublicationID=1)
    appreciation2 = Appreciation(citoyenID=2, PublicationID=2)
    db.session.add(appreciation1)
    db.session.add(appreciation2)
    db.session.commit()
    response = client.get('/api/appreciation/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_appreciations_by_citoyen(client: FlaskClient):
    # Test pour lister les appréciations par citoyen
    appreciation = Appreciation(citoyenID=1, PublicationID=1)
    db.session.add(appreciation)
    db.session.commit()
    response = client.get('/api/appreciation/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_appreciations_by_publication(client: FlaskClient):
    # Test pour lister les appréciations par publication
    appreciation = Appreciation(citoyenID=1, PublicationID=1)
    db.session.add(appreciation)
    db.session.commit()
    response = client.get('/api/appreciation/1/publications')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['publication_id'] == 1

def test_remove_appreciation(client: FlaskClient):
    # Test pour supprimer une appréciation
    appreciation = Appreciation(citoyenID=1, PublicationID=1)
    db.session.add(appreciation)
    db.session.commit()
    response = client.delete(f'/api/appreciation/delete/{appreciation.IDappreciation}')
    assert response.status_code == 204
    deleted_appreciation = Appreciation.query.get(appreciation.IDappreciation)
    assert deleted_appreciation is None

def test_remove_appreciation_not_found(client: FlaskClient):
    # Test pour supprimer une appréciation inexistante
    response = client.delete('/api/appreciation/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
