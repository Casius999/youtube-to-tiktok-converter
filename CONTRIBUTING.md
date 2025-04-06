# Guide de contribution

Merci de votre intérêt pour contribuer au projet YouTube to TikTok Converter ! Ce document fournit des lignes directrices pour contribuer au projet.

## Principes fondamentaux

Cette application respecte les principes de la **Charte Universelle d'Intégrité Systémique** :
- **Authenticité** : Chaque opération doit produire des résultats vérifiables
- **Traçabilité** : Journalisation complète de toutes les opérations
- **Vérifiabilité** : Empreintes cryptographiques pour tous les artefacts
- **Transparence** : Documentation exhaustive du fonctionnement
- **Intégrité** : Validation multi-niveaux de chaque étape

Tous les contributeurs doivent adhérer à ces principes.

## Processus de contribution

1. **Fork du dépôt** : Commencez par forker le dépôt principal sur votre compte GitHub.

2. **Création d'une branche** : Créez une branche thématique pour vos modifications.
   ```bash
   git checkout -b feature/nom-de-votre-fonctionnalite
   ```
   ou
   ```bash
   git checkout -b fix/nom-du-correctif
   ```

3. **Développement** :
   - Suivez les conventions de codage du projet
   - Assurez-vous que votre code est bien documenté
   - Ajoutez des tests pour les nouvelles fonctionnalités
   - Veillez à ce que tous les tests passent

4. **Validation de l'intégrité** :
   - Assurez-vous que votre code génère les empreintes et journaux appropriés
   - Vérifiez que la traçabilité des opérations est maintenue
   - Utilisez les outils de validation fournis dans le projet

5. **Commit de vos changements** :
   ```bash
   git commit -m "Description claire et concise des changements"
   ```

6. **Push vers votre fork** :
   ```bash
   git push origin feature/nom-de-votre-fonctionnalite
   ```

7. **Soumission d'une Pull Request** : Ouvrez une Pull Request vers la branche principale du dépôt d'origine.

## Standards de code

- **Python** : Suivez PEP 8 pour le style de code
- **Documentation** : Utilisez docstrings pour documenter les modules, classes et fonctions
- **Tests** : Écrivez des tests unitaires et d'intégration pour les nouvelles fonctionnalités
- **Journalisation** : Utilisez le système de journalisation du projet pour tracer toutes les opérations
- **Validation** : Intégrez des mécanismes de validation d'intégrité pour les nouvelles opérations

## Exigences pour les Pull Requests

- **Description détaillée** des changements apportés
- **Issue référencée** si applicable
- **Tests passants** pour toutes les fonctionnalités
- **Documentation** mise à jour si nécessaire
- **Suivi des principes** d'intégrité systémique

## Rapport de bugs

Pour signaler un bug, veuillez créer une issue avec les informations suivantes :
- Description précise du problème
- Étapes pour reproduire le bug
- Comportement attendu vs comportement observé
- Environnement (OS, versions des dépendances, etc.)
- Logs d'erreur et captures d'écran si disponibles

## Suggestions de fonctionnalités

Pour suggérer une nouvelle fonctionnalité, veuillez créer une issue décrivant :
- Le problème que cette fonctionnalité résoudrait
- Comment cette fonctionnalité s'intégrerait dans le projet
- Les avantages de cette fonctionnalité
- Éventuellement, des exemples d'implémentation similaires dans d'autres projets

## Sécurité

Si vous découvrez une vulnérabilité de sécurité, veuillez envoyer un email à security@example.com plutôt que de créer une issue publique.

## Licence

En contribuant à ce projet, vous acceptez que vos contributions soient sous la même licence que le projet (MIT).

Merci de contribuer à rendre ce projet meilleur !
