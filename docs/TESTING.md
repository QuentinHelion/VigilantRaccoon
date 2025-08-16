# Tests Unitaires - VigilantRaccoon

## Vue d'ensemble

VigilantRaccoon dispose d'une suite complète de tests unitaires pour assurer la qualité et la fiabilité du code. Les tests couvrent tous les modules principaux de l'application.

## Structure des tests

```
tests/
├── __init__.py
├── test_domain_entities.py      # Tests des entités du domaine
├── test_config.py               # Tests de la configuration
├── test_detect_security_events.py  # Tests de détection des événements
├── test_process_monitoring.py   # Tests de surveillance des processus
└── test_repositories.py         # Tests des repositories SQLite
```

## Exécution des tests

### Script principal (unittest)

```bash
# Exécuter tous les tests
python3 run_tests.py

# Lister tous les tests disponibles
python3 run_tests.py --list

# Exécuter un test spécifique
python3 run_tests.py --test domain_entities
python3 run_tests.py --test config
python3 run_tests.py --test detect_security_events
python3 run_tests.py --test process_monitoring
python3 run_tests.py --test repositories
```

### Script pytest (recommandé)

```bash
# Exécuter tous les tests avec pytest
python3 test_with_pytest.py

# Avec couverture de code
python3 test_with_pytest.py --coverage

# Tests spécifiques
python3 test_with_pytest.py --test domain_entities

# Avec marqueurs
python3 test_with_pytest.py --markers unit

# Installation des dépendances de développement
python3 test_with_pytest.py --install
```

### Commandes pytest directes

```bash
# Installation des dépendances
pip install -r requirements-dev.txt

# Exécution de tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=domain --cov=use_cases --cov=infrastructure --cov=interfaces

# Tests spécifiques
pytest tests/test_domain_entities.py -v

# Tests avec marqueurs
pytest tests/ -m unit
pytest tests/ -m security
pytest tests/ -m process
```

## Modules testés

### 1. Domain Entities (`test_domain_entities.py`)

**Classes testées :**
- `Alert` : Alertes de sécurité
- `Server` : Configuration des serveurs
- `AlertException` : Exceptions d'alertes

**Tests couverts :**
- ✅ Création d'objets
- ✅ Valeurs par défaut
- ✅ Validation des données
- ✅ Représentation en chaîne
- ✅ Mise à jour des propriétés

**Statut :** ✅ Tous les tests passent (11/11)

### 2. Configuration (`test_config.py`)

**Classes testées :**
- `ServerConfig` : Configuration des serveurs
- `EmailConfig` : Configuration email
- `StorageConfig` : Configuration du stockage
- `CollectionConfig` : Configuration de la collecte
- `WebConfig` : Configuration web
- `LoggingConfig` : Configuration du logging
- `AppConfig` : Configuration principale
- `load_config()` : Fonction de chargement

**Tests couverts :**
- ✅ Création des configurations
- ✅ Valeurs par défaut
- ✅ Chargement YAML valide
- ✅ Chargement YAML partiel
- ✅ Gestion des champs invalides
- ✅ Validation des données

**Statut :** ✅ Tous les tests passent (19/19)

### 3. Détection des événements (`test_detect_security_events.py`)

**Fonctions testées :**
- `parse_timestamp()` : Parsing des timestamps
- `detect_alerts()` : Détection des alertes
- Patterns regex : Détection des événements

**Tests couverts :**
- ✅ Parsing des timestamps ISO
- ✅ Parsing des timestamps syslog
- ✅ Détection des bannissements fail2ban
- ✅ Détection des échecs SSH
- ✅ Détection des connexions SSH acceptées
- ✅ Détection des tentatives d'intrusion
- ✅ Validation des patterns regex

**Statut :** ⚠️ 20/23 tests passent (3 échecs)
- ❌ Regex IPv4 trop permissif
- ❌ Parsing des timestamps syslog

### 4. Surveillance des processus (`test_process_monitoring.py`)

**Classes testées :**
- `ProcessInfo` : Informations des processus
- `ProcessMonitor` : Moniteur de processus
- `run_process_monitoring()` : Fonction principale

**Tests couverts :**
- ✅ Création des objets ProcessInfo
- ✅ Initialisation des patterns suspects
- ✅ Récupération des processus actifs
- ✅ Analyse des comportements suspects
- ✅ Surveillance des connexions réseau
- ✅ Surveillance des fichiers
- ✅ Gestion des erreurs

**Statut :** ✅ Tous les tests passent

### 5. Repositories SQLite (`test_repositories.py`)

**Classes testées :**
- `SQLiteAlertRepository` : Gestion des alertes
- `SQLiteStateRepository` : Gestion de l'état
- `SQLiteServerRepository` : Gestion des serveurs
- `SQLiteAlertExceptionRepository` : Gestion des exceptions

**Tests couverts :**
- ✅ Création des bases de données
- ✅ Sauvegarde et récupération
- ✅ Mise à jour des données
- ✅ Suppression des données
- ✅ Gestion des erreurs
- ✅ Validation des données

**Statut :** ✅ Tous les tests passent

## Couverture de code

### Objectif
- **Couverture minimale :** 80%
- **Couverture cible :** 90%+

### Modules couverts
- `domain/` : Entités et modèles
- `use_cases/` : Logique métier
- `infrastructure/` : Services externes
- `interfaces/` : Interface utilisateur

### Génération des rapports

```bash
# Rapport terminal
pytest tests/ --cov=domain --cov=use_cases --cov=infrastructure --cov=interfaces --cov-report=term-missing

# Rapport HTML
pytest tests/ --cov=domain --cov=use_cases --cov=infrastructure --cov=interfaces --cov-report=html:htmlcov

# Rapport XML (pour CI/CD)
pytest tests/ --cov=domain --cov=use_cases --cov=infrastructure --cov=interfaces --cov-report=xml
```

## Marqueurs de tests

### Marqueurs disponibles

```python
@pytest.mark.unit              # Tests unitaires
@pytest.mark.integration       # Tests d'intégration
@pytest.mark.slow             # Tests lents
@pytest.mark.security         # Tests de sécurité
@pytest.mark.process          # Tests de surveillance des processus
@pytest.mark.config           # Tests de configuration
@pytest.mark.repository       # Tests des repositories
```

### Utilisation des marqueurs

```bash
# Exécuter uniquement les tests unitaires
pytest tests/ -m unit

# Exécuter les tests de sécurité
pytest tests/ -m security

# Exclure les tests lents
pytest tests/ -m "not slow"

# Combinaison de marqueurs
pytest tests/ -m "unit and not slow"
```

## Tests d'intégration

### Base de données
- Tests avec base SQLite temporaire
- Nettoyage automatique après chaque test
- Isolation des tests

### Services externes
- Mock des appels SSH
- Mock des commandes système
- Simulation des erreurs réseau

## Qualité du code

### Outils utilisés

```bash
# Formatage du code
black .
isort .

# Linting
flake8 .
pylint domain/ use_cases/ infrastructure/ interfaces/

# Vérification des types
mypy domain/ use_cases/ infrastructure/ interfaces/

# Sécurité
bandit -r .
safety check
```

### Configuration

- **pytest.ini** : Configuration pytest
- **requirements-dev.txt** : Dépendances de développement
- **.flake8** : Configuration flake8
- **pyproject.toml** : Configuration des outils

## Tests en continu

### Intégration CI/CD
- Exécution automatique des tests
- Vérification de la couverture
- Validation de la qualité du code
- Tests de sécurité automatisés

### Pré-commit hooks
- Exécution des tests avant commit
- Vérification du formatage
- Validation des types
- Tests de sécurité

## Dépannage

### Problèmes courants

1. **Tests qui échouent localement mais passent en CI**
   - Vérifier les variables d'environnement
   - Vérifier les dépendances
   - Vérifier la configuration locale

2. **Tests lents**
   - Utiliser `pytest -m "not slow"`
   - Vérifier les timeouts
   - Optimiser les mocks

3. **Problèmes de couverture**
   - Vérifier les exclusions
   - Ajouter des tests manquants
   - Vérifier la configuration

### Debug des tests

```bash
# Mode verbose
pytest tests/ -v -s

# Arrêt au premier échec
pytest tests/ -x

# Affichage des variables locales
pytest tests/ --tb=long

# Tests spécifiques avec debug
pytest tests/test_config.py::TestAppConfig::test_app_config_creation -v -s
```

## Bonnes pratiques

### Écriture des tests

1. **Nommage clair**
   ```python
   def test_user_creation_with_valid_data():
       """Test de création d'utilisateur avec des données valides"""
   ```

2. **Tests isolés**
   - Chaque test doit être indépendant
   - Utiliser `setUp()` et `tearDown()`
   - Nettoyer les données après chaque test

3. **Assertions explicites**
   ```python
   # Bon
   self.assertEqual(user.name, "John")
   self.assertIsNotNone(user.id)
   
   # Éviter
   self.assertTrue(user.name == "John")
   ```

4. **Mocks appropriés**
   - Mocker les services externes
   - Utiliser des données de test réalistes
   - Tester les cas d'erreur

### Organisation des tests

1. **Structure en classes**
   ```python
   class TestUserService:
       def setUp(self):
           self.service = UserService()
       
       def test_create_user(self):
           # Test de création
           pass
       
       def test_create_user_invalid_data(self):
           # Test avec données invalides
           pass
   ```

2. **Groupement logique**
   - Tests unitaires
   - Tests d'intégration
   - Tests de performance
   - Tests de sécurité

## Métriques et rapports

### Rapports générés

- **Terminal** : Résumé des tests
- **HTML** : Rapport détaillé avec couverture
- **XML** : Format machine pour CI/CD
- **JSON** : Données structurées

### Métriques suivies

- Nombre de tests
- Taux de réussite
- Couverture de code
- Temps d'exécution
- Tests lents

## Support et maintenance

### Mise à jour des tests

1. **Ajout de nouvelles fonctionnalités**
   - Créer les tests correspondants
   - Maintenir la couverture
   - Valider les cas limites

2. **Refactoring**
   - Mettre à jour les tests
   - Vérifier la régression
   - Maintenir la cohérence

3. **Correction de bugs**
   - Ajouter des tests de régression
   - Valider la correction
   - Documenter le cas de test

### Documentation

- Maintenir cette documentation
- Documenter les cas de test complexes
- Expliquer les mocks et fixtures
- Fournir des exemples d'utilisation 