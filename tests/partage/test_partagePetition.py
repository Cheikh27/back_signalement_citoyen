import pytest # type: ignore
from app import create_app, db
from app.models.partage.partagePetition_model import PartagerPetition
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
def sample_partager_petition():
    partager = PartagerPetition(
        citoyenID=1,
        petitionID=1,
        nbPartage=0,
        dateCreated=datetime.utcnow()
    )
    db.session.add(partager)
    db.session.commit()
    return partager

# Test d'ajout d'un partage de pétition
def test_add_partager_petition(client):
    response = client.post('/partager-petitions/add', json={
        "citoyen_id": 1,
        "petition_id": 1,
        "nb_partage": 0
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'un partage de pétition par ID
def test_get_partager_petition(client, sample_partager_petition):
    response = client.get(f'/partager-petitions/{sample_partager_petition.IDpartager}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["citoyen_id"] == sample_partager_petition.citoyenID

# Test de récupération de tous les partages de pétition
def test_list_partager_petitions(client, sample_partager_petition):
    response = client.get('/partager-petitions/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des partages de pétition par citoyen
def test_list_partager_petitions_by_citoyen(client, sample_partager_petition):
    response = client.get(f'/partager-petitions/{sample_partager_petition.citoyenID}/citoyens')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des partages de pétition par pétition
def test_list_partager_petitions_by_petition(client, sample_partager_petition):
    response = client.get(f'/partager-petitions/{sample_partager_petition.petitionID}/petitions')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de mise à jour d'un partage de pétition
def test_modify_partager_petition(client, sample_partager_petition):
    response = client.put(f'/partager-petitions/update/{sample_partager_petition.IDpartager}', json={
        "nb_partage": 5
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data

# Test de suppression d'un partage de pétition
def test_remove_partager_petition(client, sample_partager_petition):
    response = client.delete(f'/partager-petitions/delete/{sample_partager_petition.IDpartager}')
    assert response.status_code == 204
    response = client.get(f'/partager-petitions/{sample_partager_petition.IDpartager}')
    assert response.status_code == 404