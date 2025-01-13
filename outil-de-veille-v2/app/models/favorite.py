from app import db

class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), nullable=False)  # Code couleur hexadécimal
    articles = db.relationship('Article', backref='favorite', cascade="all, delete-orphan")