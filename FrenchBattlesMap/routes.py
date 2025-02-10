from flask import render_template, jsonify, request, make_response
from app import app, db, cache
from models import Battle
from utils import create_mock_data
from services.battle_enrichment import process_battle_enrichment
import logging

def init_db():
    logging.info("Initializing database...")
    try:
        # Always recreate mock data
        logging.info("Creating fresh mock data...")
        create_mock_data()
        logging.info("Mock data creation completed")
    except Exception as e:
        logging.error(f"Error in init_db: {str(e)}")
        db.session.rollback()
        raise

@app.route('/')
@cache.cached(timeout=3600)  # Cache the homepage for 1 hour
def index():
    return render_template('index.html')

@app.route('/api/battles')
@cache.memoize(timeout=300)  # Cache battle results for 5 minutes
def get_battles():
    try:
        start_year = request.args.get('start_year', 0, type=int)
        end_year = request.args.get('end_year', 2025, type=int)

        logging.info(f"Fetching battles between years {start_year} and {end_year}")

        battles = Battle.query.filter(
            Battle.year >= start_year,
            Battle.year <= end_year
        ).all()

        result = [battle.to_dict() for battle in battles]
        logging.info(f"Found {len(result)} battles in the specified range")

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in get_battles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/battles/<int:battle_id>/enrich', methods=['POST'])
def enrich_battle(battle_id):
    try:
        battle = Battle.query.get_or_404(battle_id)
        success = process_battle_enrichment(battle)
        if success:
            db.session.commit()
            return jsonify({"message": "Informations de la bataille enrichies avec succès", "battle": battle.to_dict()})
        return jsonify({"error": "Échec de l'enrichissement des informations"}), 500
    except Exception as e:
        logging.error(f"Erreur lors de l'enrichissement de la bataille {battle_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    try:
        cache.delete_memoized(get_battles)
        cache.delete('view//index.html')  # Clear homepage cache
        logging.info("Cache cleared successfully")
        return jsonify({"message": "Cache cleared successfully"}), 200
    except Exception as e:
        logging.error(f"Error clearing cache: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Documentation de l'API
@app.route('/api/docs')
def api_documentation():
    return jsonify({
        "version": "1.0",
        "description": "API publique des batailles historiques françaises",
        "endpoints": {
            "GET /api/v1/battles": {
                "description": "Récupérer la liste des batailles",
                "parameters": {
                    "start_year": "int (optionnel) - Année de début",
                    "end_year": "int (optionnel) - Année de fin",
                    "type": "string (optionnel) - Type de bataille",
                    "limit": "int (optionnel) - Nombre maximum de résultats",
                    "offset": "int (optionnel) - Décalage pour la pagination"
                }
            },
            "GET /api/v1/battles/{battle_id}": {
                "description": "Récupérer les détails d'une bataille spécifique"
            },
            "GET /api/v1/statistics": {
                "description": "Obtenir des statistiques sur les batailles"
            }
        }
    })

# Endpoint pour récupérer la liste des batailles (v1)
@app.route('/api/v1/battles')
@cache.memoize(timeout=300)
def get_battles_v1():
    try:
        # Paramètres de filtrage et pagination
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)
        battle_type = request.args.get('type')
        limit = min(request.args.get('limit', 100, type=int), 1000)  # Max 1000 résultats
        offset = request.args.get('offset', 0, type=int)

        # Construction de la requête
        query = Battle.query

        # Application des filtres
        if start_year is not None:
            query = query.filter(Battle.year >= start_year)
        if end_year is not None:
            query = query.filter(Battle.year <= end_year)
        if battle_type:
            query = query.filter(Battle.name.startswith(battle_type))

        # Récupération du compte total
        total_count = query.count()

        # Application de la pagination
        battles = query.offset(offset).limit(limit).all()

        # Préparation de la réponse
        result = {
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "battles": [battle.to_dict() for battle in battles]
        }

        response = make_response(jsonify(result))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        logging.error(f"Error in get_battles_v1: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoint pour récupérer une bataille spécifique (v1)
@app.route('/api/v1/battles/<int:battle_id>')
@cache.memoize(timeout=300)
def get_battle_v1(battle_id):
    try:
        battle = Battle.query.get_or_404(battle_id)
        response = make_response(jsonify(battle.to_dict()))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        logging.error(f"Error in get_battle_v1: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoint pour les statistiques (v1)
@app.route('/api/v1/statistics')
@cache.memoize(timeout=3600)  # Cache pour 1 heure
def get_statistics_v1():
    try:
        # Statistiques globales
        total_battles = Battle.query.count()
        earliest_battle = Battle.query.order_by(Battle.year).first()
        latest_battle = Battle.query.order_by(Battle.year.desc()).first()

        # Distribution par type
        battle_types = ['Bataille', 'Siège', 'Escarmouche', 'Défense', 'Assaut']
        types_distribution = {}
        for battle_type in battle_types:
            count = Battle.query.filter(Battle.name.like(f'{battle_type}%')).count()
            if count > 0:
                types_distribution[battle_type] = count

        # Distribution par siècle
        century_query = db.session.query(
            db.func.cast(db.func.floor(Battle.year / 100.0), db.Integer).label('century'),
            db.func.count().label('count')
        ).group_by('century').order_by('century')

        century_distribution = {
            f"{century * 100}": count
            for century, count in century_query.all()
        }

        statistics = {
            "total_battles": total_battles,
            "time_span": {
                "earliest": earliest_battle.year if earliest_battle else None,
                "latest": latest_battle.year if latest_battle else None
            },
            "types_distribution": types_distribution,
            "century_distribution": century_distribution
        }

        response = make_response(jsonify(statistics))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        logging.error(f"Error in get_statistics_v1: {str(e)}")
        return jsonify({"error": str(e)}), 500