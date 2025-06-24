import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Signature

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


def test_add_signature(client: FlaskClient):
    # Test pour ajouter une nouvelle signature
    test_data = {
        'citoyen_id': 1,
        'petition_id': 1,
        'nb_signature': 1
    }
    response = client.post('/api/signature/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    signature = Signature.query.get(response_json['id'])
    assert signature is not None
    assert signature.citoyenID == test_data['citoyen_id']
    assert signature.petitionID == test_data['petition_id']
    assert signature.nbSignature == test_data['nb_signature']

def test_add_signature_incomplete_data(client: FlaskClient):
    # Test pour ajouter une signature avec des données incomplètes
    test_data = {
        'citoyen_id': 1
    }
    response = client.post('/api/signature/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_signature(client: FlaskClient):
    # Test pour récupérer une signature par ID
    signature = Signature(citoyenID=1, petitionID=1, nbSignature=1)
    db.session.add(signature)
    db.session.commit()
    response = client.get(f'/api/signature/{signature.IDsignature}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == signature.IDsignature

def test_get_signature_not_found(client: FlaskClient):
    # Test pour récupérer une signature inexistante
    response = client.get('/api/signature/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_signatures(client: FlaskClient):
    # Test pour lister toutes les signatures
    signature1 = Signature(citoyenID=1, petitionID=1, nbSignature=1)
    signature2 = Signature(citoyenID=2, petitionID=2, nbSignature=1)
    db.session.add(signature1)
    db.session.add(signature2)
    db.session.commit()
    response = client.get('/api/signature/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_signatures_by_citoyen(client: FlaskClient):
    # Test pour lister les signatures par citoyen
    signature = Signature(citoyenID=1, petitionID=1, nbSignature=1)
    db.session.add(signature)
    db.session.commit()
    response = client.get('/api/signature/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_list_signatures_by_petition(client: FlaskClient):
    # Test pour lister les signatures par pétition
    signature = Signature(citoyenID=1, petitionID=1, nbSignature=1)
    db.session.add(signature)
    db.session.commit()
    response = client.get('/api/signature/1/petitions')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['petition_id'] == 1

def test_modify_signature(client: FlaskClient):
    # Test pour modifier une signature
    signature = Signature(citoyenID=1, petitionID=1, nbSignature=1)
    db.session.add(signature)
    db.session.commit()
    test_data = {
        'nb_signature': 2
    }
    response = client.put(f'/api/signature/update/{signature.IDsignature}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_signature = Signature.query.get(response_json['id'])
    assert updated_signature.nbSignature == test_data['nb_signature']

def test_modify_signature_not_found(client: FlaskClient):
    # Test pour modifier une signature inexistante
    test_data = {
        'nb_signature': 2
    }
    response = client.put('/api/signature/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_signature(client: FlaskClient):
    # Test pour supprimer une signature
    signature = Signature(citoyenID=1, petitionID=1, nbSignature=1)
    db.session.add(signature)
    db.session.commit()
    response = client.delete(f'/api/signature/delete/{signature.IDsignature}')
    assert response.status_code == 204
    deleted_signature = Signature.query.get(signature.IDsignature)
    assert deleted_signature is None

def test_remove_signature_not_found(client: FlaskClient):
    # Test pour supprimer une signature inexistante
    response = client.delete('/api/signature/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
