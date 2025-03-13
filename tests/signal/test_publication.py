import pytest # type: ignore
from app import create_app, db
from app.models.signal.publication_model import Publication

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_create_publication(client):
    response = client.post('/publications/add', json={
        "titre": "Test Titre",
        "description": "Test Description",
        "element": "Test Element",
        "nb_aime_positif": 10,
        "nb_aime_negatif": 2,
        "autorite_id": 1,
        "signalement_id": 1
    })
    assert response.status_code == 201
    assert 'id' in response.get_json()

def test_get_publication(client):
    # Ajouter une publication d'abord
    response = client.post('/publications/add', json={
        "titre": "Titre1",
        "description": "Description1",
        "element": "Element1",
        "nb_aime_positif": 5,
        "nb_aime_negatif": 1,
        "autorite_id": 1,
        "signalement_id": 1
    })
    publication_id = response.get_json()['id']
    
    # Tester la récupération
    response = client.get(f'/publications/{publication_id}')
    assert response.status_code == 200
    assert response.get_json()['titre'] == "Titre1"

def test_get_all_publications(client):
    client.post('/publications/add', json={
        "titre": "Titre1",
        "description": "Description1",
        "element": "Element1",
        "nb_aime_positif": 5,
        "nb_aime_negatif": 1,
        "autorite_id": 1,
        "signalement_id": 1
    })
    client.post('/publications/add', json={
        "titre": "Titre2",
        "description": "Description2",
        "element": "Element2",
        "nb_aime_positif": 3,
        "nb_aime_negatif": 2,
        "autorite_id": 1,
        "signalement_id": 1
    })
    
    response = client.get('/publications/all')
    assert response.status_code == 200
    assert len(response.get_json()) >= 2

def test_update_publication(client):
    response = client.post('/publications/add', json={
        "titre": "Titre1",
        "description": "Description1",
        "element": "Element1",
        "nb_aime_positif": 5,
        "nb_aime_negatif": 1,
        "autorite_id": 1,
        "signalement_id": 1
    })
    publication_id = response.get_json()['id']
    
    response = client.put(f'/publications/update/{publication_id}', json={
        "titre": "Titre Modifié"
    })
    assert response.status_code == 200
    
    response = client.get(f'/publications/{publication_id}')
    assert response.get_json()['titre'] == "Titre Modifié"

def test_delete_publication(client):
    response = client.post('/publications/add', json={
        "titre": "Titre1",
        "description": "Description1",
        "element": "Element1",
        "nb_aime_positif": 5,
        "nb_aime_negatif": 1,
        "autorite_id": 1,
        "signalement_id": 1
    })
    publication_id = response.get_json()['id']
    
    response = client.delete(f'/publications/delete/{publication_id}')
    assert response.status_code == 204
    
    response = client.get(f'/publications/{publication_id}')
    assert response.status_code == 404
