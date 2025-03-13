import pytest # type: ignore
from app import create_app, db
from app.models.commentaire.commentaireSignalement_model import CommentaireSignalement
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
def sample_commentaire():
    commentaire = CommentaireSignalement(
        description="Test comment",
        citoyenID=1,
        signalementID=1,
        dateCreated=datetime.utcnow()
    )
    db.session.add(commentaire)
    db.session.commit()
    return commentaire

# Test d'ajout d'un commentaire
def test_add_commentaire_signalement(client):
    response = client.post('/commentaires-signalement/add', json={
        "description": "Nouveau commentaire",
        "citoyen_id": 1,
        "signalement_id": 1
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'un commentaire par ID
def test_get_commentaire_signalement(client, sample_commentaire):
    response = client.get(f'/commentaires-signalement/{sample_commentaire.IDcommentaire}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["description"] == sample_commentaire.description

# Test de récupération de tous les commentaires
def test_list_commentaires_signalement(client, sample_commentaire):
    response = client.get('/commentaires-signalement/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de mise à jour d'un commentaire
def test_modify_commentaire_signalement(client, sample_commentaire):
    response = client.put(f'/commentaires-signalement/update/{sample_commentaire.IDcommentaire}', json={
        "description": "Commentaire modifié"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data

# Test de suppression d'un commentaire
def test_remove_commentaire_signalement(client, sample_commentaire):
    response = client.delete(f'/commentaires-signalement/delete/{sample_commentaire.IDcommentaire}')
    assert response.status_code == 204
    response = client.get(f'/commentaires-signalement/{sample_commentaire.IDcommentaire}')
    assert response.status_code == 404
