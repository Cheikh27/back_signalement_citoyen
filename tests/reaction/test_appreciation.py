import pytest # type: ignore
from app import create_app, db
from app.models.reaction.appreciation_model import Appreciation
from datetime import datetime

@pytest.fixture
def client():
    app = create_app("testing")  # Assurez-vous d'avoir une configuration de test
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "CACHE_TYPE": "SimpleCache"
    })
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        
        with app.app_context():
            db.drop_all()

@pytest.fixture
def sample_appreciation():
    appreciation = Appreciation(
        citoyenID=1,
        PublicationID=1,
        dateCreated=datetime.utcnow()
    )
    db.session.add(appreciation)
    db.session.commit()
    return appreciation

# Test d'ajout d'une appréciation
def test_add_appreciation(client):
    response = client.post('/appreciations/add', json={
        "citoyen_id": 1,
        "publication_id": 1
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'une appréciation par ID
def test_get_appreciation(client, sample_appreciation):
    response = client.get(f'/appreciations/{sample_appreciation.IDappreciation}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["citoyen_id"] == sample_appreciation.citoyenID

# Test de récupération de toutes les appréciations
def test_list_appreciations(client, sample_appreciation):
    response = client.get('/appreciations/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des appréciations par citoyen
def test_list_appreciations_by_citoyen(client, sample_appreciation):
    response = client.get(f'/appreciations/{sample_appreciation.citoyenID}/citoyens')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des appréciations par publication
def test_list_appreciations_by_publication(client, sample_appreciation):
    response = client.get(f'/appreciations/{sample_appreciation.PublicationID}/publications')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de suppression d'une appréciation
def test_remove_appreciation(client, sample_appreciation):
    response = client.delete(f'/appreciations/delete/{sample_appreciation.IDappreciation}')
    assert response.status_code == 204
    response = client.get(f'/appreciations/{sample_appreciation.IDappreciation}')
    assert response.status_code == 404