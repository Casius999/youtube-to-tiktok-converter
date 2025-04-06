# YouTube to TikTok Converter

Application de production permettant de transformer des vidéos YouTube en contenu TikTok optimisé pour la viralité, avec traçabilité et vérifiabilité complètes.

## Principes fondamentaux

Cette application respecte les principes de la **Charte Universelle d'Intégrité Systémique** :
- **Authenticité** : Chaque opération produit des résultats vérifiables
- **Traçabilité** : Journalisation complète de toutes les opérations
- **Vérifiabilité** : Empreintes cryptographiques pour tous les artefacts
- **Transparence** : Documentation exhaustive du fonctionnement
- **Intégrité** : Validation multi-niveaux de chaque étape

## Architecture

L'application est composée de six modules principaux :

1. **Acquisition** : Téléchargement et extraction des vidéos YouTube
2. **Analyse** : Segmentation intelligente du contenu
3. **Montage** : Réorganisation narrative et application d'effets
4. **Adaptation** : Conversion au format vertical TikTok
5. **Optimisation** : Génération de métadonnées pour maximiser l'engagement
6. **Publication** : Validation et publication sur TikTok

## Prérequis techniques

- Python 3.10+
- FFmpeg
- TensorFlow/PyTorch
- API YouTube Data v3
- API TikTok pour Créateurs
- MongoDB (stockage des métadonnées et logs)
- S3 ou équivalent (stockage des fichiers)

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/youtube-to-tiktok-converter.git
cd youtube-to-tiktok-converter

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer le fichier .env avec vos clés API
```

## Configuration

Créez un fichier `.env` à la racine du projet avec les informations suivantes :

```
YOUTUBE_API_KEY=votre_clé_api_youtube
TIKTOK_API_KEY=votre_clé_api_tiktok
TIKTOK_API_SECRET=votre_secret_api_tiktok
MONGODB_URI=votre_uri_mongodb
S3_BUCKET=nom_de_votre_bucket
AWS_ACCESS_KEY=votre_clé_accès_aws
AWS_SECRET_KEY=votre_clé_secrète_aws
LOG_LEVEL=INFO
```

## Utilisation

```bash
# Pour lancer l'application avec interface web
python -m src.main --web

# Pour utiliser en ligne de commande
python -m src.main --url https://www.youtube.com/watch?v=VIDEO_ID
```

## Mécanismes de validation

Chaque étape du processus génère :
- Des fichiers de log détaillés (format JSON)
- Des rapports d'intégrité avec hachages SHA-256
- Des captures d'écran automatisées des étapes clés
- Des métadonnées sur les transformations appliquées

## Structure du projet

```
youtube-to-tiktok-converter/
├── src/
│   ├── acquisition/    # Module d'extraction YouTube
│   ├── analysis/       # Module d'analyse IA
│   ├── editing/        # Module de montage
│   ├── adaptation/     # Module d'adaptation format
│   ├── optimization/   # Module d'optimisation viralité
│   ├── publication/    # Module de publication TikTok
│   ├── utils/          # Utilitaires partagés
│   ├── validation/     # Systèmes de validation
│   ├── storage/        # Gestion du stockage
│   ├── logging/        # Infrastructure de journalisation
│   └── main.py         # Point d'entrée principal
├── tests/              # Tests unitaires et d'intégration
├── docs/               # Documentation détaillée
├── scripts/            # Scripts utilitaires
├── data/               # Dossier pour les données (ignoré par git)
│   ├── temp/           # Fichiers temporaires
│   ├── output/         # Résultats finaux
│   └── logs/           # Journaux détaillés
├── .env.example        # Exemple de configuration
├── requirements.txt    # Dépendances Python
├── docker-compose.yml  # Configuration Docker
├── Dockerfile          # Instructions de build
└── README.md           # Cette documentation
```

## Contribution

Les contributions doivent respecter les principes de la Charte d'Intégrité Systémique :
1. Forker le dépôt
2. Créer une branche de fonctionnalité
3. Implémenter les changements avec documentation complète
4. Soumettre une pull request avec validation des tests

## Licence

MIT
