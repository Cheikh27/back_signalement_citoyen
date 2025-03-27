import pytest # type: ignore
from unittest.mock import patch
from flask import json
from app import create_app
from app.models.autres.appartenir_model import Appartenir

@pytest.fixture
def client():
    app = create_app("testing")  # Assurez-vous d'avoir une configuration 'testing'
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

@patch('app.services.autres.appartenir_service.create_appartenir')
def test_add_appartenir(mock_create, client):
    mock_create.return_value = Appartenir(IDappartenir=1, citoyenID=10, groupeID=20)
    
    response = client.post('/api/appartenirs/add', json={'citoyen_id': 10, 'groupe_id': 20})
    assert response.status_code == 201
    assert response.json == {'id': 1}

@patch('app.services.autres.appartenir_service.get_appartenir_by_id')
def test_get_appartenir(mock_get, client):
    mock_get.return_value = Appartenir(IDappartenir=1, citoyenID=10, groupeID=20, dateCreated="2024-01-01")
    
    response = client.get('/api/appartenirs/1')
    assert response.status_code == 200
    assert response.json == {
        'id': 1, 'dateCreated': "2024-01-01", 'citoyen_id': 10, 'groupe_id': 20
    }

@patch('app.services.autres.appartenir_service.get_all_appartenirs')
def test_list_appartenirs(mock_get_all, client):
    mock_get_all.return_value = [Appartenir(IDappartenir=1, citoyenID=10, groupeID=20, dateCreated="2024-01-01")]
    
    response = client.get('/api/appartenirs/all')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['id'] == 1

@patch('app.services.autres.appartenir_service.update_appartenir')
def test_modify_appartenir(mock_update, client):
    mock_update.return_value = Appartenir(IDappartenir=1, citoyenID=15, groupeID=25)
    
    response = client.put('/api/appartenirs/update/1', json={'citoyen_id': 15, 'groupe_id': 25})
    assert response.status_code == 200
    assert response.json == {'id': 1}

@patch('app.services.autres.appartenir_service.delete_appartenir')
def test_remove_appartenir(mock_delete, client):
    mock_delete.return_value = True
    
    response = client.delete('/api/appartenirs/delete/1')
    assert response.status_code == 204
