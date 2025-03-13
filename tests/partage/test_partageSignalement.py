import pytest # type: ignore
from app import create_app, db
from app.models.partage.partageSignalement_model import PartagerSignalement
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
def sample_partager_signalement():
    partager = PartagerSignalement(
        citoyenID=1,
        SignalementID=1,
        nbPartage=0,
        dateCreated=datetime.utcnow()
    )
    db.session.add(partager)
    db.session.commit()
    return partager

# Test d'ajout d'un partage de signalement
def test_add_partager_signalement(client):
    response = client.post('/partager-signalements/add', json={
        "citoyen_id": 1,
        "signalement_id": 1,
        "nb_partage": 0
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'un partage de signalement par ID
def test_get_partager_signalement(client, sample_partager_signalement):
    response = client.get(f'/partager-signalements/{sample_partager_signalement.IDpartager}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["citoyen_id"] == sample_partager_signalement.citoyenID

# Test de récupération de tous les partages de signalement
def test_list_partager_signalements(client, sample_partager_signalement):
    response = client.get('/partager-signalements/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des partages de signalement par citoyen
def test_list_partager_signalements_by_citoyen(client, sample_partager_signalement):
    response = client.get(f'/partager-signalements/{sample_partager_signalement.citoyenID}/citoyens')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des partages de signalement par signalement
def test_list_partager_signalements_by_signalement(client, sample_partager_signalement):
    response = client.get(f'/partager-signalements/{sample_partager_signalement.SignalementID}/signalements')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de mise à jour d'un partage de signalement
def test_modify_partager_signalement(client, sample_partager_signalement):
    response = client.put(f'/partager-signalements/update/{sample_partager_signalement.IDpartager}', json={
        "nb_partage": 5
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data

# Test de suppression d'un partage de signalement
def test_remove_partager_signalement(client, sample_partager_signalement):
    response = client.delete(f'/partager-signalements/delete/{sample_partager_signalement.IDpartager}')
    assert response.status_code == 204
    response = client.get(f'/partager-signalements/{sample_partager_signalement.IDpartager}')
    assert response.status_code == 404