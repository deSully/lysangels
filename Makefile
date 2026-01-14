.PHONY: clean clean-pyc clean-build clean-test help
.DEFAULT_GOAL := help

help:
	@echo "Commandes disponibles:"
	@echo "  make clean          - Nettoyer tous les fichiers temporaires"
	@echo "  make clean-pyc      - Supprimer fichiers Python compilés (__pycache__, *.pyc, *.pyo)"
	@echo "  make clean-build    - Supprimer fichiers de build"
	@echo "  make clean-test     - Supprimer fichiers de tests"
	@echo "  make test           - Lancer les tests"
	@echo "  make migrate        - Appliquer les migrations"
	@echo "  make run            - Lancer le serveur de développement"
	@echo "  make populate       - Peupler la base de données"
	@echo "  make reset          - Réinitialiser la base de données"

clean: clean-pyc clean-build clean-test

clean-pyc:
	@echo "Suppression des fichiers Python compilés..."
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*~' -delete
	find . -type f -name '*.swp' -delete
	@echo "✓ Fichiers Python compilés supprimés"

clean-build:
	@echo "Suppression des fichiers de build..."
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	@echo "✓ Fichiers de build supprimés"

clean-test:
	@echo "Suppression des fichiers de tests..."
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	@echo "✓ Fichiers de tests supprimés"

test:
	@echo "Lancement des tests..."
	source venv/bin/activate && python manage.py test

test-fast:
	@echo "Lancement des tests (mode rapide)..."
	source venv/bin/activate && python manage.py test --keepdb

migrate:
	@echo "Application des migrations..."
	source venv/bin/activate && python manage.py migrate

makemigrations:
	@echo "Création des migrations..."
	source venv/bin/activate && python manage.py makemigrations

run:
	@echo "Démarrage du serveur de développement..."
	source venv/bin/activate && python manage.py runserver

populate:
	@echo "Peuplement de la base de données..."
	source venv/bin/activate && python populate_database.py

reset:
	@echo "Réinitialisation de la base de données..."
	source venv/bin/activate && python reset_database.py

install:
	@echo "Installation des dépendances..."
	source venv/bin/activate && pip install -r requirements.txt

shell:
	@echo "Ouverture du shell Django..."
	source venv/bin/activate && python manage.py shell

collectstatic:
	@echo "Collection des fichiers statiques..."
	source venv/bin/activate && python manage.py collectstatic --noinput

check:
	@echo "Vérification du projet..."
	source venv/bin/activate && python manage.py check

lint:
	@echo "Vérification du code (flake8)..."
	source venv/bin/activate && flake8 apps/ --max-line-length=120

format:
	@echo "Formatage du code (black)..."
	source venv/bin/activate && black apps/ --line-length=120

superuser:
	@echo "Création d'un superutilisateur..."
	source venv/bin/activate && python manage.py createsuperuser
