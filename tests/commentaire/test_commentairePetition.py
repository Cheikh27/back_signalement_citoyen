import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import CommentairePetition

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


def test_add_commentaire(client: FlaskClient):
    # Test pour ajouter un nouveau commentaire
    test_data = {
        'description': 'Ceci est un commentaire.',
        'citoyen_id': 1,
        'petition_id': 1
    }
    response = client.post('/api/commentaire/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    commentaire = CommentairePetition.query.get(response_json['id'])
    assert commentaire is not None
    assert commentaire.description == test_data['description']
    assert commentaire.citoyenID == test_data['citoyen_id']
    assert commentaire.petitionID == test_data['petition_id']

def test_add_commentaire_incomplete_data(client: FlaskClient):
    # Test pour ajouter un commentaire avec des données incomplètes
    test_data = {
        'description': 'Ceci est un commentaire.',
        'citoyen_id': 1
    }
    response = client.post('/api/commentaire/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_commentaire(client: FlaskClient):
    # Test pour récupérer un commentaire par ID
    commentaire = CommentairePetition(description='Commentaire Test', citoyenID=1, petitionID=1)
    db.session.add(commentaire)
    db.session.commit()
    response = client.get(f'/api/commentaire/{commentaire.IDcommentaire}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == commentaire.IDcommentaire

def test_get_commentaire_not_found(client: FlaskClient):
    # Test pour récupérer un commentaire inexistant
    response = client.get('/api/commentaire/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_commentaires(client: FlaskClient):
    # Test pour lister tous les commentaires
    commentaire1 = CommentairePetition(description='Commentaire 1', citoyenID=1, petitionID=1)
    commentaire2 = CommentairePetition(description='Commentaire 2', citoyenID=2, petitionID=2)
    db.session.add(commentaire1)
    db.session.add(commentaire2)
    db.session.commit()
    response = client.get('/api/commentaire/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_commentaires_by_citoyen(client: FlaskClient):
    # Test pour lister les commentaires par citoyen
    commentaire = CommentairePetition(description='Commentaire Test', citoyenID=1, petitionID=1)
    db.session.add(commentaire)
    db.session.commit()
    response = client.get('/api/commentaire/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_commentaires_by_petition(client: FlaskClient):
    # Test pour lister les commentaires par pétition
    commentaire = CommentairePetition(description='Commentaire Test', citoyenID=1, petitionID=1)
    db.session.add(commentaire)
    db.session.commit()
    response = client.get('/api/commentaire/1/petitions')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['petition_id'] == 1

def test_modify_commentaire(client: FlaskClient):
    # Test pour modifier un commentaire
    commentaire = CommentairePetition(description='Commentaire Test', citoyenID=1, petitionID=1)
    db.session.add(commentaire)
    db.session.commit()
    test_data = {
        'description': 'Nouveau contenu du commentaire.'
    }
    response = client.put(f'/api/commentaire/update/{commentaire.IDcommentaire}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_commentaire = CommentairePetition.query.get(response_json['id'])
    assert updated_commentaire.description == test_data['description']

def test_modify_commentaire_not_found(client: FlaskClient):
    # Test pour modifier un commentaire inexistant
    test_data = {
        'description': 'Nouveau contenu du commentaire.'
    }
    response = client.put('/api/commentaire/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_commentaire(client: FlaskClient):
    # Test pour supprimer un commentaire
    commentaire = CommentairePetition(description='Commentaire Test', citoyenID=1, petitionID=1)
    db.session.add(commentaire)
    db.session.commit()
    response = client.delete(f'/api/commentaire/delete/{commentaire.IDcommentaire}')
    assert response.status_code == 204
    deleted_commentaire = CommentairePetition.query.get(commentaire.IDcommentaire)
    assert deleted_commentaire is None

def test_remove_commentaire_not_found(client: FlaskClient):
    # Test pour supprimer un commentaire inexistant
    response = client.delete('/api/commentaire/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
