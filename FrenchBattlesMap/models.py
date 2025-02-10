from app import db

class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    participants = db.Column(db.String(500))
    outcome = db.Column(db.String(500))
    historical_context = db.Column(db.Text)  # Contexte historique simple
    sources = db.Column(db.Text)  # Liens vers des sources externes (format JSON)
    image_url = db.Column(db.String(500))  # URL de l'image principale
    media_urls = db.Column(db.Text)  # URLs des médias additionnels (format JSON)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'participants': self.participants,
            'outcome': self.outcome,
            'historical_context': self.historical_context,
            'sources': self.sources,
            'image_url': self.image_url,
            'media_urls': self.media_urls
        }