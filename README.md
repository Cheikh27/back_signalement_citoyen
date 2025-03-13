lancer la base de donnees (MYSQL)

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt   -->  Installez les dépendances

flask db init          |
flask db migrate       |  -->   Exécutez les migrations pour créer la base de données
flask db upgrade       |

flask run   -->   Lancez l'application  au lieu de ( python run.py ) car modifier au .env