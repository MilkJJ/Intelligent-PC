# Intelligent-PC
source venv/Scripts/activate

deactivate

pip freeze > requirements.txt

pip install -r requirements.txt

python manage.py makemigrations

python manage.py migrate

python manage.py runserver
