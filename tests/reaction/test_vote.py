import pytest # type: ignore
from app import create_app, db
from app.models.reaction.vote_model import Vote
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
def sample_vote():
    vote = Vote(
        citoyenID=1,
        signalementID=1,
        dateCreated=datetime.utcnow()
    )
    db.session.add(vote)
    db.session.commit()
    return vote

# Test d'ajout d'un vote
def test_add_vote(client):
    response = client.post('/votes/add', json={
        "citoyen_id": 1,
        "signalement_id": 1
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'un vote par ID
def test_get_vote(client, sample_vote):
    response = client.get(f'/votes/{sample_vote.IDvote}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["citoyen_id"] == sample_vote.citoyenID

# Test de récupération de tous les votes
def test_list_votes(client, sample_vote):
    response = client.get('/votes/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des votes par citoyen
def test_list_votes_by_citoyen(client, sample_vote):
    response = client.get(f'/votes/{sample_vote.citoyenID}/citoyens')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des votes par signalement
def test_list_votes_by_signalement(client, sample_vote):
    response = client.get(f'/votes/{sample_vote.signalementID}/signalements')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de suppression d'un vote
def test_remove_vote(client, sample_vote):
    response = client.delete(f'/votes/delete/{sample_vote.IDvote}')
    assert response.status_code == 204
    response = client.get(f'/votes/{sample_vote.IDvote}')
    assert response.status_code == 404