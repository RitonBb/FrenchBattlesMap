import json
from app import db, cache
from models import Battle
import logging
import random
from datetime import datetime, timedelta

def generate_location_in_france():
    # France mainland bounding box
    return {
        'latitude': random.uniform(42.333333, 51.083333),
        'longitude': random.uniform(-4.833333, 8.233333)
    }

def generate_battle_name(year, region=None):
    battle_types = ['Bataille', 'Siège', 'Escarmouche', 'Défense', 'Assaut']
    locations = ['Paris', 'Lyon', 'Marseille', 'Bordeaux', 'Toulouse', 'Nice', 'Nantes', 
                'Strasbourg', 'Montpellier', 'Lille', 'Rennes', 'Reims', 'Tours', 'Caen',
                'Orléans', 'Rouen', 'Grenoble', 'Dijon', 'Amiens', 'Nîmes', 'Saint-Étienne',
                'Angers', 'Villeurbanne', 'Le Mans', 'Clermont-Ferrand', 'Aix-en-Provence']

    if random.random() < 0.7:  # 70% chance of using a real city name
        location = random.choice(locations)
    else:
        suffixes = ['sur-Loire', 'sur-Seine', 'sur-Rhône', 'sur-Garonne', 'en-Provence', 
                   'le-Château', 'la-Ville', 'sur-Mer', 'les-Bains', 'le-Comte']
        location = f"{random.choice(locations)}-{random.choice(suffixes)}"

    # Utiliser "d'" devant les villes commençant par une voyelle
    vowels = ('a', 'e', 'i', 'o', 'u', 'é', 'è', 'ê', 'h')
    preposition = "d'" if location.lower().startswith(vowels) else "de "

    return f"{random.choice(battle_types)} {preposition}{location}"

def get_period_details(year):
    if year < 0:
        return {
            'participants': ['Tribus Gauloises', 'République Romaine', 'Tribus Germaniques', 'Tribus Celtes'],
            'outcomes': ['Victoire des Gaulois', 'Victoire Romaine', 'Retraite stratégique', 'Issue indécise']
        }
    elif year < 500:
        return {
            'participants': ['Empire Romain', 'Royaumes Francs', 'Wisigoths', 'Burgondes', 'Armée des Huns'],
            'outcomes': ['Victoire Romaine', 'Victoire des Francs', 'Victoire des Wisigoths', 'Conquête territoriale']
        }
    elif year < 1000:
        return {
            'participants': ['Royaume des Francs', 'Raiders Vikings', 'Forces Carolingiennes', 'Duché de Bretagne'],
            'outcomes': ['Victoire des Francs', 'Victoire Viking', 'Victoire Carolingienne', 'Paix négociée']
        }
    elif year < 1300:
        return {
            'participants': ['Royaume de France', 'Saint-Empire Romain', 'Royaume d\'Angleterre', 'Duché de Normandie'],
            'outcomes': ['Victoire Française', 'Victoire Impériale', 'Victoire Anglaise', 'Trêve établie']
        }
    elif year < 1500:
        return {
            'participants': ['Royaume de France', 'Royaume d\'Angleterre', 'Duché de Bourgogne', 'Couronne d\'Aragon'],
            'outcomes': ['Victoire des Français', 'Victoire des Anglais', 'Victoire Bourguignonne', 'Accord de paix']
        }
    elif year < 1700:
        return {
            'participants': ['Royaume de France', 'Empire des Habsbourg', 'Provinces-Unies', 'États Protestants'],
            'outcomes': ['Victoire Française', 'Victoire des Habsbourg', 'Victoire Protestante', 'Compromis trouvé']
        }
    elif year < 1800:
        return {
            'participants': ['Royaume de France', 'Coalition Européenne', 'République Française', 'Armée Révolutionnaire'],
            'outcomes': ['Victoire Royaliste', 'Victoire Républicaine', 'Victoire de la Coalition', 'Armistice signé']
        }
    elif year < 1900:
        return {
            'participants': ['Empire Français', 'Royaume de Prusse', 'Empire Russe', 'Empire d\'Autriche'],
            'outcomes': ['Victoire Française', 'Victoire Prussienne', 'Victoire de la Coalition', 'Traité de paix']
        }
    else:
        return {
            'participants': ['Armée Française', 'Empire Allemand', 'Forces Alliées', 'Forces de l\'Axe'],
            'outcomes': ['Victoire Française', 'Victoire Alliée', 'Retraite ordonnée', 'Position maintenue']
        }

def generate_description(year, battle_type, participants):
    actions = ['a lancé une offensive contre', 'a défendu sa position contre', 'a assiégé', 'a tendu une embuscade à', 'a affronté']
    resultats = [
        'entraînant de lourdes pertes dans les deux camps',
        'dans une bataille décisive',
        'changeant l\'équilibre des forces',
        'marquant un tournant stratégique',
        'avec des conséquences majeures sur la suite du conflit'
    ]

    parts = participants.split(' contre ')
    return f"Les forces de {parts[0]} {random.choice(actions)} {parts[1]}, {random.choice(resultats)}."

def generate_sample_media_urls(year):
    """
    Génère des URLs d'exemple pour les médias en fonction de la période
    """
    media = []

    # Images d'exemple par période (images libres de droits de Wikimedia Commons)
    if year < 500:
        media.append({
            'url': 'https://upload.wikimedia.org/wikipedia/commons/4/4a/Vercingetorix_jette_ses_armes_aux_pieds_de_Jules_César.jpg',
            'type': 'image'
        })
    elif year < 1000:
        media.append({
            'url': 'https://upload.wikimedia.org/wikipedia/commons/f/f3/Charles_de_Steuben_-_Bataille_de_Poitiers.png',
            'type': 'image'
        })
    elif year < 1500:
        media.append({
            'url': 'https://upload.wikimedia.org/wikipedia/commons/5/5f/Jeanne_d%27Arc_Orlèans.jpg',
            'type': 'image'
        })
    else:
        media.append({
            'url': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Napoleon_at_the_Battle_of_Austerlitz.jpg',
            'type': 'image'
        })

    return json.dumps(media, ensure_ascii=False)

def generate_sample_image_url(year):
    """
    Génère une URL d'image principale en fonction de la période
    """
    if year < 500:
        return 'https://upload.wikimedia.org/wikipedia/commons/3/3f/Alesia-Vercingetorix.jpg'
    elif year < 1000:
        return 'https://upload.wikimedia.org/wikipedia/commons/7/72/Bataille_Tours_732.jpg'
    elif year < 1500:
        return 'https://upload.wikimedia.org/wikipedia/commons/9/9f/Siege_of_Orleans.jpg'
    else:
        return 'https://upload.wikimedia.org/wikipedia/commons/9/99/Napoleon_Bonaparte_battle.jpg'

def create_mock_data():
    logging.info("Starting to create mock data...")
    try:
        # Clear existing data
        logging.info("Deleting existing battles...")
        Battle.query.delete()
        db.session.commit()
        logging.info("Cleared existing data")

        # Clear cache before adding new data
        from routes import get_battles
        cache.delete_memoized(get_battles)

        # Define total battles per period with the same proportions
        periods = [
            {'range': (-100, 0), 'count': 600, 'name': 'Antiquité'},
            {'range': (1, 1789), 'count': 6900, 'name': 'Moyen-Âge à Époque Moderne'},
            {'range': (1789, 1815), 'count': 3000, 'name': 'Période Révolutionnaire'},
            {'range': (1815, 1945), 'count': 4500, 'name': 'Époque Contemporaine'}
        ]

        total_processed = 0
        batch_size = 100

        for period in periods:
            logging.info(f"Traitement de la période {period['name']}...")
            battles_created = 0

            while battles_created < period['count']:
                batch = []
                for _ in range(min(batch_size, period['count'] - battles_created)):
                    year = random.randint(period['range'][0], period['range'][1])
                    period_details = get_period_details(year)
                    loc = generate_location_in_france()

                    # Ensure different participants
                    participant1 = random.choice(period_details['participants'])
                    participant2 = random.choice([p for p in period_details['participants'] if p != participant1])
                    participants = f"{participant1} contre {participant2}"

                    battle_name = generate_battle_name(year)

                    batch.append(Battle(
                        name=battle_name,
                        year=year,
                        latitude=loc['latitude'],
                        longitude=loc['longitude'],
                        description=generate_description(year, battle_name.split()[0], participants),
                        participants=participants,
                        outcome=random.choice(period_details['outcomes']),
                        image_url=generate_sample_image_url(year),
                        media_urls=generate_sample_media_urls(year)
                    ))

                try:
                    db.session.bulk_save_objects(batch)
                    db.session.commit()
                    battles_created += len(batch)
                    total_processed += len(batch)
                    logging.info(f"Ajout du lot : {total_processed}/15000 batailles. Période en cours : {period['name']}")
                except Exception as e:
                    logging.error(f"Erreur lors de l'ajout du lot dans la période {period['name']} : {str(e)}")
                    db.session.rollback()
                    raise

        # Verify data was inserted
        count = Battle.query.count()
        logging.info(f"Nombre total de batailles dans la base de données après insertion : {count}")
        return True
    except Exception as e:
        logging.error(f"Erreur lors de la création des données : {str(e)}")
        db.session.rollback()
        raise