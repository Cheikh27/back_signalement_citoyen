import pytest # type: ignore
from app import create_app, db
from app.models.signal.petition_model import Petition
from flask import json

test_petition_data = {
    "description": "Test petition description",
    "nb_signature": 10,
    "nb_partage": 5,
    "date_fin": "2025-12-31",
    "objectif_signature": 100,
    "titre": "Test Petition",
    "cible": "Gouvernement",
    "id_moderateur": 1,
    "citoyen_id": 1
}

@pytest.fixture
def client():
    app = create_app("testing")  # Utiliser la configuration de test
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        
        with app.app_context():
            db.session.remove()
            db.drop_all()

def test_add_petition(client):
    response = client.post("/petitions/add", data=json.dumps(test_petition_data), content_type="application/json")
    assert response.status_code == 201
    json_data = response.get_json()
    assert "id" in json_data

def test_get_petition(client):
    response = client.post("/petitions/add", data=json.dumps(test_petition_data), content_type="application/json")
    petition_id = response.get_json()["id"]
    response = client.get(f"/petitions/{petition_id}")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["titre"] == "Test Petition"

def test_list_petitions(client):
    client.post("/petitions/add", data=json.dumps(test_petition_data), content_type="application/json")
    response = client.get("/petitions/all")
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data) > 0

def test_update_petition(client):
    response = client.post("/petitions/add", data=json.dumps(test_petition_data), content_type="application/json")
    petition_id = response.get_json()["id"]
    update_data = {"description": "Updated description"}
    response = client.put(f"/petitions/update/{petition_id}", data=json.dumps(update_data), content_type="application/json")
    assert response.status_code == 200
    response = client.get(f"/petitions/{petition_id}")
    assert response.get_json()["description"] == "Updated description"

def test_delete_petition(client):
    response = client.post("/petitions/add", data=json.dumps(test_petition_data), content_type="application/json")
    petition_id = response.get_json()["id"]
    response = client.delete(f"/petitions/delete/{petition_id}")
    assert response.status_code == 204
    response = client.get(f"/petitions/{petition_id}")
    assert response.status_code == 404
