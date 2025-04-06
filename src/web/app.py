"""Module d'interface web pour l'application.

Ce module fournit une interface web pour interagir avec l'application,
permettant aux utilisateurs de soumettre des vidéos YouTube et de suivre
le processus de conversion.
"""

import os
import sys
import json
import time
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from loguru import logger
from pathlib import Path

# Import des modules internes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.config import Config
from src.acquisition.youtube_downloader import YouTubeDownloader
from src.analysis.video_analyzer import VideoAnalyzer
from src.editing.video_editor import VideoEditor
from src.adaptation.format_adapter import FormatAdapter
from src.optimization.viral_optimizer import ViralOptimizer
from src.publication.tiktok_publisher import TikTokPublisher
from src.validation.integrity_validator import IntegrityValidator
from src.storage.artifact_manager import ArtifactManager
from src.logging.audit import AuditLogger


# Modèles de données pour l'API
class ConversionRequest(BaseModel):
    """Modèle pour une demande de conversion."""
    url: str = Field(..., description="URL de la vidéo YouTube à convertir")
    audio_quality: str = Field("high", description="Qualité audio (low, medium, high)")
    video_quality: str = Field("high", description="Qualité vidéo (low, medium, high)")
    publish: bool = Field(False, description="Publier directement sur TikTok")
    hashtags: List[str] = Field([], description="Hashtags à ajouter")


class ConversionResponse(BaseModel):
    """Modèle pour une réponse de conversion."""
    process_id: str = Field(..., description="Identifiant unique du processus")
    status: str = Field(..., description="Statut de la conversion")
    message: str = Field(..., description="Message d'information")
    url: Optional[str] = Field(None, description="URL de la vidéo YouTube")
    timestamp: float = Field(..., description="Timestamp de la demande")
    output_dir: Optional[str] = Field(None, description="Répertoire de sortie")


class ConversionStatus(BaseModel):
    """Modèle pour le statut d'une conversion."""
    process_id: str = Field(..., description="Identifiant unique du processus")
    status: str = Field(..., description="Statut de la conversion")
    progress: float = Field(..., description="Progression de la conversion (0-100)")
    current_stage: str = Field(..., description="Étape actuelle")
    started_at: float = Field(..., description="Timestamp de début")
    elapsed_time: float = Field(..., description="Temps écoulé en secondes")
    estimated_time_remaining: Optional[float] = Field(None, description="Temps restant estimé en secondes")
    error: Optional[str] = Field(None, description="Message d'erreur éventuel")


# Stockage des processus en cours
active_processes: Dict[str, Dict[str, Any]] = {}


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI.
    
    Returns:
        Application FastAPI configurée
    """
    app = FastAPI(
        title="YouTube to TikTok Converter",
        description="API pour convertir des vidéos YouTube en vidéos TikTok optimisées pour la viralité",
        version="1.0.0"
    )
    
    # Configuration CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Dossier des fichiers statiques
    static_dir = Path("data/output")
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Routes API
    @app.get("/")
    async def read_root():
        """Page d'accueil de l'API."""
        return {
            "name": "YouTube to TikTok Converter API",
            "version": "1.0.0",
            "status": "online",
            "timestamp": time.time()
        }
    
    @app.post("/api/convert", response_model=ConversionResponse)
    async def convert_video(
        request: ConversionRequest,
        background_tasks: BackgroundTasks
    ):
        """Convertit une vidéo YouTube en vidéo TikTok."""
        # Génération d'un identifiant unique pour le processus
        process_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Initialisation du processus
        active_processes[process_id] = {
            "status": "initializing",
            "progress": 0.0,
            "current_stage": "initialisation",
            "started_at": timestamp,
            "request": request.dict(),
            "output_dir": str(Path(f"data/output/{process_id}")),
            "error": None
        }
        
        # Lancement de la conversion en arrière-plan
        background_tasks.add_task(
            process_conversion,
            process_id,
            request.url,
            request.audio_quality,
            request.video_quality,
            request.publish,
            request.hashtags
        )
        
        # Réponse immédiate
        return ConversionResponse(
            process_id=process_id,
            status="initializing",
            message="Conversion démarrée",
            url=request.url,
            timestamp=timestamp,
            output_dir=active_processes[process_id]["output_dir"]
        )
    
    @app.get("/api/status/{process_id}", response_model=ConversionStatus)
    async def get_status(process_id: str):
        """Récupère le statut d'une conversion en cours."""
        if process_id not in active_processes:
            raise HTTPException(status_code=404, detail="Processus non trouvé")
        
        process = active_processes[process_id]
        elapsed_time = time.time() - process["started_at"]
        
        # Calcul du temps restant estimé
        estimated_time_remaining = None
        if process["progress"] > 0 and process["progress"] < 100:
            estimated_time_remaining = (elapsed_time / process["progress"]) * (100 - process["progress"])
        
        return ConversionStatus(
            process_id=process_id,
            status=process["status"],
            progress=process["progress"],
            current_stage=process["current_stage"],
            started_at=process["started_at"],
            elapsed_time=elapsed_time,
            estimated_time_remaining=estimated_time_remaining,
            error=process.get("error")
        )
    
    @app.get("/api/results/{process_id}")
    async def get_results(process_id: str):
        """Récupère les résultats d'une conversion terminée."""
        if process_id not in active_processes:
            raise HTTPException(status_code=404, detail="Processus non trouvé")
        
        process = active_processes[process_id]
        
        if process["status"] != "completed":
            raise HTTPException(status_code=400, detail="Conversion non terminée")
        
        # Récupération du rapport final
        try:
            report_file = Path(process["output_dir"]) / "final_report.json"
            if not report_file.exists():
                raise HTTPException(status_code=404, detail="Rapport non trouvé")
            
            with open(report_file, "r") as f:
                report = json.load(f)
            
            return report
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des résultats: {str(e)}")
    
    @app.get("/api/download/{process_id}")
    async def download_video(process_id: str):
        """Télécharge la vidéo convertie."""
        if process_id not in active_processes:
            raise HTTPException(status_code=404, detail="Processus non trouvé")
        
        process = active_processes[process_id]
        
        if process["status"] != "completed":
            raise HTTPException(status_code=400, detail="Conversion non terminée")
        
        # Récupération du rapport final pour obtenir le chemin de la vidéo
        try:
            report_file = Path(process["output_dir"]) / "final_report.json"
            if not report_file.exists():
                raise HTTPException(status_code=404, detail="Rapport non trouvé")
            
            with open(report_file, "r") as f:
                report = json.load(f)
            
            video_path = report.get("final_video")
            if not video_path or not os.path.exists(video_path):
                raise HTTPException(status_code=404, detail="Vidéo non trouvée")
            
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename=f"tiktok_video_{process_id}.mp4"
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du téléchargement: {str(e)}")
    
    @app.delete("/api/cancel/{process_id}")
    async def cancel_conversion(process_id: str):
        """Annule une conversion en cours."""
        if process_id not in active_processes:
            raise HTTPException(status_code=404, detail="Processus non trouvé")
        
        process = active_processes[process_id]
        
        if process["status"] in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Processus déjà terminé")
        
        # Mise à jour du statut
        process["status"] = "cancelled"
        process["progress"] = 100.0
        process["current_stage"] = "annulation"
        
        return {"status": "success", "message": "Conversion annulée"}
    
    @app.get("/api/list")
    async def list_conversions():
        """Liste toutes les conversions."""
        result = []
        
        for process_id, process in active_processes.items():
            result.append({
                "process_id": process_id,
                "status": process["status"],
                "progress": process["progress"],
                "current_stage": process["current_stage"],
                "started_at": process["started_at"],
                "url": process.get("request", {}).get("url"),
                "elapsed_time": time.time() - process["started_at"]
            })
        
        return result
    
    return app


async def process_conversion(
    process_id: str,
    url: str,
    audio_quality: str,
    video_quality: str,
    publish: bool,
    hashtags: List[str]
):
    """Traite une demande de conversion en arrière-plan.
    
    Args:
        process_id: Identifiant unique du processus
        url: URL de la vidéo YouTube
        audio_quality: Qualité audio (low, medium, high)
        video_quality: Qualité vidéo (low, medium, high)
        publish: Publier directement sur TikTok
        hashtags: Hashtags à ajouter
    """
    try:
        # Mise à jour du statut
        active_processes[process_id]["status"] = "processing"
        
        # Chemin du dossier de sortie
        output_path = Path(active_processes[process_id]["output_dir"])
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        config = Config(
            audio_quality=audio_quality,
            video_quality=video_quality,
            output_dir=str(output_path),
            process_id=process_id,
            hashtags=hashtags
        )
        
        # Initialisation des composants
        audit_logger = AuditLogger(process_id)
        audit_logger.log_start(url)
        
        artifact_manager = ArtifactManager(process_id, str(output_path))
        integrity_validator = IntegrityValidator(process_id)
        
        # Étape 1: Acquisition et Extraction (20%)
        update_process_status(process_id, "downloading", 5, "Téléchargement de la vidéo")
        
        downloader = YouTubeDownloader(config)
        video_path, audio_path, video_info = downloader.download(url)
        
        # Validation et audit
        video_hash = integrity_validator.generate_file_hash(video_path)
        audio_hash = integrity_validator.generate_file_hash(audio_path)
        artifact_manager.save_file_info({
            "stage": "acquisition",
            "video_path": video_path,
            "video_hash": video_hash,
            "audio_path": audio_path,
            "audio_hash": audio_hash,
            "video_info": video_info
        })
        
        update_process_status(process_id, "analyzing", 20, "Analyse de la vidéo")
        
        # Étape 2: Analyse (20%)
        analyzer = VideoAnalyzer(config)
        segments, analysis_report = analyzer.analyze(video_path, audio_path)
        
        # Validation et audit
        segments_hash = integrity_validator.generate_data_hash(segments)
        artifact_manager.save_file_info({
            "stage": "analysis",
            "segments": segments,
            "segments_hash": segments_hash,
            "analysis_report": analysis_report
        })
        
        update_process_status(process_id, "editing", 40, "Montage de la vidéo")
        
        # Étape 3: Montage (20%)
        editor = VideoEditor(config)
        edited_video_path = editor.edit(video_path, audio_path, segments)
        
        # Validation et audit
        edited_hash = integrity_validator.generate_file_hash(edited_video_path)
        artifact_manager.save_file_info({
            "stage": "editing",
            "edited_video_path": edited_video_path,
            "edited_hash": edited_hash
        })
        
        update_process_status(process_id, "adapting", 60, "Adaptation au format TikTok")
        
        # Étape 4: Adaptation (15%)
        adapter = FormatAdapter(config)
        tiktok_format_path = adapter.adapt(edited_video_path)
        
        # Validation et audit
        adapted_hash = integrity_validator.generate_file_hash(tiktok_format_path)
        artifact_manager.save_file_info({
            "stage": "adaptation",
            "tiktok_format_path": tiktok_format_path,
            "adapted_hash": adapted_hash
        })
        
        update_process_status(process_id, "optimizing", 75, "Optimisation pour la viralité")
        
        # Étape 5: Optimisation (15%)
        optimizer = ViralOptimizer(config)
        optimized_path, metadata = optimizer.optimize(tiktok_format_path, video_info)
        
        # Validation et audit
        optimized_hash = integrity_validator.generate_file_hash(optimized_path)
        metadata_hash = integrity_validator.generate_data_hash(metadata)
        artifact_manager.save_file_info({
            "stage": "optimization",
            "optimized_path": optimized_path,
            "optimized_hash": optimized_hash,
            "metadata": metadata,
            "metadata_hash": metadata_hash
        })
        
        # Étape 6: Publication (si demandée) (10%)
        result = {}
        if publish:
            update_process_status(process_id, "publishing", 90, "Publication sur TikTok")
            
            publisher = TikTokPublisher(config)
            result = publisher.publish(optimized_path, metadata)
            
            # Validation et audit
            artifact_manager.save_file_info({
                "stage": "publication",
                "result": result
            })
        
        # Finalisation
        end_time = time.time()
        start_time = active_processes[process_id]["started_at"]
        total_time = end_time - start_time
        
        # Génération du rapport final
        final_report = {
            "process_id": process_id,
            "url": url,
            "start_time": start_time,
            "end_time": end_time,
            "total_time": total_time,
            "output_path": str(output_path),
            "final_video": optimized_path,
            "final_hash": optimized_hash,
            "tiktok_published": publish,
            "tiktok_result": result if publish else {},
            "metadata": metadata,
            "download_url": f"/api/download/{process_id}"
        }
        
        artifact_manager.save_final_report(final_report)
        audit_logger.log_completion(final_report)
        
        # Mise à jour du statut final
        update_process_status(process_id, "completed", 100, "Conversion terminée")
        
    except Exception as e:
        logger.exception(f"Erreur lors de la conversion: {str(e)}")
        
        # Journalisation de l'erreur
        try:
            audit_logger.log_error(str(e))
        except:
            pass
        
        # Mise à jour du statut d'erreur
        active_processes[process_id]["status"] = "failed"
        active_processes[process_id]["error"] = str(e)
        active_processes[process_id]["progress"] = 100.0
        active_processes[process_id]["current_stage"] = "erreur"


def update_process_status(process_id: str, status: str, progress: float, stage: str):
    """Met à jour le statut d'un processus.
    
    Args:
        process_id: Identifiant du processus
        status: Nouveau statut
        progress: Progression (0-100)
        stage: Étape actuelle
    """
    if process_id in active_processes:
        # Vérification d'annulation
        if active_processes[process_id]["status"] == "cancelled":
            raise ValueError("Processus annulé par l'utilisateur")
        
        active_processes[process_id]["status"] = status
        active_processes[process_id]["progress"] = progress
        active_processes[process_id]["current_stage"] = stage
        
        logger.info(f"Process {process_id}: {status} ({progress:.1f}%) - {stage}")
