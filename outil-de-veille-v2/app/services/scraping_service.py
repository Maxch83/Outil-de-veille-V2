from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pytz
from app import db
from app.models.article import Article
from app.models.url_config import UrlConfig

def get_news_scrapping():
    allEntries = [get20minutes(), getSolutionsNumeriques(), getCyberdaily()]
    
    for entries in allEntries:
        # Utiliser un ensemble pour suivre les liens uniques
        unique_links = set()
        
        # Filtrer les articles pour ne conserver que les uniques
        unique_entries = []
        for entry in entries:
            if entry['link'] not in unique_links:
                unique_links.add(entry['link'])
                unique_entries.append(entry)
        
        for entry in unique_entries:
            # Vérifier si l'article existe déjà dans la base de données
            existing_article = Article.query.filter_by(link=entry['link']).first()
            if existing_article:
                continue
            
            try:
                article = Article(
                    title=entry['title'],
                    link=entry['link'],
                    description=entry['description'],
                    published=entry['published'],
                    show_notification=entry['show_notification'],  # Ne pas afficher la notification si le flux est nouveau
                    url_config_id=entry['url_config_id']
                )
                db.session.add(article)
            except Exception as e:
                print(f"Erreur lors de l'insertion de l'article : {entry['link']}")
                print(e)
        db.session.commit()
        
def get20minutes():
    urls_20minutes = [
        'https://www.20minutes.fr/dossier/cybercriminalite',
        'https://www.20minutes.fr/dossier/cyberattaque',
        'https://www.20minutes.fr/dossier/cybersecurite'
    ]
    
    articles_20minutes = []  
    
    # Date actuelle avec fuseau horaire
    now = datetime.now(pytz.timezone('Europe/Paris'))
    
    # Vérifiez si UrlConfig existe, sinon le créer
    url_config = UrlConfig.query.filter_by(url='https://www.20minutes.fr').first()
    if not url_config:
        url_config = UrlConfig(
            website_title='20 minutes',
            url='https://www.20minutes.fr',
            category='actualites',
            subcategory='generale'
        )
        db.session.add(url_config)
        db.session.commit()
    
    for url in urls_20minutes:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    
        raw_titles_links = soup.find_all('h2')
        
        stop_scraping = False
        
        for raw_title_link in raw_titles_links:
            if stop_scraping:
                break
            
            title_link = raw_title_link.a
            link = title_link.get('href')
            title = title_link.get_text()
            
            response2 = requests.get(link)
            response2.raise_for_status()
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            
            raw_desc = soup2.find('span', class_='font-source-serif-pro')
            desc = raw_desc.get_text() if raw_desc else 'Description non trouvée'
            
            raw_parsed_date = soup2.find('time')
            parsed_date_text = raw_parsed_date.get_text().strip() if raw_parsed_date else None
            
            if parsed_date_text:
                try:
                    # Essayer avec le premier format
                    parsed_date = datetime.strptime(parsed_date_text, "Publié le %d/%m/%Y à %Hh%M")
                except ValueError:
                    try:
                        # Si le premier format échoue, essayer le second format
                        parsed_date = datetime.strptime(parsed_date_text, "Publié le %d/%m/%y à %Hh%M")
                    except ValueError as ve:
                        print(f"Erreur de format de date pour l'article {title}: {ve}")
                        continue
                
                # Ajouter le fuseau horaire à parsed_date
                parsed_date = pytz.timezone('Europe/Paris').localize(parsed_date)
                
                # Vérifier si la date est dans les 14 derniers jours
                if now - timedelta(days=14) <= parsed_date <= now:

                    # Ajouter l'article à la liste des articles
                    articles_20minutes.append({
                        'title': title,
                        'link': link,
                        'description': desc,
                        'published': parsed_date,  # Conservez le datetime object ici
                        'show_notification': not url_config.is_new,
                        'url_config_id': url_config.id
                    })
                    
                else:
                    # Si l'article est plus vieux que 14 jours, arrêter le scraping
                    stop_scraping = True
                    break
                
    if url_config.is_new :
        url_config.is_new = False
                
    return articles_20minutes

def getSolutionsNumeriques():
    url = 'https://www.solutions-numeriques.com/cybersecurite/'
    
    articles_solutions_numeriques = []  
    
    # Date actuelle avec fuseau horaire
    now = datetime.now(pytz.timezone('Europe/Paris'))
    
    # Vérifiez si UrlConfig existe, sinon le créer
    url_config = UrlConfig.query.filter_by(url='https://www.solutions-numeriques.com').first()
    if not url_config:
        url_config = UrlConfig(
            website_title='Solutions Numériques',
            url='https://www.solutions-numeriques.com',
            category='actualites',
            subcategory='generale'
        )
        db.session.add(url_config)
        db.session.commit()
    
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    raw_titles_links = soup.find_all('div', class_='bloc_article_16')
        
    stop_scraping = False
        
    for raw_title_link in raw_titles_links:
        if stop_scraping:
            break
        
        title_link = raw_title_link.find_all('a')[-1]

        link = title_link.get('href')
        title = title_link.get('title')
        
        response2 = requests.get(link)
        response2.raise_for_status()
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        raw_desc = soup2.find('div', class_='td-post-content')

        # Trouver le premier paragraphe dans ce div
        if raw_desc:
            raw_desc = raw_desc.find('p')
    
        desc = raw_desc.get_text() if raw_desc else 'Description non trouvée'
        
        raw_parsed_date = soup2.find('time')
        if raw_parsed_date and raw_parsed_date.has_attr('datetime'):
            parsed_date_text = raw_parsed_date['datetime']
            try:
                # Essayer avec l'attribut datetime d'abord
                parsed_date = datetime.fromisoformat(parsed_date_text)
            except ValueError as ve:
                print(f"Erreur de format de date pour l'article {title}: {ve}")
                continue
        else:
            parsed_date = None
        
        if parsed_date:
            # Ajouter le fuseau horaire à parsed_date s'il n'en a pas
            if parsed_date.tzinfo is None:
                parsed_date = pytz.timezone('Europe/Paris').localize(parsed_date)
            
            # Vérifier si la date est dans les 14 derniers jours
            if now - timedelta(days=14) <= parsed_date <= now:
            
                # Ajouter l'article à la liste des articles
                articles_solutions_numeriques.append({
                    'title': title,
                    'link': link,
                    'description': desc,
                    'published': parsed_date,  # Conservez le datetime object ici
                    'show_notification': not url_config.is_new,
                    'url_config_id': url_config.id
                })
           
        else:
            # Si l'article est plus vieux que 14 jours, arrêter le scraping
            stop_scraping = True
            break
        
    if url_config.is_new :
        url_config.is_new = False
                
    return articles_solutions_numeriques

def getCyberdaily():
    url = 'https://www.cyberdaily.au/news'
    
    articles_cyberdaily = []  
    
    # Date actuelle avec fuseau horaire
    now = datetime.now().date()
    
    # Vérifiez si UrlConfig existe, sinon le créer
    url_config = UrlConfig.query.filter_by(url='https://www.cyberdaily.au').first()
    if not url_config:
        url_config = UrlConfig(
            website_title='Cyber daily',
            url='https://www.cyberdaily.au',
            category='actualites',
            subcategory='specialise'
        )
        db.session.add(url_config)
        db.session.commit()
    
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    articles = soup.find_all('div', class_='categ_items-1')
    
    stop_scraping = False
    
    for article in articles:
        if stop_scraping:
            break
        
        link = 'https://www.cyberdaily.au'+article.find('a').get('href') if article else 'Titre non trouvée'
        paragraphs = article.find_all('p')
        title = paragraphs[0].get_text() if paragraphs[0] else 'Titre non trouvée'
        description = paragraphs[1].get_text() if paragraphs[1] else 'Description non trouvée'
        published = datetime.strptime(paragraphs[2].get_text().split(' • ')[1].strip(), '%a, %d %b %Y').date() if paragraphs[2] else now

        if now - timedelta(days=5) <= published <= now:
            # Ajouter l'article à la liste des articles
                articles_cyberdaily.append({
                    'title': title,
                    'link': link,
                    'description': description,
                    'published': published,
                    'show_notification': not url_config.is_new,
                    'url_config_id': url_config.id
                })
        else:
            # Si l'article est plus vieux que XX jours, arrêter le scraping
            stop_scraping = True
            break
        
    if url_config.is_new :
        url_config.is_new = False
        
    return articles_cyberdaily