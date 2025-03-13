import pytest # type: ignore
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.routes.signal.signalement_route import signalement_bp
from app.services.signal.signalement_service import db, create_signalement

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
    
    app.register_blueprint(signalement_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_signalement(app):
    with app.app_context():
        signalement = create_signalement(
            description="Test Signalement",
            elements="Element Test",
            statut="en_cours",
            nb_vote_positif=5,
            nb_vote_negatif=2,
            cible="Cible Test",
            id_moderateur=1,
            citoyen_id=1
        )
        return signalement

def test_add_signalement(client):
    response = client.post('/signalements/add', json={
        "description": "Test Signalement",
        "elements": "Element Test",
        "statut": "en_cours",
        "nb_vote_positif": 5,
        "nb_vote_negatif": 2,
        "cible": "Cible Test",
        "id_moderateur": 1,
        "citoyen_id": 1
    })
    assert response.status_code == 201
    assert "id" in response.json

def test_get_signalement(client, sample_signalement):
    response = client.get(f'/signalements/{sample_signalement.IDsignalement}')
    assert response.status_code == 200
    assert response.json["description"] == "Test Signalement"

def test_list_signalements(client):
    response = client.get('/signalements/all')
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_update_signalement(client, sample_signalement):
    response = client.put(f'/signalements/update/{sample_signalement.IDsignalement}', json={
        "description": "Updated Description"
    })
    assert response.status_code == 200

def test_delete_signalement(client, sample_signalement):
    response = client.delete(f'/signalements/delete/{sample_signalement.IDsignalement}')
    assert response.status_code == 204
