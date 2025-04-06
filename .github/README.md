# Configuration du déploiement GitHub Actions vers Google Cloud Run

Pour finaliser la configuration du déploiement automatique vers Google Cloud Run, suivez ces étapes :

1. Le compte de service `github-actions-sa` a été créé dans le projet GCP `powerful-host-455818-i8`

2. Une clé de compte de service a été générée dans le fichier `github-actions-key.json`

3. **Ajoutez cette clé comme secret GitHub** :
   - Allez dans "Settings" > "Secrets and variables" > "Actions" de votre dépôt
   - Cliquez sur "New repository secret"
   - Nommez-le `GCP_SA_KEY`
   - Copiez le contenu entier du fichier `github-actions-key.json` dans la valeur
   - Cliquez sur "Add secret"

4. Le workflow GitHub Actions est déjà configuré dans le fichier `.github/workflows/google-cloud-run.yml`

5. Après avoir ajouté le secret, tout push sur la branche main déclenchera automatiquement le déploiement sur Google Cloud Run

## Informations techniques

- **Projet GCP** : powerful-host-455818-i8
- **Service** : youtube-tiktok-converter
- **Région** : us-central1
- **Compte de service** : github-actions-sa@powerful-host-455818-i8.iam.gserviceaccount.com
- **Rôles attribués** : 
  - roles/run.admin
  - roles/storage.admin
  - roles/iam.serviceAccountUser

## Accès au service déployé

Une fois déployé, le service sera accessible à l'URL fournie par Cloud Run, généralement sous la forme :
```
https://youtube-tiktok-converter-randomid-uc.a.run.app
```

Vous pourrez trouver cette URL dans la console GCP sous Cloud Run ou dans les journaux de déploiement GitHub Actions.
