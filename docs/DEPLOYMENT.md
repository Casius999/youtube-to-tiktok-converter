# Documentation de déploiement sur GCP

## Informations du projet GCP

**Détails du projet :**
- **Nom du projet :** My First Project
- **ID du projet :** powerful-host-455818-i8
- **Numéro du projet :** 1004994141013
- **Crédits disponibles :** 10 161 $ (valables jusqu'au 4 juillet 2025)

## Infrastructure existante

**Dépôts d'artefacts :**
- **Repository principal :** youtube-tiktok-repo (Artifact Registry)
- **URI du registre :** us-central1-docker.pkg.dev/powerful-host-455818-i8/youtube-tiktok-repo
- **Location :** us-central1
- **Description :** Dépôt pour YouTube to TikTok Converter

**Configuration d'identité Workload :**
- **Pool d'identité :** github-actions-pool
- **Nom complet du pool :** projects/1004994141013/locations/global/workloadIdentityPools/github-actions-pool
- **Fournisseur :** github-actions-provider
- **Condition :** Repository limité à 'Casius999/youtube-to-tiktok-converter'

**Compte de service :**
- **Nom :** github-actions-sa
- **Email :** github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com
- **Rôles :** 
  - roles/run.admin
  - roles/artifactregistry.admin
  - roles/storage.admin
  - roles/iam.serviceAccountUser
  - roles/iam.workloadIdentityUser

## Détails de l'architecture de déploiement

### Pipeline de déploiement

Le déploiement est orchestré par GitHub Actions qui :
1. Construit une image Docker à partir du code source
2. Pousse l'image vers Artifact Registry de GCP
3. Déploie l'application sur Cloud Run

### Workflow GitHub Actions

Le workflow est défini dans `.github/workflows/deploy-to-gcp.yml` et utilise l'authentification Workload Identity Federation pour sécuriser la communication entre GitHub et GCP.

```yaml
workload_identity_provider: 'projects/1004994141013/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider'
service_account: 'github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com'
```

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

## Configuration initiale de GCP (déjà effectuée)

Si vous devez reconfigurer l'environnement GCP, voici les commandes à exécuter :

```bash
# 1. Créer un compte de service pour GitHub Actions
gcloud iam service-accounts create github-actions-sa --display-name="GitHub Actions Service Account"

# 2. Accorder les rôles nécessaires
gcloud projects add-iam-policy-binding powerful-host-455818-i8 \
  --member="serviceAccount:github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding powerful-host-455818-i8 \
  --member="serviceAccount:github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding powerful-host-455818-i8 \
  --member="serviceAccount:github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 3. Configurer Workload Identity Federation
gcloud iam workload-identity-pools create github-actions-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-actions-provider \
  --workload-identity-pool=github-actions-pool \
  --location=global \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping=google.subject=assertion.sub \
  --attribute-condition="assertion.repository=='Casius999/youtube-to-tiktok-converter'" \
  --display-name="GitHub Actions Provider"

# 4. Configurer la liaison entre le compte de service et l'identité GitHub
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/1004994141013/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/Casius999/youtube-to-tiktok-converter"

# 5. Créer un dépôt Artifact Registry
gcloud artifacts repositories create youtube-tiktok-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Dépôt pour YouTube to TikTok Converter"
```

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
