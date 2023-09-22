# Intelligent-PC
<!-- Before running -->
source venv/Scripts/activate
pip install -r requirements.txt

<!-- Before commit and push -->
pip freeze > requirements.txt

<!-- To run -->
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

<!-- Finish running -->
deactivate
