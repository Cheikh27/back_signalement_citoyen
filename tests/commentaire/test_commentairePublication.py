import pytest # type: ignore
from unittest.mock import patch, MagicMock
from flask import Flask
from app.routes.commentaire.commentairePublication_route import commentaire_publication_bp

@pytest.fixture
def client():
    """Fixture pour configurer l'application Flask en mode test"""
    app = Flask(__name__)
    app.register_blueprint(commentaire_publication_bp)
    app.config['TESTING'] = True
    return app.test_client()

@patch('app.routes.commentaire.commentairePublication_routes.create_commentaire_publication')
def test_add_commentaire_publication(mock_create, client):
    """Test pour la création d'un commentaire"""
    mock_create.return_value = MagicMock(IDcommentaire=1)

    response = client.post('/commentaires-publication/add', json={
        'description': 'Test Commentaire',
        'citoyen_id': 123,
        'publication_id': 456
    })

    assert response.status_code == 201
    assert response.json == {'id': 1}
    mock_create.assert_called_once()

@patch('app.routes.commentaire.commentairePublication_routes.get_commentaire_publication_by_id')
def test_get_commentaire_publication(mock_get, client):
    """Test pour la récupération d'un commentaire par ID"""
    mock_get.return_value = MagicMock(
        IDcommentaire=1, description="Test", citoyenID=123, publicationID=456, dateCreated="2024-02-13"
    )

    response = client.get('/commentaires-publication/1')

    assert response.status_code == 200
    assert response.json['id'] == 1
    mock_get.assert_called_once_with(1)

@patch('app.routes.commentaire.commentairePublication_routes.get_all_commentaires_publication')
def test_list_commentaires_publication(mock_get_all, client):
    """Test pour la récupération de tous les commentaires"""
    mock_get_all.return_value = [
        MagicMock(IDcommentaire=1, description="Comment 1", citoyenID=123, publicationID=456, dateCreated="2024-02-13"),
        MagicMock(IDcommentaire=2, description="Comment 2", citoyenID=124, publicationID=457, dateCreated="2024-02-14")
    ]

    response = client.get('/commentaires-publication/all')

    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['id'] == 1
    assert response.json[1]['id'] == 2
    mock_get_all.assert_called_once()

@patch('app.routes.commentaire.commentairePublication_routes.update_commentaire_publication')
def test_modify_commentaire_publication(mock_update, client):
    """Test pour la mise à jour d'un commentaire"""
    mock_update.return_value = MagicMock(IDcommentaire=1)

    response = client.put('/commentaires-publication/update/1', json={'description': 'Updated Comment'})

    assert response.status_code == 200
    assert response.json == {'id': 1}
    mock_update.assert_called_once_with(1, description='Updated Comment')

@patch('app.routes.commentaire.commentairePublication_routes.delete_commentaire_publication')
def test_remove_commentaire_publication(mock_delete, client):
    """Test pour la suppression d'un commentaire"""
    mock_delete.return_value = True

    response = client.delete('/commentaires-publication/delete/1')

    assert response.status_code == 204
    mock_delete.assert_called_once_with(1)

    # Test lorsque le commentaire n'existe pas
    mock_delete.return_value = False
    response = client.delete('/commentaires-publication/delete/99')
    assert response.status_code == 404
    assert response.json == {'message': 'Not found'}
