import feedparser
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from sqlalchemy import func
import pytz
from app import db
from app.models.article import Article
from app.models.url_config import UrlConfig
from app.models.favorite import Favorite

def get_news():
    feedparser.USER_AGENT = "OutilDeVeille/2.0 +https://urgencecyber-regionsud.fr/"

    def utc_now():
        date_now = datetime.now(pytz.utc).astimezone(pytz.timezone('Europe/Paris')) - timedelta(hours=2)
        return date_now
    
    french_tz = pytz.timezone('Europe/Paris')
    feeds = UrlConfig.query.all()
    ouest_france_urls = [
        'https://www.ouest-france.fr/rss/une',
        'https://www.ouest-france.fr/rss/france',
        'https://www.ouest-france.fr/rss/sport'
    ]
    scrapping_urls = [
        'https://www.20minutes.fr',
        'https://www.solutions-numeriques.com',
        'https://www.cyberdaily.au'
    ]
    
    # Date limite pour les articles (il y a 2 mois)
    date_limit = utc_now() - timedelta(days=60)

    for feed in feeds:
        feed_url = feed.url
        is_new_feed = feed.is_new
        articles = []

        if feed_url.endswith('.json'):
            response = requests.get(feed_url)
            json_data = response.json()
            for item in json_data:
                discovered = pytz.utc.localize(datetime.strptime(item['discovered'], "%Y-%m-%d %H:%M:%S.%f")).astimezone(french_tz)
                discovered = discovered.replace(second=0, microsecond=0)
                if discovered > date_limit:
                    article = {
                        'title': item.get('post_title', 'No Title'),
                        'link': 'no url '+item.get('post_title', 'No Title'), # Pas de lien fourni dans le JSON
                        'group_link': 'https://www.ransomlook.io/group/' + item.get('group_name', 'No Title'),
                        'description': item.get('group_name', 'No group_name'),
                        'published': discovered
                    }
                    
                    articles.append(article)
        else:
            parsed_feed = feedparser.parse(feed_url)
            for entry in parsed_feed.entries:
                
                group_link = None
                
                if feed_url == 'https://www.lemondeinformatique.fr/flux-rss/thematique/securite/rss.xml':
                    entry.published_parsed = entry.updated_parsed
                
                if hasattr(entry, 'published_parsed') and entry.published_parsed is not None:
                    published = datetime(*entry.published_parsed[:6], tzinfo=pytz.utc)
                    if published > utc_now() :
                        print('date futuriste pour : '+ feed_url)
                        published = utc_now()
                else:
                    print('Mauvaise date pour : '+ feed_url)
                    published = utc_now()

                if feed_url == 'https://www.redpacketsecurity.com/category/ransomware/rss':
                    titre_desc = entry.title.split(' Victim: ')
                    if titre_desc[0].endswith(' Ransomware'):
                        titre_desc[0] = titre_desc[0][:-len(' Ransomware')].strip()
                    entry.title = titre_desc[1].strip()
                    entry.description = titre_desc[0].strip()
                    group_link = 'https://www.ransomlook.io/group/'+entry['description'].lower()
                    response = requests.head(group_link, allow_redirects=False)
                    # Vérifier le code de statut
                    if response.status_code != 200:
                        group_link = group_link.replace(" ", "")

                if feed_url == 'https://www.ransomlook.io/rss.xml':
                    group_link = entry.link
                    entry.link = entry.link+'?'+entry.guid
                    titre_desc = entry.title.split(" By ")
                    entry.title = titre_desc[0].strip()
                    entry.description = titre_desc[1].strip()

                if feed_url == 'https://ransomware.live/rss.xml':
                    group_link = entry.link
                    if hasattr(entry, 'category'):
                        entry.link = entry.guid + ' ' + entry.category
                    if ' has just published a new victim : ' in entry.title:
                        titre_desc = entry.title.split(' has just published a new victim : ')
                        entry.title = titre_desc[1].strip()
                        title = titre_desc[0].split(' ', 1)
                        entry.description = title[1].strip()
                    elif ' has just published a new victim: ' in entry.title:
                        titre_desc = entry.title.split(' has just published a new victim: ')
                        entry.title = titre_desc[1].strip()
                        title = titre_desc[0].split(' ', 1)
                        entry.description = title[1].strip()
                    else:
                        print("Le texte 'has just published a new victim : ' n'est pas présent dans "+entry.title)
                        entry.descricption = entry.title
                    

                if feed.website_title == 'CERT-FR':
                    reference = entry.link.split('/')[-2]
                    entry.title = '<p class="nocolor">' + entry.title + '</p>' + reference + '<br>'
                    
                if feed.website_title == 'CISA':
                    # Parse the article description HTML
                    soup = BeautifulSoup(entry.description, 'html.parser')
                    li_tags = soup.find_all('li')

                    extracted_content = ''

                    for tag in li_tags:
                        original_text = tag.get_text()

                        # Check if the text contains any of the required keywords
                        if any(keyword in original_text for keyword in ['ATTENTION', 'Vulnerabilities', 'Equipment', 'CVSS']):
                            # Clone the <li> element by creating a new tag with the same content
                            cloned_tag = tag.__copy__()

                            if 'CVSS' not in original_text:
                                # Remove all <strong> tags from the clone for non-CVSS elements
                                for strong_tag in cloned_tag.find_all('strong'):
                                    strong_tag.decompose()

                            # Get the clean text without <strong> tags and remove colons
                            cleaned_text = cloned_tag.get_text()
                            cleaned_text = cleaned_text.replace(':', '').strip()

                            extracted_content += f'{cleaned_text}, '

                    # Remove the trailing comma and space
                    second_part, separator, first_part = extracted_content.rstrip(', ').rpartition(', ')
                    entry.description = f'{first_part}{separator}{second_part}'

                # Définir les URL spécifiques et les catégories d'intérêt
                special_feed_urls = [
                    'https://www.futura-sciences.com/rss/high-tech/actualites.xml',
                    'https://www.zdnet.fr/feed'
                ]
                
                special_categories = ['cybersécurité', 'cyberattaque']

                # Vérifier les conditions générales
                is_published_recently = published and published > date_limit
                is_not_special_feed = feed_url not in special_feed_urls

                # Vérifier les conditions spécifiques pour l'URL spéciale
                is_special_feed = feed_url in special_feed_urls
                
                categories = []
                
                if 'tags' in entry:
                    # Extract all categories
                    categories = [tag.term.lower() for tag in entry.tags]

                    # Check if any of the special categories are present
                    is_special_category = any(category in special_categories for category in categories)
                else:
                    is_special_category = False

                # Combiner les conditions
                if (is_published_recently and is_not_special_feed) or (is_special_feed and is_published_recently and is_special_category):
                    article = {
                        'title': entry.title,
                        'link': entry.link,
                        'group_link': group_link,
                        'description': entry.description if hasattr(entry, 'description') else 'Unknown',
                        'published': published
                    }
                    articles.append(article)

        for entry in articles:
            if (feed_url == 'https://www.nicematin.com/rss' and 'cyber' in entry['title'].lower()) or \
               (feed_url in ouest_france_urls and 'societe/cyberattaque' in entry['link']) or \
               (feed_url not in ['https://www.nicematin.com/rss'] + ouest_france_urls + scrapping_urls):
                   
                existing_feed = Article.query.filter_by(link=entry['link']).first() or \
                                (Article.query.filter(func.lower(func.replace(Article.title, ' ', '')) == entry['title'].lower().replace(' ', '')).first() and \
                                Article.query.filter(func.lower(func.replace(Article.description, ' ', '')) == entry['description'].lower().replace(' ', '')).first())
                   
                if existing_feed is None:
                    article = Article(
                        title=entry['title'], 
                        link=entry['link'], 
                        description=entry['description'], 
                        published=entry['published'],
                        group_link=entry['group_link'],
                        show_notification=not is_new_feed,  # Ne pas afficher la notification si le flux est nouveau
                        url_config_id=feed.id,
                    )
                    db.session.add(article)
        
        # Marquer le flux comme non nouveau après la première récupération des articles
        if feed.is_new:
            feed.is_new = False
            db.session.add(feed)
        
        db.session.commit()

def get_articles_by_categories(categories):
    articles_by_category = {}
    seven_days_ago = datetime.now(pytz.timezone('Europe/Paris')) - timedelta(days=14)
    for category in categories:
        if category == 'domaines_ioc':
            articles = Article.query.join(UrlConfig).outerjoin(Favorite).filter(
            UrlConfig.category == 'domaine' or UrlConfig.category == 'ioc',
            Article.published >= seven_days_ago
            ).order_by(Article.published.desc()).all()
        else :
            articles = Article.query.join(UrlConfig).outerjoin(Favorite).filter(
                UrlConfig.category == category,
                Article.published >= seven_days_ago
                ).order_by(Article.published.desc()).all()
        articles_by_category[category] = articles
    return articles_by_category

def get_articles_by_subcategories(category, subcategories):
    articles_by_subcategory = {}
    seven_days_ago = datetime.now(pytz.timezone('Europe/Paris')) - timedelta(days=14)
    for subcategory in subcategories:
        if subcategory and category != 'attaques':
            articles = Article.query.join(UrlConfig).filter(UrlConfig.category == category, UrlConfig.subcategory == subcategory, Article.published >= seven_days_ago).order_by(Article.published.desc()).all()
        else:
            articles = Article.query.join(UrlConfig).filter(UrlConfig.category == subcategory, UrlConfig.subcategory.is_(None), Article.published >= seven_days_ago).order_by(Article.published.desc()).all()
        articles_by_subcategory[subcategory] = articles
    return articles_by_subcategory