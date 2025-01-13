from app import db

class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    link = db.Column(db.String(500), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    published = db.Column(db.DateTime, nullable=False)
    group_link = db.Column(db.String(500))
    show_notification = db.Column(db.Boolean, default=True)
    url_config_id = db.Column(db.Integer, db.ForeignKey('url_config.id'), nullable=False)
    favorite_id = db.Column(db.Integer, db.ForeignKey('favorite.id'), nullable=True)