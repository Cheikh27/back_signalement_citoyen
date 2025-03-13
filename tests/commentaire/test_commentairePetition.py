import pytest # type: ignore
from unittest.mock import patch, MagicMock
from flask import Flask
from app.routes.commentaire.commentairePetition_route import commentaire_bp

def create_test_app():
    app = Flask(__name__)
    app.register_blueprint(commentaire_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client():
    app = create_test_app()
    return app.test_client()

@patch('app.services.commentaire.commentairePetition_service.create_commentaire')
def test_add_commentaire(mock_create_commentaire, client):
    mock_commentaire = MagicMock()
    mock_commentaire.IDcommentaire = 1
    mock_create_commentaire.return_value = mock_commentaire
    
    response = client.post('/commentaires_petition/add', json={
        'description': 'Test Commentaire',
        'citoyen_id': 1,
        'petition_id': 1
    })
    
    assert response.status_code == 201
    assert response.json['id'] == 1

@patch('app.services.commentaire.commentairePetition_service.get_commentaire_by_id')
def test_get_commentaire(mock_get_commentaire_by_id, client):
    mock_commentaire = MagicMock()
    mock_commentaire.IDcommentaire = 1
    mock_commentaire.description = "Test Commentaire"
    mock_commentaire.citoyenID = 1
    mock_commentaire.petitionID = 1
    mock_commentaire.dateCreated = "2024-01-01"
    mock_get_commentaire_by_id.return_value = mock_commentaire
    
    response = client.get('/commentaires_petition/1')
    
    assert response.status_code == 200
    assert response.json['id'] == 1
    assert response.json['description'] == "Test Commentaire"

@patch('app.services.commentaire.commentairePetition_service.get_all_commentaires')
def test_list_commentaires(mock_get_all_commentaires, client):
    mock_commentaire = MagicMock()
    mock_commentaire.IDcommentaire = 1
    mock_commentaire.description = "Test Commentaire"
    mock_commentaire.citoyenID = 1
    mock_commentaire.petitionID = 1
    mock_commentaire.dateCreated = "2024-01-01"
    mock_get_all_commentaires.return_value = [mock_commentaire]
    
    response = client.get('/commentaires_petition/all')
    
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['id'] == 1

@patch('app.services.commentaire.commentairePetition_service.update_commentaire')
def test_modify_commentaire(mock_update_commentaire, client):
    mock_commentaire = MagicMock()
    mock_commentaire.IDcommentaire = 1
    mock_update_commentaire.return_value = mock_commentaire
    
    response = client.put('/commentaires_petition/update/1', json={
        'description': 'Updated Commentaire'
    })
    
    assert response.status_code == 200
    assert response.json['id'] == 1

@patch('app.services.commentaire.commentairePetition_service.delete_commentaire')
def test_remove_commentaire(mock_delete_commentaire, client):
    mock_delete_commentaire.return_value = True
    
    response = client.delete('/commentaires_petition/delete/1')
    
    assert response.status_code == 204
