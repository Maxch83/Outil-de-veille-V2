from app import db

class UrlConfig(db.Model):
    __tablename__ = 'url_config'
    id = db.Column(db.Integer, primary_key=True)
    website_title = db.Column(db.String(250), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=True)
    is_new = db.Column(db.Boolean, default=True)
    articles = db.relationship('Article', backref='url_config', cascade="all, delete-orphan")