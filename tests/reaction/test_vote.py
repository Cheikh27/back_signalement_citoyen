import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Vote

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


def test_add_vote(client: FlaskClient):
    # Test pour ajouter un nouveau vote
    test_data = {
        'citoyen_id': 1,
        'signalement_id': 1
    }
    response = client.post('/api/vote/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    vote = Vote.query.get(response_json['id'])
    assert vote is not None
    assert vote.citoyenID == test_data['citoyen_id']
    assert vote.signalementID == test_data['signalement_id']

def test_add_vote_incomplete_data(client: FlaskClient):
    # Test pour ajouter un vote avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/vote/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_vote(client: FlaskClient):
    # Test pour récupérer un vote par ID
    vote = Vote(citoyenID=1, signalementID=1)
    db.session.add(vote)
    db.session.commit()
    response = client.get(f'/api/vote/{vote.IDvote}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == vote.IDvote

def test_get_vote_not_found(client: FlaskClient):
    # Test pour récupérer un vote inexistant
    response = client.get('/api/vote/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_votes(client: FlaskClient):
    # Test pour lister tous les votes
    vote1 = Vote(citoyenID=1, signalementID=1)
    vote2 = Vote(citoyenID=2, signalementID=2)
    db.session.add(vote1)
    db.session.add(vote2)
    db.session.commit()
    response = client.get('/api/vote/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_votes_by_citoyen(client: FlaskClient):
    # Test pour lister les votes par citoyen
    vote = Vote(citoyenID=1, signalementID=1)
    db.session.add(vote)
    db.session.commit()
    response = client.get('/api/vote/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_votes_by_signalement(client: FlaskClient):
    # Test pour lister les votes par signalement
    vote = Vote(citoyenID=1, signalementID=1)
    db.session.add(vote)
    db.session.commit()
    response = client.get('/api/vote/1/signalements')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['signalement_id'] == 1

def test_remove_vote(client: FlaskClient):
    # Test pour supprimer un vote
    vote = Vote(citoyenID=1, signalementID=1)
    db.session.add(vote)
    db.session.commit()
    response = client.delete(f'/api/vote/delete/{vote.IDvote}')
    assert response.status_code == 204
    deleted_vote = Vote.query.get(vote.IDvote)
    assert deleted_vote is None

def test_remove_vote_not_found(client: FlaskClient):
    # Test pour supprimer un vote inexistant
    response = client.delete('/api/vote/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
