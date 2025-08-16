# Surveillance des Processus - VigilantRaccoon

## Vue d'ensemble

Le module de surveillance des processus de VigilantRaccoon surveille en temps réel les processus système pour détecter des comportements suspects et des activités malveillantes sur vos serveurs Debian.

## Fonctionnalités

### 🔍 Détection des comportements suspects

- **Reverse shells** : Détection des tentatives de connexion inverse
- **Outils de téléchargement** : Surveillance des téléchargements suspects
- **Escalade de privilèges** : Détection des tentatives d'élévation de droits
- **Manipulation de fichiers** : Surveillance des modifications de permissions
- **Outils réseau** : Détection d'outils de reconnaissance réseau
- **Mining de cryptomonnaies** : Identification des processus de minage

### 🌐 Surveillance réseau

- **Connexions sortantes** : Surveillance des connexions réseau des processus
- **Ports suspects** : Détection des connexions vers des ports dangereux
- **Trafic anormal** : Identification du trafic réseau suspect

### 💾 Surveillance des ressources

- **Utilisation CPU** : Détection des processus consommant trop de ressources
- **Utilisation mémoire** : Surveillance de la consommation RAM
- **Utilisation disque** : Détection de l'activité disque excessive

### 📁 Surveillance des fichiers

- **Fichiers temporaires** : Détection de fichiers suspects dans `/tmp`, `/var/tmp`
- **Permissions dangereuses** : Surveillance des fichiers avec permissions 777/666
- **Extensions suspectes** : Détection de fichiers exécutables suspects

## Configuration

### Fichier de configuration

Le module utilise le fichier `config/process_monitoring.yaml` pour sa configuration :

```yaml
process_monitoring:
  suspicious_patterns:
    reverse_shell:
      enabled: true
      level: "high"
      patterns:
        - "nc -e /bin/bash"
        - "bash -i"
        - "python -c 'import socket'"
    
    download_tools:
      enabled: true
      level: "medium"
      patterns:
        - "wget.*http"
        - "curl.*http"
  
  suspicious_ports:
    - 22    # SSH
    - 23    # Telnet
    - 3389  # RDP
    - 5900  # VNC
  
  resource_thresholds:
    cpu_percent: 80.0
    memory_percent: 80.0
    disk_usage_percent: 90.0
```

### Paramètres configurables

| Paramètre | Description | Défaut |
|-----------|-------------|---------|
| `suspicious_patterns` | Patterns de détection des comportements suspects | Voir fichier de config |
| `suspicious_ports` | Ports réseau considérés comme suspects | [22, 23, 3389, 5900, 8080, 8443, 9000] |
| `resource_thresholds` | Seuils d'alerte pour l'utilisation des ressources | CPU: 80%, RAM: 80%, Disque: 90% |
| `suspicious_locations` | Emplacements surveillés pour les fichiers suspects | `/tmp`, `/var/tmp`, `/dev/shm` |
| `whitelist_commands` | Commandes système ignorées | `sshd`, `systemd`, `cron`, etc. |
| `whitelist_users` | Utilisateurs système ignorés | `root`, `systemd`, `daemon` |

## Utilisation

### Intégration automatique

Le module est automatiquement intégré dans le scheduler principal et s'exécute à chaque cycle de surveillance pour les serveurs locaux.

### Exécution manuelle

```python
from use_cases.process_monitoring import run_process_monitoring

# Surveillance d'un serveur spécifique
alerts = run_process_monitoring("mon-serveur")
print(f"Alertes générées: {len(alerts)}")
```

### Utilisation de la classe ProcessMonitor

```python
from use_cases.process_monitoring import ProcessMonitor

monitor = ProcessMonitor()

# Récupération des processus actifs
processes = monitor.get_active_processes("mon-serveur")

# Analyse d'un processus spécifique
alerts = monitor.analyze_process_behavior(processes[0])

# Surveillance des fichiers
file_alerts = monitor.check_file_activity("mon-serveur")
```

## Types d'alertes

### Niveaux de gravité

- **HIGH** : Comportements hautement suspects (reverse shells, mining, etc.)
- **MEDIUM** : Activités modérément suspectes (téléchargements, ports suspects)
- **INFO** : Informations de surveillance (démarrage de services, etc.)

### Règles de détection

| Règle | Description | Niveau |
|-------|-------------|---------|
| `suspicious_reverse_shell` | Détection de shells inverses | HIGH |
| `suspicious_download_tools` | Utilisation d'outils de téléchargement | MEDIUM |
| `suspicious_privilege_escalation` | Tentatives d'élévation de privilèges | HIGH |
| `suspicious_file_manipulation` | Manipulation de permissions de fichiers | MEDIUM |
| `suspicious_network_tools` | Utilisation d'outils de reconnaissance | MEDIUM |
| `suspicious_crypto_mining` | Processus de minage de cryptomonnaies | HIGH |
| `suspicious_network_connection` | Connexions réseau suspectes | MEDIUM |
| `high_resource_usage` | Utilisation excessive des ressources | MEDIUM |
| `suspicious_file_permissions` | Fichiers avec permissions dangereuses | HIGH |

## Personnalisation

### Ajout de nouveaux patterns

```yaml
suspicious_patterns:
  custom_pattern:
    enabled: true
    level: "medium"
    patterns:
      - "ma_commande_suspecte"
      - "autre_pattern"
```

### Modification des seuils

```yaml
resource_thresholds:
  cpu_percent: 70.0      # Alerte si CPU > 70%
  memory_percent: 75.0   # Alerte si RAM > 75%
  disk_usage_percent: 85.0  # Alerte si disque > 85%
```

### Ajout de ports suspects

```yaml
suspicious_ports:
  - 22      # SSH
  - 23      # Telnet
  - 3389    # RDP
  - 5900    # VNC
  - 8080    # HTTP alternatif
  - 8443    # HTTPS alternatif
  - 9000    # Port alternatif
  - 12345   # Port personnalisé
```

## Surveillance en temps réel

### Intégration avec le scheduler

Le module s'exécute automatiquement à chaque cycle de surveillance (par défaut toutes les 60 secondes) pour les serveurs locaux.

### Logs et monitoring

Toutes les activités sont enregistrées dans les logs de l'application avec le niveau de détail configuré.

### Notifications

Les alertes sont automatiquement envoyées par email si configuré, avec priorité pour les alertes de niveau HIGH.

## Dépannage

### Faux positifs

Si vous rencontrez trop de faux positifs :

1. **Ajustez les patterns** dans la configuration
2. **Ajoutez des commandes** à la whitelist
3. **Modifiez les seuils** de ressources
4. **Personnalisez les ports** suspects

### Performance

Pour optimiser les performances :

1. **Augmentez l'intervalle** de surveillance
2. **Réduisez le nombre** de processus surveillés
3. **Limitez la surveillance** aux processus critiques
4. **Utilisez des timeouts** appropriés

### Logs de débogage

Activez le mode DEBUG dans la configuration pour obtenir plus d'informations sur le fonctionnement du module.

## Sécurité

### Permissions requises

Le module nécessite des permissions pour :
- Lire les informations des processus (`ps`)
- Accéder aux informations réseau (`netstat`)
- Lire les répertoires système
- Exécuter des commandes système

### Isolation

Le module s'exécute dans un environnement isolé et n'a pas accès aux données sensibles des processus.

### Validation

Toutes les entrées sont validées et sanitizées avant traitement pour éviter les injections de commandes.

## Support

Pour toute question ou problème avec le module de surveillance des processus, consultez :
- La documentation de l'API
- Les logs de l'application
- Les tests unitaires inclus
- Les exemples de configuration 