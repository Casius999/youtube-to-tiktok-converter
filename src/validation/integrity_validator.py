"""Module de validation d'intégrité.

Ce module est responsable de la validation de l'intégrité des fichiers
et des processus pour garantir l'authenticité et la traçabilité.
"""

import os
import json
import time
import hashlib
import hmac
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from loguru import logger


class IntegrityValidator:
    """Classe pour valider l'intégrité des fichiers et processus."""
    
    def __init__(self, process_id: str):
        """Initialise le validateur d'intégrité.
        
        Args:
            process_id: Identifiant unique du processus
        """
        self.process_id = process_id
        
        # Création du dossier pour les rapports de validation
        self.validation_dir = Path(f"data/logs/{process_id}/validation")
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier de rapport principal
        self.report_file = self.validation_dir / "integrity_report.json"
        
        # Initialisation du rapport
        self.report = {
            "process_id": process_id,
            "timestamp": time.time(),
            "validations": []
        }
    
    def generate_file_hash(self, file_path: str) -> str:
        """Génère une empreinte SHA-256 pour un fichier.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Empreinte SHA-256 du fichier
        
        Raises:
            ValueError: Si le fichier n'existe pas ou n'est pas accessible
        """
        if not os.path.exists(file_path):
            error_msg = f"Le fichier n'existe pas: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Calcul de l'empreinte SHA-256
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Enregistrement de la validation
            self._record_validation("file_hash", {
                "file_path": file_path,
                "hash": file_hash,
                "algorithm": "sha256",
                "file_size": os.path.getsize(file_path)
            })
            
            logger.debug(f"Empreinte générée pour {file_path}: {file_hash}")
            return file_hash
            
        except Exception as e:
            error_msg = f"Erreur lors du calcul de l'empreinte: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def generate_data_hash(self, data: Any) -> str:
        """Génère une empreinte SHA-256 pour des données.
        
        Args:
            data: Données à hacher (sérialisables en JSON)
            
        Returns:
            Empreinte SHA-256 des données
        """
        try:
            # Sérialisation des données en JSON
            json_data = json.dumps(data, sort_keys=True)
            
            # Calcul de l'empreinte SHA-256
            data_hash = hashlib.sha256(json_data.encode('utf-8')).hexdigest()
            
            # Enregistrement de la validation
            self._record_validation("data_hash", {
                "hash": data_hash,
                "algorithm": "sha256",
                "data_type": type(data).__name__
            })
            
            logger.debug(f"Empreinte générée pour données: {data_hash}")
            return data_hash
            
        except Exception as e:
            error_msg = f"Erreur lors du calcul de l'empreinte des données: {str(e)}"
            logger.error(error_msg)
            return hashlib.sha256(str(data).encode('utf-8')).hexdigest()
    
    def validate_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Valide l'intégrité d'un fichier en comparant son empreinte.
        
        Args:
            file_path: Chemin du fichier à valider
            expected_hash: Empreinte attendue
            
        Returns:
            True si l'intégrité est validée, False sinon
        """
        try:
            # Calcul de l'empreinte actuelle
            current_hash = self.generate_file_hash(file_path)
            
            # Comparaison avec l'empreinte attendue
            is_valid = current_hash == expected_hash
            
            # Enregistrement de la validation
            self._record_validation("file_integrity", {
                "file_path": file_path,
                "expected_hash": expected_hash,
                "current_hash": current_hash,
                "is_valid": is_valid
            })
            
            if is_valid:
                logger.info(f"Intégrité validée pour {file_path}")
            else:
                logger.warning(f"Échec de validation d'intégrité pour {file_path}")
            
            return is_valid
            
        except Exception as e:
            error_msg = f"Erreur lors de la validation d'intégrité: {str(e)}"
            logger.error(error_msg)
            
            # Enregistrement de l'erreur
            self._record_validation("file_integrity_error", {
                "file_path": file_path,
                "expected_hash": expected_hash,
                "error": str(e)
            })
            
            return False
    
    def validate_process_chain(self, chain_data: List[Dict[str, Any]]) -> bool:
        """Valide l'intégrité d'une chaîne de processus.
        
        Args:
            chain_data: Liste des données de processus à valider
            
        Returns:
            True si la chaîne est valide, False sinon
        """
        if not chain_data:
            logger.warning("Chaîne de processus vide")
            return False
        
        try:
            # Vérification de la chaîne d'intégrité
            is_valid = True
            previous_hash = None
            validation_results = []
            
            for i, data in enumerate(chain_data):
                # Vérification que chaque élément possède les champs requis
                if not all(k in data for k in ["stage", "timestamp", "data_hash"]):
                    logger.warning(f"Élément {i} de la chaîne incomplet")
                    is_valid = False
                    validation_results.append({
                        "index": i,
                        "is_valid": False,
                        "error": "Champs manquants"
                    })
                    continue
                
                # Recalcul de l'empreinte des données
                if "data" in data:
                    calculated_hash = self.generate_data_hash(data["data"])
                    hash_valid = calculated_hash == data["data_hash"]
                    
                    if not hash_valid:
                        logger.warning(f"Incohérence d'empreinte à l'étape {i}")
                        is_valid = False
                else:
                    # Si les données ne sont pas présentes, on ne peut pas valider l'empreinte
                    hash_valid = None
                
                # Vérification de la référence à l'empreinte précédente
                if previous_hash is not None and "previous_hash" in data:
                    prev_hash_valid = data["previous_hash"] == previous_hash
                    
                    if not prev_hash_valid:
                        logger.warning(f"Rupture de la chaîne à l'étape {i}")
                        is_valid = False
                else:
                    prev_hash_valid = None
                
                # Mise à jour de l'empreinte précédente
                previous_hash = data["data_hash"]
                
                # Enregistrement du résultat de validation pour cet élément
                validation_results.append({
                    "index": i,
                    "stage": data["stage"],
                    "timestamp": data["timestamp"],
                    "hash_valid": hash_valid,
                    "prev_hash_valid": prev_hash_valid,
                    "is_valid": hash_valid is not False and prev_hash_valid is not False
                })
            
            # Enregistrement de la validation
            self._record_validation("process_chain", {
                "is_valid": is_valid,
                "chain_length": len(chain_data),
                "results": validation_results
            })
            
            if is_valid:
                logger.info(f"Chaîne de processus validée ({len(chain_data)} étapes)")
            else:
                logger.warning(f"Échec de validation de la chaîne de processus")
            
            return is_valid
            
        except Exception as e:
            error_msg = f"Erreur lors de la validation de la chaîne: {str(e)}"
            logger.error(error_msg)
            
            # Enregistrement de l'erreur
            self._record_validation("process_chain_error", {
                "error": str(e)
            })
            
            return False
    
    def create_integrity_signature(self, data: Any, secret_key: str) -> str:
        """Crée une signature HMAC pour des données.
        
        Args:
            data: Données à signer
            secret_key: Clé secrète pour la signature
            
        Returns:
            Signature HMAC hexadécimale
        """
        try:
            # Sérialisation des données en JSON
            json_data = json.dumps(data, sort_keys=True)
            
            # Création de la signature HMAC
            signature = hmac.new(
                secret_key.encode('utf-8'),
                json_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Enregistrement de la validation (sans la clé secrète)
            self._record_validation("integrity_signature", {
                "signature": signature,
                "algorithm": "hmac-sha256",
                "data_type": type(data).__name__
            })
            
            logger.debug(f"Signature générée: {signature}")
            return signature
            
        except Exception as e:
            error_msg = f"Erreur lors de la création de la signature: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def verify_integrity_signature(self, data: Any, signature: str, secret_key: str) -> bool:
        """Vérifie une signature HMAC pour des données.
        
        Args:
            data: Données à vérifier
            signature: Signature à vérifier
            secret_key: Clé secrète utilisée pour la signature
            
        Returns:
            True si la signature est valide, False sinon
        """
        try:
            # Création d'une nouvelle signature
            new_signature = self.create_integrity_signature(data, secret_key)
            
            # Comparaison des signatures
            is_valid = hmac.compare_digest(new_signature, signature)
            
            # Enregistrement de la validation
            self._record_validation("signature_verification", {
                "is_valid": is_valid,
                "algorithm": "hmac-sha256",
                "data_type": type(data).__name__
            })
            
            if is_valid:
                logger.info(f"Signature valide")
            else:
                logger.warning(f"Signature invalide")
            
            return is_valid
            
        except Exception as e:
            error_msg = f"Erreur lors de la vérification de la signature: {str(e)}"
            logger.error(error_msg)
            
            # Enregistrement de l'erreur
            self._record_validation("signature_verification_error", {
                "error": str(e)
            })
            
            return False
    
    def generate_full_report(self) -> Dict[str, Any]:
        """Génère un rapport complet de toutes les validations.
        
        Returns:
            Rapport d'intégrité complet
        """
        logger.info("Génération du rapport d'intégrité complet")
        
        # Mise à jour du timestamp
        self.report["generated_at"] = time.time()
        
        # Statistiques de validation
        total_validations = len(self.report["validations"])
        successful_validations = sum(
            1 for v in self.report["validations"] 
            if "is_valid" in v["details"] and v["details"]["is_valid"]
        )
        
        self.report["statistics"] = {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0
        }
        
        # Sauvegarde du rapport
        self._save_report()
        
        logger.info(f"Rapport d'intégrité généré: {self.report_file}")
        return self.report
    
    def _record_validation(self, validation_type: str, details: Dict[str, Any]) -> None:
        """Enregistre une validation dans le rapport.
        
        Args:
            validation_type: Type de validation
            details: Détails de la validation
        """
        validation = {
            "timestamp": time.time(),
            "type": validation_type,
            "details": details
        }
        
        # Ajout au rapport
        self.report["validations"].append(validation)
        
        # Sauvegarde périodique du rapport
        if len(self.report["validations"]) % 10 == 0:
            self._save_report()
    
    def _save_report(self) -> None:
        """Sauvegarde le rapport d'intégrité dans un fichier JSON."""
        with open(self.report_file, 'w') as f:
            json.dump(self.report, f, indent=2)
