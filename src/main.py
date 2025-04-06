#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module principal de l'application YouTube to TikTok Converter.

Ce module est le point d'entrée principal de l'application, coordonnant
le flux de travail complet depuis l'acquisition jusqu'à la publication.
"""

import os
import sys
import time
from pathlib import Path

import typer
from loguru import logger
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialisation
app_cli = typer.Typer(help="YouTube to TikTok Converter")

# Création des dossiers nécessaires
for directory in ["data", "data/temp", "data/output", "data/logs"]:
    Path(directory).mkdir(exist_ok=True, parents=True)

# Configuration du logger
log_path = Path("data/logs")
log_path.mkdir(exist_ok=True, parents=True)
logger.add(
    log_path / "app_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,
    diagnose=True,
)


@app_cli.command()
def convert(
    url: str = typer.Argument(..., help="URL de la vidéo YouTube à convertir"),
    output_dir: str = typer.Option(None, "--output", "-o", help="Dossier de sortie"),
    audio_quality: str = typer.Option("high", "--audio-quality", "-a"),
    video_quality: str = typer.Option("high", "--video-quality", "-v"),
    publish: bool = typer.Option(False, "--publish", "-p"),
):
    """Convertit une vidéo YouTube en vidéo TikTok optimisée pour la viralité."""
    logger.info(f"Démarrage de la conversion: {url}")
    logger.info("Cette fonctionnalité sera implémentée dans une version future.")


@app_cli.command()
def web():
    """Démarre l'interface web de l'application."""
    import uvicorn
    
    # Création de l'application FastAPI
    web_app = FastAPI(
        title="YouTube to TikTok Converter",
        description="API pour convertir des vidéos YouTube en vidéos TikTok optimisées pour la viralité",
        version="1.0.0"
    )
    
    # Configuration CORS
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @web_app.get("/")
    async def read_root():
        """Page d'accueil de l'API."""
        return {
            "name": "YouTube to TikTok Converter API",
            "version": "1.0.0",
            "status": "online",
            "timestamp": time.time()
        }
    
    @web_app.get("/api/status")
    async def get_status():
        """Vérifie l'état de l'API."""
        return {
            "status": "operational",
            "environment": os.getenv("ENVIRONMENT", "production"),
            "timestamp": time.time()
        }
    
    @web_app.post("/api/convert")
    async def api_convert(url: str):
        """Convertit une vidéo YouTube en vidéo TikTok."""
        if not url:
            raise HTTPException(status_code=400, detail="URL manquante")
        
        process_id = f"process_{int(time.time())}"
        
        return {
            "process_id": process_id,
            "status": "accepted",
            "message": "Conversion en attente d'implémentation",
            "url": url,
            "timestamp": time.time()
        }
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    logger.info(f"Démarrage de l'interface web sur http://{host}:{port}")
    uvicorn.run(web_app, host=host, port=port)


@app_cli.command()
def version():
    """Affiche la version de l'application."""
    logger.info("Version: 1.0.0")
    return "1.0.0"


if __name__ == "__main__":
    app_cli()
