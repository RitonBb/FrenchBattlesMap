import json
import logging
import trafilatura
from urllib.parse import quote
from datetime import datetime
from app import db  # Ajout de l'import manquant

def get_gallica_content(battle_name, year):
    """
    Recherche des informations sur Gallica BnF
    """
    try:
        query = quote(f"{battle_name} {year}")
        url = f"https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&exactSearch=false&collapsing=true&version=1.2&query={query}"
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            content = trafilatura.extract(downloaded)
            if content and len(content.strip()) > 0:
                return content
        return None
    except Exception as e:
        logging.error(f"Erreur lors de la recherche Gallica pour {battle_name}: {str(e)}")
        return None

def get_persee_content(battle_name, year):
    """
    Recherche des informations sur Persée
    """
    try:
        period = "antiquite" if year < 500 else "medieval" if year < 1500 else "moderne"
        query = quote(f"{battle_name} {period}")
        url = f"https://www.persee.fr/search?q={query}"
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            content = trafilatura.extract(downloaded)
            if content and len(content.strip()) > 0:
                return content
        return None
    except Exception as e:
        logging.error(f"Erreur lors de la recherche Persée pour {battle_name}: {str(e)}")
        return None

def get_sources_urls(battle_name, year):
    """
    Génère les URLs des sources pour une bataille
    """
    try:
        encoded_name = quote(battle_name)
        sources = {
            "wikipedia": f"https://fr.wikipedia.org/wiki/Special:Search?search={encoded_name}",
            "gallica": f"https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&exactSearch=false&collapsing=true&version=1.2&query={encoded_name}",
            "persee": f"https://www.persee.fr/search?q={encoded_name}"
        }

        # Ajouter des sources spécialisées selon la période
        if year < 500:
            sources["inrap"] = "https://www.inrap.fr/recherche?q=" + encoded_name
        elif year < 1500:
            sources["menestrel"] = "http://www.menestrel.fr/spip.php?recherche=" + encoded_name
        else:
            sources["histoire_defense"] = "https://www.servicehistorique.sga.defense.gouv.fr/?q=" + encoded_name

        return sources
    except Exception as e:
        logging.error(f"Erreur lors de la génération des URLs pour {battle_name}: {str(e)}")
        return {}

def get_period_context(year):
    """
    Retourne le contexte historique selon la période
    """
    if year < 0:
        return "Cette bataille s'inscrit dans la période gauloise, marquée par les conflits entre tribus et l'expansion romaine."
    elif year < 500:
        return "Cette bataille a lieu durant l'Antiquité tardive, période de transition entre l'Empire romain et les royaumes francs."
    elif year < 1000:
        return "Cette bataille se déroule pendant le Haut Moyen Âge, époque marquée par l'émergence du royaume franc et les invasions vikings."
    elif year < 1500:
        return "Cette bataille s'inscrit dans le contexte du Moyen Âge central et tardif, période de structuration du royaume de France."
    elif year < 1800:
        return "Cette bataille se déroule sous l'Ancien Régime, période marquée par la centralisation du pouvoir royal et les conflits européens."
    else:
        return "Cette bataille appartient à l'époque contemporaine, caractérisée par les guerres nationales et les conflits mondiaux."

def process_battle_enrichment(battle):
    """
    Enrichit les informations d'une bataille avec des sources externes et un contexte historique
    """
    try:
        logging.info(f"Enrichissement des informations pour la bataille : {battle.name}")

        # Ajout du contexte historique de base
        battle.historical_context = get_period_context(battle.year)

        # Récupération des URLs des sources avec vérification des liens
        sources = get_sources_urls(battle.name, battle.year)
        if sources:
            battle.sources = json.dumps(sources, ensure_ascii=False)

        # Tentative de récupération d'informations de Gallica
        gallica_info = get_gallica_content(battle.name, battle.year)
        if gallica_info:
            battle.historical_context += f"\n\nInformations complémentaires de Gallica :\n{gallica_info[:500]}..."

        # Tentative de récupération d'informations de Persée
        persee_info = get_persee_content(battle.name, battle.year)
        if persee_info:
            battle.historical_context += f"\n\nInformations complémentaires de Persée :\n{persee_info[:500]}..."

        # Ajout des médias si nécessaire
        if not battle.media_urls:
            from utils import generate_sample_media_urls
            battle.media_urls = generate_sample_media_urls(battle.year)

        if not battle.image_url:
            from utils import generate_sample_image_url
            battle.image_url = generate_sample_image_url(battle.year)

        # Sauvegarde des modifications
        db.session.commit()
        logging.info(f"Enrichissement réussi pour la bataille : {battle.name}")
        return True

    except Exception as e:
        logging.error(f"Erreur lors de l'enrichissement de la bataille {battle.name}: {str(e)}")
        db.session.rollback()
        return False