"""Module de journalisation pour l'audit.

Ce module est responsable de la journalisation détaillée de toutes les opérations
effectuées pendant le processus de conversion, pour assurer la traçabilité
et la transparence.
"""

import os
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from loguru import logger


class AuditLogger:
    """Classe pour la journalisation d'audit des opérations."""
    
    def __init__(self, process_id: str):
        """Initialise le journal d'audit.
        
        Args:
            process_id: Identifiant unique du processus
        """
        self.process_id = process_id
        self.start_time = time.time()
        self.logs = []
        
        # Création du dossier de logs
        self.log_dir = Path(f"data/logs/{process_id}")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier de log principal
        self.log_file = self.log_dir / "audit.log"
        self.json_log_file = self.log_dir / "audit.json"
        
        # Initialisation du journal
        self._init_log()
    
    def _init_log(self):
        """Initialise le journal d'audit avec les informations de base."""
        logger.info(f"Initialisation du journal d'audit pour le processus {self.process_id}")
        
        # Informations de base
        init_log = {
            "process_id": self.process_id,
            "start_time": self.start_time,
            "start_time_human": datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S'),
            "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
            "status": "started",
            "events": []
        }
        
        # Enregistrement initial
        self.logs.append(init_log)
        self._write_log()
        
        logger.info(f"Journal d'audit initialisé: {self.log_file}")
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Enregistre un événement dans le journal.
        
        Args:
            event_type: Type d'événement (start, download, analyze, etc.)
            details: Détails spécifiques de l'événement
        """
        event = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "type": event_type,
            "details": details
        }
        
        self.logs[0]["events"].append(event)
        self._write_log()
        
        logger.debug(f"Événement journalisé: {event_type}")
    
    def log_file_operation(self, operation: str, file_path: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Enregistre une opération sur un fichier avec génération d'empreinte.
        
        Args:
            operation: Type d'opération (create, read, update, delete)
            file_path: Chemin du fichier concerné
            metadata: Métadonnées supplémentaires
        """
        if not os.path.exists(file_path):
            logger.warning(f"Impossible de journaliser l'opération sur un fichier inexistant: {file_path}")
            file_hash = None
            file_size = None
        else:
            # Calcul de l'empreinte SHA-256 du fichier
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            file_size = os.path.getsize(file_path)
        
        details = {
            "operation": operation,
            "path": str(file_path),
            "file_hash": file_hash,
            "file_size": file_size,
            "metadata": metadata or {}
        }
        
        self.log_event(f"file_{operation}", details)
        
        logger.info(f"Opération sur fichier journalisée: {operation} - {file_path}")
    
    def log_start(self, source_url: str) -> None:
        """Enregistre le début du processus.
        
        Args:
            source_url: URL de la vidéo source
        """
        details = {
            "source_url": source_url,
            "start_time": time.time(),
            "start_time_human": datetime.now().isoformat()
        }
        
        self.log_event("process_start", details)
        
        logger.info(f"Début du processus journalisé: {source_url}")
    
    def log_completion(self, result: Dict[str, Any]) -> None:
        """Enregistre la complétion du processus.
        
        Args:
            result: Résultat du processus
        """
        end_time = time.time()
        duration = end_time - self.start_time
        
        details = {
            "result": result,
            "end_time": end_time,
            "end_time_human": datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration,
            "duration_human": self._format_duration(duration)
        }
        
        self.log_event("process_complete", details)
        
        # Mise à jour du statut global
        self.logs[0]["status"] = "completed"
        self.logs[0]["end_time"] = end_time
        self.logs[0]["duration"] = duration
        
        self._write_log()
        
        logger.info(f"Complétion du processus journalisée: durée {self._format_duration(duration)}")
    
    def log_error(self, error_message: str, details: Dict[str, Any] = None) -> None:
        """Enregistre une erreur dans le journal.
        
        Args:
            error_message: Message d'erreur
            details: Détails supplémentaires sur l'erreur
        """
        error_details = {
            "error": error_message,
            "timestamp": time.time(),
            "details": details or {}
        }
        
        self.log_event("error", error_details)
        
        # Mise à jour du statut global en cas d'erreur
        self.logs[0]["status"] = "error"
        self.logs[0]["error"] = error_message
        
        self._write_log()
        
        logger.error(f"Erreur journalisée: {error_message}")
    
    def log_validation(self, validation_type: str, is_valid: bool, 
                      details: Dict[str, Any]) -> None:
        """Enregistre un résultat de validation.
        
        Args:
            validation_type: Type de validation effectuée
            is_valid: Résultat de la validation
            details: Détails de la validation
        """
        validation_details = {
            "type": validation_type,
            "is_valid": is_valid,
            "details": details
        }
        
        self.log_event("validation", validation_details)
        
        # Si la validation a échoué, mettre à jour le statut
        if not is_valid:
            self.logs[0]["has_validation_errors"] = True
        
        self._write_log()
        
        logger.info(f"Validation {validation_type} journalisée: {'succès' if is_valid else 'échec'}")
    
    def log_transformation(self, transformation_type: str, 
                          input_path: str, output_path: str, 
                          parameters: Dict[str, Any]) -> None:
        """Enregistre une transformation de média.
        
        Args:
            transformation_type: Type de transformation
            input_path: Chemin du fichier d'entrée
            output_path: Chemin du fichier de sortie
            parameters: Paramètres de la transformation
        """
        # Calcul des empreintes des fichiers
        input_hash = self._calculate_file_hash(input_path)
        output_hash = self._calculate_file_hash(output_path)
        
        details = {
            "type": transformation_type,
            "input_path": str(input_path),
            "output_path": str(output_path),
            "input_hash": input_hash,
            "output_hash": output_hash,
            "parameters": parameters,
            "timestamp": time.time()
        }
        
        self.log_event("transformation", details)
        
        logger.info(f"Transformation {transformation_type} journalisée")
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calcule l'empreinte SHA-256 d'un fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Empreinte du fichier ou None si le fichier n'existe pas
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'empreinte: {str(e)}")
            return None
    
    def _write_log(self) -> None:
        """Écrit le journal d'audit dans les fichiers de log."""
        # Écriture du journal au format JSON
        with open(self.json_log_file, 'w') as f:
            json.dump(self.logs, f, indent=2)
        
        # Écriture du journal au format texte
        with open(self.log_file, 'w') as f:
            f.write(f"=== JOURNAL D'AUDIT ===\n")
            f.write(f"Process ID: {self.process_id}\n")
            f.write(f"Début: {datetime.fromtimestamp(self.logs[0]['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Statut: {self.logs[0]['status']}\n")
            
            if "end_time" in self.logs[0]:
                f.write(f"Fin: {datetime.fromtimestamp(self.logs[0]['end_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Durée: {self._format_duration(self.logs[0]['duration'])}\n")
            
            f.write("\n=== ÉVÉNEMENTS ===\n")
            
            for event in self.logs[0]["events"]:
                f.write(f"\n[{event['datetime']}] {event['type']}\n")
                for key, value in event["details"].items():
                    if isinstance(value, dict):
                        f.write(f"  {key}:\n")
                        for k, v in value.items():
                            f.write(f"    {k}: {v}\n")
                    elif isinstance(value, list):
                        f.write(f"  {key}:\n")
                        for item in value:
                            f.write(f"    - {item}\n")
                    else:
                        f.write(f"  {key}: {value}\n")
    
    def _format_duration(self, seconds: float) -> str:
        """Formate une durée en secondes en format lisible.
        
        Args:
            seconds: Durée en secondes
            
        Returns:
            Chaîne formatée (HH:MM:SS)
        """
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
