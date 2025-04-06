"""Module de gestion des artefacts.

Ce module est responsable de la sauvegarde et de la gestion des artefacts
générés pendant le processus de conversion, avec traçabilité complète.
"""

import os
import json
import time
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from loguru import logger
import boto3
from botocore.exceptions import ClientError


class ArtifactManager:
    """Classe pour gérer les artefacts générés pendant le processus."""
    
    def __init__(self, process_id: str, output_dir: str):
        """Initialise le gestionnaire d'artefacts.
        
        Args:
            process_id: Identifiant unique du processus
            output_dir: Répertoire de sortie pour les artefacts
        """
        self.process_id = process_id
        self.output_dir = Path(output_dir)
        
        # Création du répertoire de sortie
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier de manifeste pour les artefacts
        self.manifest_file = self.output_dir / "artifacts_manifest.json"
        
        # Initialisation du manifeste
        self.manifest = {
            "process_id": process_id,
            "creation_time": time.time(),
            "creation_time_human": datetime.now().isoformat(),
            "artifacts": []
        }
        
        # Sauvegarde du manifeste initial
        self._save_manifest()
        
        logger.info(f"Gestionnaire d'artefacts initialisé pour le processus {process_id}")
    
    def save_file_info(self, artifact_info: Dict[str, Any]) -> None:
        """Enregistre les informations sur un artefact.
        
        Args:
            artifact_info: Informations sur l'artefact
        """
        # Ajout du timestamp
        artifact_info["timestamp"] = time.time()
        artifact_info["datetime"] = datetime.now().isoformat()
        
        # Identification de l'artefact
        stage = artifact_info.get("stage", "unknown")
        artifact_id = f"{stage}_{int(time.time())}"
        
        # Calcul des empreintes pour les chemins de fichiers
        for key, value in artifact_info.items():
            if isinstance(value, str) and os.path.exists(value) and os.path.isfile(value):
                # Calcul de l'empreinte SHA-256 du fichier
                try:
                    with open(value, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    
                    # Ajout des informations sur le fichier
                    file_info = {
                        "path": value,
                        "hash": file_hash,
                        "size": os.path.getsize(value),
                        "hash_algorithm": "sha256"
                    }
                    
                    # Remplacement de la valeur par les informations détaillées
                    artifact_info[f"{key}_info"] = file_info
                except Exception as e:
                    logger.warning(f"Impossible de calculer l'empreinte pour {value}: {str(e)}")
        
        # Ajout au manifeste
        artifact_entry = {
            "id": artifact_id,
            "stage": stage,
            "timestamp": artifact_info["timestamp"],
            "datetime": artifact_info["datetime"],
            "info": artifact_info
        }
        
        self.manifest["artifacts"].append(artifact_entry)
        
        # Sauvegarde du manifeste
        self._save_manifest()
        
        logger.info(f"Informations sur l'artefact enregistrées: {stage}")
    
    def copy_artifact(self, source_path: str, target_name: Optional[str] = None) -> str:
        """Copie un artefact dans le répertoire de sortie.
        
        Args:
            source_path: Chemin du fichier source
            target_name: Nom du fichier de destination (optionnel)
            
        Returns:
            Chemin du fichier copié
        
        Raises:
            ValueError: Si le fichier source n'existe pas
        """
        if not os.path.exists(source_path):
            error_msg = f"Le fichier source n'existe pas: {source_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Détermination du nom de fichier de destination
            if target_name is None:
                target_name = os.path.basename(source_path)
            
            # Chemin complet de destination
            target_path = self.output_dir / target_name
            
            # Copie du fichier
            shutil.copy2(source_path, target_path)
            
            # Enregistrement des informations sur l'artefact
            with open(source_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            artifact_info = {
                "stage": "artifact_copy",
                "source_path": source_path,
                "target_path": str(target_path),
                "hash": file_hash,
                "size": os.path.getsize(source_path)
            }
            
            self.save_file_info(artifact_info)
            
            logger.info(f"Artefact copié: {source_path} -> {target_path}")
            return str(target_path)
            
        except Exception as e:
            error_msg = f"Erreur lors de la copie de l'artefact: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def save_final_report(self, report_data: Dict[str, Any]) -> str:
        """Sauvegarde le rapport final du processus.
        
        Args:
            report_data: Données du rapport
            
        Returns:
            Chemin du fichier de rapport
        """
        logger.info("Sauvegarde du rapport final")
        
        # Chemin du fichier de rapport
        report_file = self.output_dir / "final_report.json"
        
        # Ajout des informations de traçabilité
        report_data["manifest_file"] = str(self.manifest_file)
        report_data["saved_at"] = time.time()
        report_data["saved_at_human"] = datetime.now().isoformat()
        
        # Génération d'une empreinte pour le rapport
        report_hash = hashlib.sha256(json.dumps(report_data, sort_keys=True).encode('utf-8')).hexdigest()
        report_data["report_hash"] = report_hash
        
        # Sauvegarde du rapport
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Sauvegarde d'une copie dans le manifeste
        self.manifest["final_report"] = report_data
        self.manifest["final_report_hash"] = report_hash
        self._save_manifest()
        
        logger.info(f"Rapport final sauvegardé: {report_file}")
        return str(report_file)
    
    def archive_artifacts(self, archive_name: Optional[str] = None) -> str:
        """Archive tous les artefacts dans un fichier zip.
        
        Args:
            archive_name: Nom de l'archive (optionnel)
            
        Returns:
            Chemin de l'archive
        """
        import zipfile
        
        logger.info("Archivage des artefacts")
        
        # Détermination du nom de l'archive
        if archive_name is None:
            archive_name = f"artifacts_{self.process_id}_{int(time.time())}.zip"
        
        # Chemin complet de l'archive
        archive_path = self.output_dir / archive_name
        
        try:
            # Création de l'archive
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Ajout du manifeste
                zipf.write(self.manifest_file, arcname=os.path.basename(self.manifest_file))
                
                # Parcours des artefacts et ajout à l'archive
                for artifact in self.manifest["artifacts"]:
                    info = artifact["info"]
                    
                    # Recherche des chemins de fichiers
                    for key, value in info.items():
                        if isinstance(value, str) and os.path.exists(value) and os.path.isfile(value):
                            # Ajout du fichier à l'archive
                            try:
                                zipf.write(value, arcname=os.path.basename(value))
                                logger.debug(f"Fichier ajouté à l'archive: {value}")
                            except Exception as e:
                                logger.warning(f"Impossible d'ajouter {value} à l'archive: {str(e)}")
            
            # Calcul de l'empreinte de l'archive
            with open(archive_path, 'rb') as f:
                archive_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Enregistrement des informations sur l'archive
            archive_info = {
                "stage": "artifacts_archive",
                "archive_path": str(archive_path),
                "archive_hash": archive_hash,
                "archive_size": os.path.getsize(archive_path),
                "artifact_count": len(self.manifest["artifacts"])
            }
            
            self.save_file_info(archive_info)
            
            logger.info(f"Artefacts archivés: {archive_path}")
            return str(archive_path)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'archivage des artefacts: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def upload_to_s3(self, file_path: str, bucket_name: str, 
                    object_key: Optional[str] = None, 
                    aws_access_key: Optional[str] = None,
                    aws_secret_key: Optional[str] = None) -> Dict[str, Any]:
        """Télécharge un artefact vers Amazon S3.
        
        Args:
            file_path: Chemin du fichier à télécharger
            bucket_name: Nom du bucket S3
            object_key: Clé de l'objet dans S3 (optionnel)
            aws_access_key: Clé d'accès AWS (optionnel)
            aws_secret_key: Clé secrète AWS (optionnel)
            
        Returns:
            Informations sur le téléchargement
        
        Raises:
            ValueError: Si le fichier n'existe pas ou en cas d'erreur de téléchargement
        """
        if not os.path.exists(file_path):
            error_msg = f"Le fichier à télécharger n'existe pas: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Détermination de la clé de l'objet
            if object_key is None:
                object_key = f"{self.process_id}/{os.path.basename(file_path)}"
            
            # Création du client S3
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            
            # Téléchargement du fichier
            s3_client.upload_file(file_path, bucket_name, object_key)
            
            # Génération de l'URL de l'objet
            object_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"
            
            # Enregistrement des informations sur le téléchargement
            upload_info = {
                "stage": "s3_upload",
                "file_path": file_path,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "object_url": object_url,
                "file_size": os.path.getsize(file_path)
            }
            
            self.save_file_info(upload_info)
            
            logger.info(f"Fichier téléchargé vers S3: {object_url}")
            return upload_info
            
        except ClientError as e:
            error_msg = f"Erreur AWS lors du téléchargement: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"Erreur lors du téléchargement vers S3: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _save_manifest(self) -> None:
        """Sauvegarde le manifeste des artefacts."""
        with open(self.manifest_file, 'w') as f:
            json.dump(self.manifest, f, indent=2)
