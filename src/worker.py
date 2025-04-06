#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module worker pour le traitement en arrière-plan.

Ce module est responsable de l'exécution des tâches de conversion
en arrière-plan, permettant un traitement asynchrone des demandes.
"""

import os
import sys
import time
import json
import signal
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import pymongo
from loguru import logger
from dotenv import load_dotenv

# Import des modules internes
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


# Chargement des variables d'environnement
load_dotenv()

# Configuration du logger
log_path = Path("data/logs")
log_path.mkdir(exist_ok=True, parents=True)
logger.add(
    log_path / "worker_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,
    diagnose=True,
)

# Créer des dossiers nécessaires
for directory in ["data", "data/temp", "data/output", "data/logs"]:
    Path(directory).mkdir(exist_ok=True, parents=True)

# Connexion à MongoDB
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/youtube_tiktok_converter")
mongo_client = pymongo.MongoClient(mongo_uri)
db = mongo_client.get_database()

# Collections
tasks_collection = db.tasks
results_collection = db.results


class Worker:
    """Classe de travailleur pour le traitement en arrière-plan."""
    
    def __init__(self):
        """Initialise le travailleur."""
        self.running = True
        self.current_task = None
        
        # Configuration de la gestion des signaux
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        logger.info("Travailleur initialisé")
    
    def handle_shutdown(self, sig, frame):
        """Gère l'arrêt propre du travailleur.
        
        Args:
            sig: Signal reçu
            frame: Frame actuelle
        """
        logger.info(f"Signal reçu ({sig}), arrêt en cours...")
        self.running = False
        
        # Si une tâche est en cours, la marquer comme interrompue
        if self.current_task:
            tasks_collection.update_one(
                {"_id": self.current_task["_id"]},
                {"$set": {"status": "interrupted", "updated_at": time.time()}}
            )
            logger.warning(f"Tâche interrompue: {self.current_task['_id']}")
        
        # Arrêter le programme
        logger.info("Travailleur arrêté")
        sys.exit(0)
    
    async def run(self):
        """Exécute la boucle principale du travailleur."""
        logger.info("Démarrage du travailleur")
        
        while self.running:
            try:
                # Recherche d'une tâche en attente
                task = tasks_collection.find_one_and_update(
                    {"status": "pending"},
                    {"$set": {"status": "processing", "updated_at": time.time(), "worker_id": os.getpid()}},
                    sort=[("priority", pymongo.DESCENDING), ("created_at", pymongo.ASCENDING)]
                )
                
                if task:
                    self.current_task = task
                    logger.info(f"Traitement de la tâche: {task['_id']}")
                    
                    # Traitement de la tâche
                    await self.process_task(task)
                    
                    # Réinitialisation de la tâche courante
                    self.current_task = None
                else:
                    # Aucune tâche en attente, attendre un peu
                    await asyncio.sleep(5)
            
            except Exception as e:
                logger.exception(f"Erreur dans la boucle principale: {str(e)}")
                await asyncio.sleep(10)  # Attendre un peu plus longtemps en cas d'erreur
    
    async def process_task(self, task: Dict[str, Any]):
        """Traite une tâche.
        
        Args:
            task: Tâche à traiter
        """
        task_id = str(task["_id"])
        process_id = task.get("process_id", task_id)
        
        try:
            # Mise à jour du statut
            self.update_task_status(task_id, "processing", 0, "Initialisation")
            
            # Extraction des paramètres
            url = task["parameters"]["url"]
            audio_quality = task["parameters"].get("audio_quality", "high")
            video_quality = task["parameters"].get("video_quality", "high")
            publish = task["parameters"].get("publish", False)
            hashtags = task["parameters"].get("hashtags", [])
            
            # Création du dossier de sortie
            output_path = Path(f"data/output/{process_id}")
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
            
            # Processus de conversion en 6 étapes
            
            # Étape 1: Acquisition et Extraction (20%)
            self.update_task_status(task_id, "processing", 5, "Téléchargement de la vidéo")
            
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
            
            # Étape 2: Analyse (20%)
            self.update_task_status(task_id, "processing", 20, "Analyse de la vidéo")
            
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
            
            # Étape 3: Montage (20%)
            self.update_task_status(task_id, "processing", 40, "Montage de la vidéo")
            
            editor = VideoEditor(config)
            edited_video_path = editor.edit(video_path, audio_path, segments)
            
            # Validation et audit
            edited_hash = integrity_validator.generate_file_hash(edited_video_path)
            artifact_manager.save_file_info({
                "stage": "editing",
                "edited_video_path": edited_video_path,
                "edited_hash": edited_hash
            })
            
            # Étape 4: Adaptation (15%)
            self.update_task_status(task_id, "processing", 60, "Adaptation au format TikTok")
            
            adapter = FormatAdapter(config)
            tiktok_format_path = adapter.adapt(edited_video_path)
            
            # Validation et audit
            adapted_hash = integrity_validator.generate_file_hash(tiktok_format_path)
            artifact_manager.save_file_info({
                "stage": "adaptation",
                "tiktok_format_path": tiktok_format_path,
                "adapted_hash": adapted_hash
            })
            
            # Étape 5: Optimisation (15%)
            self.update_task_status(task_id, "processing", 75, "Optimisation pour la viralité")
            
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
                self.update_task_status(task_id, "processing", 90, "Publication sur TikTok")
                
                publisher = TikTokPublisher(config)
                result = publisher.publish(optimized_path, metadata)
                
                # Validation et audit
                artifact_manager.save_file_info({
                    "stage": "publication",
                    "result": result
                })
            
            # Finalisation
            end_time = time.time()
            start_time = task["created_at"]
            total_time = end_time - start_time
            
            # Génération du rapport final
            final_report = {
                "process_id": process_id,
                "task_id": task_id,
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
            
            # Sauvegarde du rapport
            artifact_manager.save_final_report(final_report)
            audit_logger.log_completion(final_report)
            
            # Sauvegarde du résultat dans MongoDB
            results_collection.insert_one({
                "task_id": task_id,
                "process_id": process_id,
                "created_at": time.time(),
                "url": url,
                "output_path": str(output_path),
                "final_video": optimized_path,
                "tiktok_published": publish,
                "tiktok_result": result if publish else {},
                "report": final_report
            })
            
            # Mise à jour du statut de la tâche
            self.update_task_status(task_id, "completed", 100, "Conversion terminée")
            
            logger.info(f"Tâche {task_id} terminée avec succès")
            
        except Exception as e:
            logger.exception(f"Erreur lors du traitement de la tâche {task_id}: {str(e)}")
            
            # Journalisation de l'erreur
            try:
                audit_logger = AuditLogger(process_id)
                audit_logger.log_error(str(e))
            except:
                pass
            
            # Mise à jour du statut de la tâche
            self.update_task_status(task_id, "failed", 100, f"Erreur: {str(e)}")
    
    def update_task_status(self, task_id: str, status: str, progress: float, message: str):
        """Met à jour le statut d'une tâche.
        
        Args:
            task_id: Identifiant de la tâche
            status: Nouveau statut
            progress: Progression (0-100)
            message: Message d'information
        """
        tasks_collection.update_one(
            {"_id": task_id},
            {
                "$set": {
                    "status": status,
                    "progress": progress,
                    "message": message,
                    "updated_at": time.time()
                }
            }
        )
        
        logger.info(f"Tâche {task_id}: {status} ({progress:.1f}%) - {message}")


async def create_task(url: str, audio_quality: str = "high", video_quality: str = "high",
                     publish: bool = False, hashtags: List[str] = None,
                     priority: int = 0) -> Dict[str, Any]:
    """Crée une nouvelle tâche de conversion.
    
    Args:
        url: URL de la vidéo YouTube
        audio_quality: Qualité audio (low, medium, high)
        video_quality: Qualité vidéo (low, medium, high)
        publish: Publier directement sur TikTok
        hashtags: Hashtags à ajouter
        priority: Priorité de la tâche (0 = normale, >0 = plus haute)
        
    Returns:
        Tâche créée
    """
    # Génération d'un identifiant unique pour le processus
    process_id = f"task_{int(time.time())}_{hash(url) % 10000:04d}"
    
    # Création de la tâche
    task = {
        "_id": process_id,
        "process_id": process_id,
        "status": "pending",
        "progress": 0,
        "message": "En attente de traitement",
        "parameters": {
            "url": url,
            "audio_quality": audio_quality,
            "video_quality": video_quality,
            "publish": publish,
            "hashtags": hashtags or []
        },
        "priority": priority,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    
    # Insertion dans la base de données
    tasks_collection.insert_one(task)
    
    logger.info(f"Tâche créée: {process_id}")
    return task


async def main():
    """Fonction principale."""
    # Création du travailleur
    worker = Worker()
    
    # Exécution du travailleur
    await worker.run()


if __name__ == "__main__":
    # Exécution du travailleur
    asyncio.run(main())
