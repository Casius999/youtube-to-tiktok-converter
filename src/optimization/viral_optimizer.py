"""Module d'optimisation pour la viralité.

Ce module est responsable de l'optimisation des vidéos pour maximiser
leur potentiel viral sur TikTok, incluant les effets visuels, les hashtags
et les métadonnées.
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any

import ffmpeg
import numpy as np
from loguru import logger
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx

from src.utils.config import Config


class ViralOptimizer:
    """Classe pour optimiser les vidéos pour la viralité sur TikTok."""
    
    def __init__(self, config: Config):
        """Initialise l'optimiseur viral avec la configuration.
        
        Args:
            config: Configuration de l'application
        """
        self.config = config
        self.process_id = config.process_id
        
        # Préparation des ressources pour l'optimisation
        self.trending_hashtags = self._load_trending_hashtags()
        self.effect_templates = self._load_effect_templates()
    
    def _load_trending_hashtags(self) -> List[str]:
        """Charge les hashtags tendance pour TikTok.
        
        Returns:
            Liste des hashtags populaires
        """
        # Dans une implémentation réelle, ces hashtags seraient récupérés via une API
        # Simulation pour l'exemple
        return [
            "fyp", "foryoupage", "viral", "trending", "tiktok", "viralvideo",
            "foryou", "explore", "trending", "comedy", "funny", "meme", "challenge",
            "dance", "music", "song", "duet", "xyzbca", "tiktokviral", "trend",
            "trendingnow", "viraltrend", "creative", "transformation", "satisfying",
            "aesthetic", "relaxing", "motivation", "inspiration", "lifehack"
        ]
    
    def _load_effect_templates(self) -> List[Dict[str, Any]]:
        """Charge les templates d'effets viraux pour TikTok.
        
        Returns:
            Liste des templates d'effets disponibles
        """
        # Dans une implémentation réelle, ces effets seraient chargés depuis une base de données
        # Simulation pour l'exemple
        return [
            {
                "name": "trending_overlay",
                "type": "text",
                "text": "WATCH TILL THE END 🔥",
                "position": "top",
                "duration": 3.0,
                "color": "white",
                "font_size": 40
            },
            {
                "name": "caption_overlay",
                "type": "text",
                "text": "POV: When you finally see it...",
                "position": "bottom",
                "duration": 4.0,
                "color": "white",
                "font_size": 36
            },
            {
                "name": "zoom_effect",
                "type": "zoom",
                "start_time": 0.3,
                "duration": 1.0,
                "zoom_factor": 1.2
            },
            {
                "name": "flash_effect",
                "type": "flash",
                "start_time": 0.5,
                "duration": 0.2,
                "intensity": 0.5
            },
            {
                "name": "shake_effect",
                "type": "shake",
                "start_time": 1.0,
                "duration": 0.5,
                "intensity": 5.0
            }
        ]
    
    def optimize(self, input_path: str, video_info: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Optimise une vidéo pour maximiser sa viralité sur TikTok.
        
        Args:
            input_path: Chemin vers la vidéo à optimiser
            video_info: Informations sur la vidéo d'origine
            
        Returns:
            Tuple contenant (chemin_vidéo_optimisée, métadonnées)
        """
        logger.info(f"Optimisation pour la viralité: {input_path}")
        
        # 1. Création des métadonnées virales (titre, description, hashtags)
        metadata = self._generate_viral_metadata(video_info)
        
        # 2. Application des effets viraux à la vidéo
        optimized_path = self._apply_viral_effects(input_path, metadata)
        
        # 3. Finalisation et validation des optimisations
        final_metadata = self._finalize_optimization(optimized_path, metadata)
        
        # Sauvegarde des métadonnées dans un fichier JSON
        metadata_path = self.config.get_output_file_path("metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(final_metadata, f, indent=2)
        
        logger.info(f"Optimisation terminée: {optimized_path}")
        return optimized_path, final_metadata
    
    def _generate_viral_metadata(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des métadonnées optimisées pour la viralité.
        
        Args:
            video_info: Informations sur la vidéo d'origine
            
        Returns:
            Métadonnées optimisées pour TikTok
        """
        logger.info("Génération des métadonnées virales")
        
        # Extraction des informations pertinentes de la vidéo d'origine
        original_title = video_info.get("title", "")
        original_keywords = video_info.get("keywords", [])
        original_description = video_info.get("description", "")
        
        # Extraction de mots-clés pertinents du titre et de la description
        relevant_words = self._extract_relevant_words(
            original_title + " " + original_description
        )
        
        # Génération d'un titre accrocheur pour TikTok
        title_templates = [
            "😱 You won't believe what happens when {}",
            "This is why {} will blow your mind",
            "POV: When {} changes everything",
            "I tried {} and this happened...",
            "The truth about {} they don't want you to know",
            "Wait for it... {} 🔥",
            "How {} broke the internet",
            "When {} goes viral"
        ]
        
        # Sélection d'un modèle de titre et remplacement
        title_template = random.choice(title_templates)
        if relevant_words:
            viral_title = title_template.format(random.choice(relevant_words))
        else:
            # Si pas de mots pertinents, simplification du titre
            words = original_title.split(" ")
            if len(words) > 3:
                simple_subject = " ".join(words[:3])
            else:
                simple_subject = original_title if original_title else "this"
            viral_title = title_template.format(simple_subject)
        
        # Sélection de hashtags pertinents
        # Combiner les hashtags spécifiés par l'utilisateur avec des tendances
        user_hashtags = self.config.hashtags
        num_trending = min(8, 15 - len(user_hashtags))  # Maximum ~15 hashtags au total
        
        # Ajouter des hashtags pertinents basés sur les mots-clés d'origine
        relevant_hashtags = []
        for keyword in original_keywords:
            # Transformer le mot-clé en hashtag (sans espaces, sans caractères spéciaux)
            hashtag = "#" + "".join(c for c in keyword if c.isalnum()).lower()
            if len(hashtag) > 1 and hashtag not in relevant_hashtags:
                relevant_hashtags.append(hashtag)
        
        # Compléter avec des hashtags tendance
        trending_selection = random.sample(self.trending_hashtags, num_trending)
        
        # Compilation des hashtags
        hashtags = [
            *["#" + tag if not tag.startswith("#") else tag for tag in user_hashtags],
            *relevant_hashtags[:5],  # Limiter à 5 hashtags pertinents max
            *["#" + tag if not tag.startswith("#") else tag for tag in trending_selection]
        ]
        
        # Élimination des doublons tout en préservant l'ordre
        unique_hashtags = []
        for tag in hashtags:
            if tag not in unique_hashtags:
                unique_hashtags.append(tag)
        
        # Génération d'une description engageante
        description_templates = [
            "🤯 {title} | Comment if you agree! | {hashtags}",
            "Wait for it... 👀 | {title} | {hashtags}",
            "You asked for it, here it is! | {title} | {hashtags}",
            "POV: {title} | Drop a ❤️ if you relate! | {hashtags}",
            "This changed everything! | {title} | {hashtags}",
            "Watch till the end! 🔥 | {title} | {hashtags}"
        ]
        
        description_template = random.choice(description_templates)
        viral_description = description_template.format(
            title=viral_title,
            hashtags=" ".join(unique_hashtags[:15])  # Limiter à ~15 hashtags
        )
        
        # Compilation des métadonnées
        metadata = {
            "title": viral_title,
            "description": viral_description,
            "hashtags": unique_hashtags,
            "original_info": {
                "title": original_title,
                "keywords": original_keywords
            }
        }
        
        logger.info(f"Métadonnées générées: {viral_title}")
        return metadata
    
    def _extract_relevant_words(self, text: str) -> List[str]:
        """Extrait des mots-clés pertinents d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste des mots-clés pertinents
        """
        # Dans une implémentation réelle, utiliser NLP pour l'extraction de concepts
        # Simulation simplifiée pour l'exemple
        
        # Nettoyage du texte
        clean_text = "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text)
        words = clean_text.split()
        
        # Filtrage des mots courts et des mots vides
        stopwords = ["the", "and", "a", "to", "of", "in", "is", "it", "you", "that", "was", "for",
                    "on", "are", "with", "as", "this", "be", "at", "by", "an", "not", "we", "i"]
        
        filtered_words = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Extraction des phrases pertinentes (groupes de 2-3 mots)
        phrases = []
        if len(filtered_words) >= 3:
            for i in range(len(filtered_words) - 2):
                phrase = " ".join(filtered_words[i:i+3])
                if len(phrase) < 30:  # Limite de longueur
                    phrases.append(phrase)
        
        if len(filtered_words) >= 2:
            for i in range(len(filtered_words) - 1):
                phrase = " ".join(filtered_words[i:i+2])
                if len(phrase) < 25:  # Limite de longueur
                    phrases.append(phrase)
        
        # Si pas assez de phrases, utiliser des mots individuels
        if len(phrases) < 5 and filtered_words:
            phrases.extend(filtered_words[:10])
        
        # Dédupliquer et limiter le nombre
        unique_phrases = list(set(phrases))
        return unique_phrases[:10]  # Retourner max 10 phrases
    
    def _apply_viral_effects(self, input_path: str, metadata: Dict[str, Any]) -> str:
        """Applique des effets viraux à la vidéo.
        
        Args:
            input_path: Chemin vers la vidéo d'entrée
            metadata: Métadonnées générées
            
        Returns:
            Chemin vers la vidéo avec effets
        """
        logger.info(f"Application des effets viraux à la vidéo: {input_path}")
        
        # Chemin de sortie pour la vidéo optimisée
        output_path = self.config.get_output_file_path("optimized.mp4")
        
        try:
            # Chargement de la vidéo avec MoviePy
            video = VideoFileClip(input_path)
            duration = video.duration
            
            # 1. Sélection aléatoire d'effets à appliquer
            # Limiter le nombre d'effets pour ne pas surcharger la vidéo
            num_effects = min(3, len(self.effect_templates))
            selected_effects = random.sample(self.effect_templates, num_effects)
            
            # 2. Création des éléments d'overlay
            overlays = []
            
            for effect in selected_effects:
                effect_type = effect["type"]
                
                # Effets de texte (overlay)
                if effect_type == "text":
                    # Création du clip texte
                    txt_clip = TextClip(
                        effect["text"],
                        fontsize=effect["font_size"],
                        color=effect["color"],
                        stroke_color="black",
                        stroke_width=1,
                        font="Arial-Bold"
                    )
                    
                    txt_clip = txt_clip.set_duration(min(effect["duration"], duration))
                    
                    # Positionnement du texte
                    if effect["position"] == "top":
                        txt_clip = txt_clip.margin(bottom=10, opacity=0).set_position(("center", 0.1))
                    elif effect["position"] == "bottom":
                        txt_clip = txt_clip.margin(top=10, opacity=0).set_position(("center", 0.8))
                    else:  # center
                        txt_clip = txt_clip.set_position("center")
                    
                    overlays.append(txt_clip)
                
                # Effets de zoom
                elif effect_type == "zoom" and effect["start_time"] < duration:
                    # Détermination de la plage temporelle pour l'effet
                    start_time = effect["start_time"]
                    effect_duration = min(effect["duration"], duration - start_time)
                    end_time = start_time + effect_duration
                    
                    # Création d'un sous-clip pour l'effet de zoom
                    if effect_duration > 0:
                        # Application du zoom
                        zoom_factor = effect["zoom_factor"]
                        zoomed_clip = (
                            video.subclip(start_time, end_time)
                            .fx(vfx.resize, zoom_factor)
                            .set_position("center")
                        )
                        
                        # Remplacement du segment original par le segment zoomé
                        video = video.subclip(0, start_time)
                        video = video.set_duration(duration)
                        overlays.append(zoomed_clip.set_start(start_time))
                
                # Autres effets (flash, shake, etc.)
                # Pour une implémentation complète, ajouter ici
            
            # 3. Composition de la vidéo finale avec les overlays
            if overlays:
                final_video = CompositeVideoClip([video] + overlays)
            else:
                final_video = video
            
            # 4. Ajout d'un texte avec un hashtag aléatoire pour renforcer l'identité
            if metadata["hashtags"]:
                random_hashtag = random.choice(metadata["hashtags"])
                hashtag_clip = (
                    TextClip(
                        random_hashtag,
                        fontsize=24,
                        color="white",
                        stroke_color="black",
                        stroke_width=1,
                        font="Arial-Bold"
                    )
                    .set_duration(min(5.0, duration))
                    .margin(bottom=10, opacity=0)
                    .set_position(("right", 0.95))
                )
                final_video = CompositeVideoClip([final_video, hashtag_clip])
            
            # 5. Écriture de la vidéo finale
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-pix_fmt", "yuv420p"],
                verbose=False,
                logger=None
            )
            
            # Fermeture des clips
            final_video.close()
            video.close()
            for clip in overlays:
                clip.close()
            
            logger.info(f"Effets viraux appliqués: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application des effets viraux: {str(e)}")
            # En cas d'erreur, on retourne la vidéo d'entrée
            return input_path
    
    def _finalize_optimization(self, video_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Finalise l'optimisation et complète les métadonnées.
        
        Args:
            video_path: Chemin vers la vidéo optimisée
            metadata: Métadonnées générées
            
        Returns:
            Métadonnées complétées et validées
        """
        logger.info("Finalisation de l'optimisation")
        
        # Extraction des métadonnées de la vidéo optimisée
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            if video_stream:
                # Mise à jour des métadonnées avec les informations techniques
                metadata.update({
                    "video_info": {
                        "width": int(video_stream.get("width", 0)),
                        "height": int(video_stream.get("height", 0)),
                        "duration": float(probe.get("format", {}).get("duration", 0)),
                        "bitrate": int(probe.get("format", {}).get("bit_rate", 0)) // 1000,
                        "codec": video_stream.get("codec_name", ""),
                        "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                        "audio_codec": audio_stream.get("codec_name", "") if audio_stream else None,
                        "audio_bitrate": int(audio_stream.get("bit_rate", 0)) // 1000 if audio_stream else 0
                    },
                    "tiktok_ready": True,
                    "optimization_timestamp": str(pd.Timestamp.now()),
                    "optimized_path": video_path
                })
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation des métadonnées: {str(e)}")
            # En cas d'erreur, ajout d'informations minimales
            metadata.update({
                "tiktok_ready": True,
                "optimization_timestamp": str(pd.Timestamp.now()),
                "optimized_path": video_path,
                "error": str(e)
            })
        
        return metadata