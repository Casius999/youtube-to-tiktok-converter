FROM python:3.10-slim

# Installation des dépendances système requises
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Définition du répertoire de travail
WORKDIR /app

# Copie des fichiers de configuration
COPY requirements.txt .
COPY .env.example .env

# Installation des dépendances Python
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création des répertoires nécessaires
RUN mkdir -p data/temp data/output data/logs

# Exposition du port pour l'interface web
EXPOSE 8000

# Variables d'environnement
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Point d'entrée
ENTRYPOINT ["python", "-m", "src.main"]

# Commande par défaut (démarrage de l'interface web)
CMD ["web"]
