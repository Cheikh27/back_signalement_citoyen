import pytest # type: ignore
from unittest.mock import patch, MagicMock
from flask import Flask
from app.routes.autres.groupe_route import groupe_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(groupe_bp)
    app.config['TESTING'] = True
    return app.test_client()

@patch('app.services.autres.groupe_service.create_groupe')
def test_add_groupe(mock_create_groupe, client):
    mock_groupe = MagicMock()
    mock_groupe.IDgroupe = 1
    mock_create_groupe.return_value = mock_groupe

    response = client.post('/api/groupes/add', json={
        'nom': 'Test Groupe',
        'description': 'Description du groupe',
        'statut': 'actif',
        'image': 'image.png',
        'admin': 1
    })
    
    assert response.status_code == 201
    assert response.get_json() == {'id': 1}

@patch('app.services.autres.groupe_service.get_groupe_by_id')
def test_get_groupe(mock_get_groupe_by_id, client):
    mock_groupe = MagicMock()
    mock_groupe.IDgroupe = 1
    mock_groupe.nom = 'Test Groupe'
    mock_groupe.description = 'Description du groupe'
    mock_groupe.statut = 'actif'
    mock_groupe.image = 'image.png'
    mock_groupe.admin = 1
    mock_groupe.dateCreated = '2024-02-12'
    mock_get_groupe_by_id.return_value = mock_groupe

    response = client.get('/api/groupes/1')
    
    assert response.status_code == 200
    assert response.get_json() == {
        'id': 1,
        'nom': 'Test Groupe',
        'description': 'Description du groupe',
        'statut': 'actif',
        'image': 'image.png',
        'admin': 1,
        'dateCreated': '2024-02-12'
    }

@patch('app.services.autres.groupe_service.get_all_groupes')
def test_list_groupes(mock_get_all_groupes, client):
    mock_groupe = MagicMock()
    mock_groupe.IDgroupe = 1
    mock_groupe.nom = 'Test Groupe'
    mock_groupe.description = 'Description du groupe'
    mock_groupe.statut = 'actif'
    mock_groupe.image = 'image.png'
    mock_groupe.admin = 1
    mock_groupe.dateCreated = '2024-02-12'
    mock_get_all_groupes.return_value = [mock_groupe]

    response = client.get('/api/groupes/all')
    
    assert response.status_code == 200
    assert response.get_json() == [{
        'id': 1,
        'nom': 'Test Groupe',
        'description': 'Description du groupe',
        'statut': 'actif',
        'image': 'image.png',
        'admin': 1,
        'dateCreated': '2024-02-12'
    }]

@patch('app.services.autres.groupe_service.update_groupe')
def test_modify_groupe(mock_update_groupe, client):
    mock_groupe = MagicMock()
    mock_groupe.IDgroupe = 1
    mock_update_groupe.return_value = mock_groupe

    response = client.put('/api/groupes/update/1', json={
        'nom': 'Groupe Modifié'
    })
    
    assert response.status_code == 200
    assert response.get_json() == {'id': 1}

@patch('app.services.autres.groupe_service.delete_groupe')
def test_remove_groupe(mock_delete_groupe, client):
    mock_delete_groupe.return_value = True

    response = client.delete('/api/groupes/delete/1')
    
    assert response.status_code == 204