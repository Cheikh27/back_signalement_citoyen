lancer la base de donnees (MYSQL)

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt   -->  Installez les dépendances

flask db downgrade base |
rm -r migrations        |---------> au cas ou

flask db init          |
flask db migrate       |  -->   Exécutez les migrations pour créer la base de données
flask db upgrade       |

flask run --debug   -->   Lancez l'application  au lieu de ( python run.py ) car modifier au .env

http://127.0.0.1:5000/apidocs   ======>  pour acceder aux documentations
http://127.0.0.1:5000/api/xxxxxx   ====>  pour acceder aux API 