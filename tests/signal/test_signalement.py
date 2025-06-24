import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import create_app, db
from app.models import Signalement

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


def test_add_signalement(client: FlaskClient):
    # Test pour ajouter un nouveau signalement
    test_data = {
        'description': 'Description détaillée du signalement',
        'elements': 'Éléments de preuve ou contexte',
        'cible': 'Autorité ou entité ciblée',
        'citoyen_id': 1,
        'nb_vote_positif': 0,
        'nb_vote_negatif': 0
    }
    response = client.post('/api/signalement/add', json=test_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'id' in response_json
    signalement = Signalement.query.get(response_json['id'])
    assert signalement is not None
    assert signalement.description == test_data['description']
    assert signalement.elements == test_data['elements']
    assert signalement.cible == test_data['cible']
    assert signalement.citoyenID == test_data['citoyen_id']
    assert signalement.nbVotePositif == test_data['nb_vote_positif']
    assert signalement.nbVoteNegatif == test_data['nb_vote_negatif']

def test_add_signalement_incomplete_data(client: FlaskClient):
    # Test pour ajouter un signalement avec des données incomplètes
    test_data = {
        'description': 'Description détaillée du signalement'
    }
    response = client.post('/api/signalement/add', json=test_data)
    assert response.status_code == 400
    response_json = response.get_json()
    assert response_json['message'] == 'Bad Request'

def test_get_signalement(client: FlaskClient):
    # Test pour récupérer un signalement par ID
    signalement = Signalement(
        description='Description détaillée du signalement',
        elements='Éléments de preuve ou contexte',
        cible='Autorité ou entité ciblée',
        citoyenID=1,
        nbVotePositif=0,
        nbVoteNegatif=0
    )
    db.session.add(signalement)
    db.session.commit()
    response = client.get(f'/api/signalement/{signalement.IDsignalement}')
    assert response.status_code == 200
    response_json = response.get_json()
    assert response_json['id'] == signalement.IDsignalement

def test_get_signalement_not_found(client: FlaskClient):
    # Test pour récupérer un signalement inexistant
    response = client.get('/api/signalement/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_list_signalements(client: FlaskClient):
    # Test pour lister tous les signalements
    signalement1 = Signalement(
        description='Signalement 1',
        elements='Éléments 1',
        cible='Cible 1',
        citoyenID=1,
        nbVotePositif=0,
        nbVoteNegatif=0
    )
    signalement2 = Signalement(
        description='Signalement 2',
        elements='Éléments 2',
        cible='Cible 2',
        citoyenID=2,
        nbVotePositif=0,
        nbVoteNegatif=0
    )
    db.session.add(signalement1)
    db.session.add(signalement2)
    db.session.commit()
    response = client.get('/api/signalement/all')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 2

def test_list_signalements_by_citoyen(client: FlaskClient):
    # Test pour lister les signalements par citoyen
    signalement = Signalement(
        description='Description détaillée du signalement',
        elements='Éléments de preuve ou contexte',
        cible='Autorité ou entité ciblée',
        citoyenID=1,
        nbVotePositif=0,
        nbVoteNegatif=0
    )
    db.session.add(signalement)
    db.session.commit()
    response = client.get('/api/signalement/1/citoyens')
    assert response.status_code == 200
    response_json = response.get_json()
    assert len(response_json) == 1
    assert response_json[0]['citoyen_id'] == 1

def test_modify_signalement(client: FlaskClient):
    # Test pour modifier un signalement
    signalement = Signalement(
        description='Description détaillée du signalement',
        elements='Éléments de preuve ou contexte',
        cible='Autorité ou entité ciblée',
        citoyenID=1,
        nbVotePositif=0,
        nbVoteNegatif=0
    )
    db.session.add(signalement)
    db.session.commit()
    test_data = {
        'description': 'Nouvelle description du signalement',
        'elements': 'Nouveaux éléments',
        'nb_vote_positif': 5,
        'nb_vote_negatif': 2
    }
    response = client.put(f'/api/signalement/update/{signalement.IDsignalement}', json=test_data)
    assert response.status_code == 200
    response_json = response.get_json()
    assert 'id' in response_json
    updated_signalement = Signalement.query.get(response_json['id'])
    assert updated_signalement.description == test_data['description']
    assert updated_signalement.elements == test_data['elements']
    assert updated_signalement.nbVotePositif == test_data['nb_vote_positif']
    assert updated_signalement.nbVoteNegatif == test_data['nb_vote_negatif']

def test_modify_signalement_not_found(client: FlaskClient):
    # Test pour modifier un signalement inexistant
    test_data = {
        'description': 'Nouvelle description du signalement',
        'elements': 'Nouveaux éléments'
    }
    response = client.put('/api/signalement/update/999', json=test_data)
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'

def test_remove_signalement(client: FlaskClient):
    # Test pour supprimer un signalement
    signalement = Signalement(
        description='Description détaillée du signalement',
        elements='Éléments de preuve ou contexte',
        cible='Autorité ou entité ciblée',
        citoyenID=1,
        nbVotePositif=0,
        nbVoteNegatif=0
    )
    db.session.add(signalement)
    db.session.commit()
    response = client.delete(f'/api/signalement/delete/{signalement.IDsignalement}')
    assert response.status_code == 204
    deleted_signalement = Signalement.query.get(signalement.IDsignalement)
    assert deleted_signalement is None

def test_remove_signalement_not_found(client: FlaskClient):
    # Test pour supprimer un signalement inexistant
    response = client.delete('/api/signalement/delete/999')
    assert response.status_code == 404
    response_json = response.get_json()
    assert response_json['message'] == 'Not found'
