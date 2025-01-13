from app import db
from app.models.url_config import UrlConfig
from app.services.init_urls import get_urls

def extract_site_name(url):
    if 'feeds.feedburner.com' in url:
        site_name = url.split('/')[-1].title()
    elif 'raw.githubusercontent.com' in url:
        site_name = url.split('/')[4].title()
    elif 'www.cert.ssi.gouv.fr' in url:
        site_name = 'CERT-FR'
    elif 'cert.europa.eu' in url:
        site_name = 'CERT-EU'
    elif 'www.cisa.gov' in url:
        site_name = 'CISA'
    else:
        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]
        if url.startswith('www.'):
            url = url[4:]
        site_name = url.split('.')[0].title()
    return site_name

def InitDB():
    if UrlConfig.query.first() is None:  # Vérifie si la table User est vide
        urls = get_urls()
        for url in urls:
            website_title = extract_site_name(url[0])
            category = url[1]
            if url[0] and category:
                existing_feed = UrlConfig.query.filter_by(url=url[0]).first()
                if not existing_feed:
                    new_feed = UrlConfig(website_title=website_title, url=url[0], category=category, subcategory=url[2] if url[2] != '' else None)
                    db.session.add(new_feed)
        db.session.commit()
        print("Base de données initialisée avec des données de départ.")
