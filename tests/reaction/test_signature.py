import pytest # type: ignore
from app import create_app, db
from app.models.reaction.signature_model import Signature
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
def sample_signature():
    signature = Signature(
        citoyenID=1,
        petitionID=1,
        nbSignature=1,
        dateCreated=datetime.utcnow()
    )
    db.session.add(signature)
    db.session.commit()
    return signature

# Test d'ajout d'une signature
def test_add_signature(client):
    response = client.post('/signatures/add', json={
        "citoyen_id": 1,
        "petition_id": 1,
        "nb_signature": 1
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'une signature par ID
def test_get_signature(client, sample_signature):
    response = client.get(f'/signatures/{sample_signature.IDsignature}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["citoyen_id"] == sample_signature.citoyenID

# Test de récupération de toutes les signatures
def test_list_signatures(client, sample_signature):
    response = client.get('/signatures/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des signatures par citoyen
def test_list_signatures_by_citoyen(client, sample_signature):
    response = client.get(f'/signatures/{sample_signature.citoyenID}/citoyens')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des signatures par pétition
def test_list_signatures_by_petition(client, sample_signature):
    response = client.get(f'/signatures/{sample_signature.petitionID}/petitions')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de mise à jour d'une signature
def test_modify_signature(client, sample_signature):
    response = client.put(f'/signatures/update/{sample_signature.IDsignature}', json={
        "nb_signature": 5
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data

# Test de suppression d'une signature
def test_remove_signature(client, sample_signature):
    response = client.delete(f'/signatures/delete/{sample_signature.IDsignature}')
    assert response.status_code == 204
    response = client.get(f'/signatures/{sample_signature.IDsignature}')
    assert response.status_code == 404