import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Petition

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


def test_add_petition(client: FlaskClient):
    # Test pour ajouter une nouvelle pétition
    test_data = {
        'description': 'Pétition pour améliorer les infrastructures',
        'titre': 'Amélioration des routes',
        'cible': 'Gouvernement',
        'citoyen_id': 1,
        'nb_signature': 0,
        'nb_partage': 0,
        'date_fin': '2024-12-31',
        'objectif_signature': 1000
    }
    response = client.post('/api/petition/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    petition = Petition.query.get(response_json['id'])
    assert petition is not None
    assert petition.description == test_data['description']
    assert petition.titre == test_data['titre']
    assert petition.cible == test_data['cible']
    assert petition.citoyenID == test_data['citoyen_id']
    assert petition.nbSignature == test_data['nb_signature']
    assert petition.nbPartage == test_data['nb_partage']
    assert petition.dateFin == test_data['date_fin']
    assert petition.objectifSignature == test_data['objectif_signature']

def test_add_petition_incomplete_data(client: FlaskClient):
    # Test pour ajouter une pétition avec des données incomplètes
    test_data = {
        'description': 'Pétition pour améliorer les infrastructures',
        'titre': 'Amélioration des routes'
    }
    response = client.post('/api/petition/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_petition(client: FlaskClient):
    # Test pour récupérer une pétition par ID
    petition = Petition(
        description='Pétition pour améliorer les infrastructures',
        titre='Amélioration des routes',
        cible='Gouvernement',
        citoyenID=1,
        nbSignature=0,
        nbPartage=0,
        dateFin='2024-12-31',
        objectifSignature=1000
    )
    db.session.add(petition)
    db.session.commit()
    response = client.get(f'/api/petition/{petition.IDpetition}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == petition.IDpetition

def test_get_petition_not_found(client: FlaskClient):
    # Test pour récupérer une pétition inexistante
    response = client.get('/api/petition/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_petitions(client: FlaskClient):
    # Test pour lister toutes les pétitions
    petition1 = Petition(
        description='Pétition 1',
        titre='Titre 1',
        cible='Gouvernement',
        citoyenID=1,
        nbSignature=0,
        nbPartage=0,
        dateFin='2024-12-31',
        objectifSignature=1000
    )
    petition2 = Petition(
        description='Pétition 2',
        titre='Titre 2',
        cible='Gouvernement',
        citoyenID=2,
        nbSignature=0,
        nbPartage=0,
        dateFin='2024-12-31',
        objectifSignature=1000
    )
    db.session.add(petition1)
    db.session.add(petition2)
    db.session.commit()
    response = client.get('/api/petition/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_petitions_by_citoyen(client: FlaskClient):
    # Test pour lister les pétitions par citoyen
    petition = Petition(
        description='Pétition pour améliorer les infrastructures',
        titre='Amélioration des routes',
        cible='Gouvernement',
        citoyenID=1,
        nbSignature=0,
        nbPartage=0,
        dateFin='2024-12-31',
        objectifSignature=1000
    )
    db.session.add(petition)
    db.session.commit()
    response = client.get('/api/petition/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_modify_petition(client: FlaskClient):
    # Test pour modifier une pétition
    petition = Petition(
        description='Pétition pour améliorer les infrastructures',
        titre='Amélioration des routes',
        cible='Gouvernement',
        citoyenID=1,
        nbSignature=0,
        nbPartage=0,
        dateFin='2024-12-31',
        objectifSignature=1000
    )
    db.session.add(petition)
    db.session.commit()
    test_data = {
        'description': 'Nouvelle description de la pétition',
        'nb_signature': 100
    }
    response = client.put(f'/api/petition/update/{petition.IDpetition}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_petition = Petition.query.get(response_json['id'])
    assert updated_petition.description == test_data['description']
    assert updated_petition.nbSignature == test_data['nb_signature']

def test_modify_petition_not_found(client: FlaskClient):
    # Test pour modifier une pétition inexistante
    test_data = {
        'description': 'Nouvelle description de la pétition',
        'nb_signature': 100
    }
    response = client.put('/api/petition/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_petition(client: FlaskClient):
    # Test pour supprimer une pétition
    petition = Petition(
        description='Pétition pour améliorer les infrastructures',
        titre='Amélioration des routes',
        cible='Gouvernement',
        citoyenID=1,
        nbSignature=0,
        nbPartage=0,
        dateFin='2024-12-31',
        objectifSignature=1000
    )
    db.session.add(petition)
    db.session.commit()
    response = client.delete(f'/api/petition/delete/{petition.IDpetition}')
    assert response.status_code == 204
    deleted_petition = Petition.query.get(petition.IDpetition)
    assert deleted_petition is None

def test_remove_petition_not_found(client: FlaskClient):
    # Test pour supprimer une pétition inexistante
    response = client.delete('/api/petition/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
