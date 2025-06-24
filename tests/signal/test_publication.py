import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Publication

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


def test_add_publication(client: FlaskClient):
    # Test pour ajouter une nouvelle publication
    test_data = {
        'titre': 'Titre de la publication',
        'description': 'Description détaillée',
        'element': 'Élément associé',
        'nb_aime_positif': 0,
        'nb_aime_negatif': 0,
        'autorite_id': 1,
        'signalement_id': 1
    }
    response = client.post('/api/publication/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    publication = Publication.query.get(response_json['id'])
    assert publication is not None
    assert publication.titre == test_data['titre']
    assert publication.description == test_data['description']
    assert publication.element == test_data['element']
    assert publication.nbAimePositif == test_data['nb_aime_positif']
    assert publication.nbAimeNegatif == test_data['nb_aime_negatif']
    assert publication.autoriteID == test_data['autorite_id']
    assert publication.signalementID == test_data['signalement_id']

def test_add_publication_incomplete_data(client: FlaskClient):
    # Test pour ajouter une publication avec des données incomplètes
    test_data = {
        'titre': 'Titre de la publication',
        'description': 'Description détaillée'
    }
    response = client.post('/api/publication/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_publication(client: FlaskClient):
    # Test pour récupérer une publication par ID
    publication = Publication(
        titre='Titre de la publication',
        description='Description détaillée',
        element='Élément associé',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=1,
        signalementID=1
    )
    db.session.add(publication)
    db.session.commit()
    response = client.get(f'/api/publication/{publication.IDpublication}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == publication.IDpublication

def test_get_publication_not_found(client: FlaskClient):
    # Test pour récupérer une publication inexistante
    response = client.get('/api/publication/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_publications(client: FlaskClient):
    # Test pour lister toutes les publications
    publication1 = Publication(
        titre='Publication 1',
        description='Description 1',
        element='Élément 1',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=1,
        signalementID=1
    )
    publication2 = Publication(
        titre='Publication 2',
        description='Description 2',
        element='Élément 2',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=2,
        signalementID=2
    )
    db.session.add(publication1)
    db.session.add(publication2)
    db.session.commit()
    response = client.get('/api/publication/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_publications_by_autorite(client: FlaskClient):
    # Test pour lister les publications par autorité
    publication = Publication(
        titre='Titre de la publication',
        description='Description détaillée',
        element='Élément associé',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=1,
        signalementID=1
    )
    db.session.add(publication)
    db.session.commit()
    response = client.get('/api/publication/1/autorites')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['autorite_id'] == 1

def test_list_publications_by_signalement(client: FlaskClient):
    # Test pour lister les publications par signalement
    publication = Publication(
        titre='Titre de la publication',
        description='Description détaillée',
        element='Élément associé',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=1,
        signalementID=1
    )
    db.session.add(publication)
    db.session.commit()
    response = client.get('/api/publication/1/signalements')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['signalement_id'] == 1

def test_modify_publication(client: FlaskClient):
    # Test pour modifier une publication
    publication = Publication(
        titre='Titre de la publication',
        description='Description détaillée',
        element='Élément associé',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=1,
        signalementID=1
    )
    db.session.add(publication)
    db.session.commit()
    test_data = {
        'titre': 'Nouveau titre',
        'description': 'Nouvelle description',
        'nb_aime_positif': 5,
        'nb_aime_negatif': 2
    }
    response = client.put(f'/api/publication/update/{publication.IDpublication}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_publication = Publication.query.get(response_json['id'])
    assert updated_publication.titre == test_data['titre']
    assert updated_publication.description == test_data['description']
    assert updated_publication.nbAimePositif == test_data['nb_aime_positif']
    assert updated_publication.nbAimeNegatif == test_data['nb_aime_negatif']

def test_modify_publication_not_found(client: FlaskClient):
    # Test pour modifier une publication inexistante
    test_data = {
        'titre': 'Nouveau titre',
        'description': 'Nouvelle description'
    }
    response = client.put('/api/publication/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_publication(client: FlaskClient):
    # Test pour supprimer une publication
    publication = Publication(
        titre='Titre de la publication',
        description='Description détaillée',
        element='Élément associé',
        nbAimePositif=0,
        nbAimeNegatif=0,
        autoriteID=1,
        signalementID=1
    )
    db.session.add(publication)
    db.session.commit()
    response = client.delete(f'/api/publication/delete/{publication.IDpublication}')
    assert response.status_code == 204
    deleted_publication = Publication.query.get(publication.IDpublication)
    assert deleted_publication is None

def test_remove_publication_not_found(client: FlaskClient):
    # Test pour supprimer une publication inexistante
    response = client.delete('/api/publication/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
