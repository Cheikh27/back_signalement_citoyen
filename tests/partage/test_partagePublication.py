import pytest # type: ignore
from app import create_app, db
from app.models.partage.partagePublication_model import PartagerPublication
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
def sample_partager_publication():
    partager = PartagerPublication(
        citoyenID=1,
        publicationID=1,
        nbPartage=0,
        dateCreated=datetime.utcnow()
    )
    db.session.add(partager)
    db.session.commit()
    return partager

# Test d'ajout d'un partage de publication
def test_add_partager_publication(client):
    response = client.post('/partager-publications/add', json={
        "citoyen_id": 1,
        "publication_id": 1,
        "nb_partage": 0
    })
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test de récupération d'un partage de publication par ID
def test_get_partager_publication(client, sample_partager_publication):
    response = client.get(f'/partager-publications/{sample_partager_publication.IDpartager}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["citoyen_id"] == sample_partager_publication.citoyenID

# Test de récupération de tous les partages de publication
def test_list_partager_publications(client, sample_partager_publication):
    response = client.get('/partager-publications/all')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des partages de publication par citoyen
def test_list_partager_publications_by_citoyen(client, sample_partager_publication):
    response = client.get(f'/partager-publications/{sample_partager_publication.citoyenID}/citoyens')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de récupération des partages de publication par publication
def test_list_partager_publications_by_publication(client, sample_partager_publication):
    response = client.get(f'/partager-publications/{sample_partager_publication.publicationID}/publications')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Test de mise à jour d'un partage de publication
def test_modify_partager_publication(client, sample_partager_publication):
    response = client.put(f'/partager-publications/update/{sample_partager_publication.IDpartager}', json={
        "nb_partage": 5
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data

# Test de suppression d'un partage de publication
def test_remove_partager_publication(client, sample_partager_publication):
    response = client.delete(f'/partager-publications/delete/{sample_partager_publication.IDpartager}')
    assert response.status_code == 204
    response = client.get(f'/partager-publications/{sample_partager_publication.IDpartager}')
    assert response.status_code == 404