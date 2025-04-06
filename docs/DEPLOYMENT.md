# Documentation de déploiement sur GCP

## Informations du projet GCP

**Détails du projet :**
- **Nom du projet :** My First Project
- **ID du projet :** powerful-host-455818-i8
- **Numéro du projet :** 10D4994141013
- **Crédits disponibles :** 10 161 $ (valables jusqu'au 4 juillet 2025)

## Infrastructure existante

**Dépôts d'artefacts :**
- Repository principal : youtube-tiktok-repo (Artifact Registry)
- Location : us-central1

**Services Cloud Run :**
- Service principal : youtube-tiktok-converter
- Région : us-central1

## Détails de l'architecture de déploiement

### Pipeline de déploiement

Le déploiement est orchestré par GitHub Actions qui :
1. Construit une image Docker à partir du code source
2. Pousse l'image vers Artifact Registry de GCP
3. Déploie l'application sur Cloud Run

### Workflow GitHub Actions

Le workflow est défini dans `.github/workflows/deploy-to-gcp.yml` et utilise l'authentification Workload Identity Federation pour sécuriser la communication entre GitHub et GCP.

## Instructions de déploiement manuel

Si un déploiement manuel est nécessaire, voici les commandes à exécuter dans Cloud Shell :

```bash
# 1. Cloner le dépôt
git clone https://github.com/Casius999/youtube-to-tiktok-converter.git
cd youtube-to-tiktok-converter

# 2. Construire l'image Docker
docker build -t us-central1-docker.pkg.dev/powerful-host-455818-i8/youtube-tiktok-repo/youtube-tiktok-converter:latest .

# 3. Pousser l'image vers Artifact Registry
docker push us-central1-docker.pkg.dev/powerful-host-455818-i8/youtube-tiktok-repo/youtube-tiktok-converter:latest

# 4. Déployer sur Cloud Run
gcloud run deploy youtube-tiktok-converter \
  --image us-central1-docker.pkg.dev/powerful-host-455818-i8/youtube-tiktok-repo/youtube-tiktok-converter:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

## Configuration du service Cloud Run

- **Mémoire allouée :** 2 Go
- **CPU :** 1
- **Mise à l'échelle automatique :** 0-10 instances
- **Accessibilité :** Publique (--allow-unauthenticated)

## Variables d'environnement requises

Le service Cloud Run nécessite les variables d'environnement suivantes :
- `YOUTUBE_API_KEY` : Clé API YouTube
- `TIKTOK_API_KEY` : Clé API TikTok
- `TIKTOK_API_SECRET` : Secret API TikTok
- `MONGODB_URI` : URI de connexion MongoDB
- `LOG_LEVEL` : Niveau de journalisation (INFO, DEBUG, etc.)

## Surveillance et journalisation

- **Logs d'application :** Cloud Logging
- **Métriques de performance :** Cloud Monitoring
- **Alertes :** Configurées via Cloud Monitoring

## Dépannage

Si l'application ne se déploie pas correctement :
1. Vérifier les logs GitHub Actions pour les erreurs de build
2. Vérifier les logs Cloud Run pour les erreurs d'exécution
3. S'assurer que toutes les API requises sont activées
4. Vérifier que le compte de service a les permissions nécessaires

## Maintenance

### Mises à jour de l'application
Un push sur la branche `main` du dépôt GitHub déclenchera automatiquement un nouveau déploiement.

### Mises à jour manuelles
```bash
# Mettre à jour l'application manuellement
gcloud run services update youtube-tiktok-converter \
  --image us-central1-docker.pkg.dev/powerful-host-455818-i8/youtube-tiktok-repo/youtube-tiktok-converter:new-tag
```

## Contacts et responsabilités

Pour toute question concernant le déploiement, contacter l'équipe DevOps.
