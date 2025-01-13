import pandas as pd
from io import BytesIO
import os
import signal
from flask import render_template, request, redirect, send_file, url_for, jsonify
from sqlalchemy import and_
from app import app, db, format_datetime, read_config, save_config
from app.models.article import Article
from app.models.url_config import UrlConfig
from app.models.favorite import Favorite
from app.services.rss_service import get_news, get_articles_by_categories, get_articles_by_subcategories
from app.services.scraping_service import get_news_scrapping
from app.services.init_urls import get_urls
from app.services.init_db import extract_site_name

@app.route('/')
def index():
    favoris = Favorite.query.all()
    category='all'
    categories = ['actualites', 'bulletins', 'attaques', 'domaines', 'ioc', 'domaines_ioc']
    articles_by_category = get_articles_by_categories(categories)
    return render_template('index.html', articles_by_category=articles_by_category, favoris=favoris, category=category)

@app.route('/admin_articles')
def admin_articles():
    articles = Article.query.all()  # Récupérer tous les utilisateurs
    return render_template('admin_articles.html', articles=articles)

@app.route('/admin_urlconfig')
def admin_urlconfig():
    urlConfigs = UrlConfig.query.all()  # Récupérer tous les utilisateurs
    return render_template('admin_urlconfig.html', urlConfigs=urlConfigs)


@app.route('/favorites/json', methods=['GET'])
def get_favorites():
    favoris = Favorite.query.all()
    favoris_data = [{'id': fav.id, 'name': fav.name, 'color': fav.color} for fav in favoris]
    return jsonify(favoris=favoris_data)


@app.route('/news/all/json')
def get_all_news():
    get_news_scrapping()
    get_news()
    categories = ['attaques', 'actualites', 'bulletins', 'domaines', 'ioc', 'domaines_ioc']

    articles_by_categories = get_articles_by_categories(categories)
    articles_data = {
        category: [
            {
                'id': article.id,
                'title': article.title,
                'link': article.link,
                'description': article.description,
                'published': article.published,
                'group_link': article.group_link,
                'show_notification': article.show_notification,
                'website_title': article.url_config.website_title,
                'favorite_id': article.favorite_id,
                'color': article.favorite.color if article.favorite else None
            }
            for article in articles
        ]
        for category, articles in articles_by_categories.items()
    }
    return jsonify(articles_data)

@app.route('/category/<string:category>/json')
def show_category_json(category):
    get_news_scrapping()
    get_news()  # Mise à jour des articles depuis les flux RSS
    subcategories = []
    if category == 'bulletins':
        subcategories = ['anssi', 'cisa', 'autres']
    elif category == 'actualites':
        subcategories = ['specialise', 'generale']
    elif category == 'attaques':
        subcategories = ['']
    elif category == 'domaines':
        subcategories = ['']

    articles_by_subcategory = get_articles_by_subcategories(category, subcategories)
    articles_data = {subcategory: [{'id': article.id, 'title': article.title, 'link': article.link, 'description': article.description, 'published': article.published, 'show_notification': article.show_notification} for article in articles] for subcategory, articles in articles_by_subcategory.items()}
    return jsonify(articles_data)

@app.route('/category/<string:category>')
def view_category(category):
    subcategories = []
    if category == 'bulletins':
        subcategories = ['anssi', 'cisa', 'autres']
    elif category == 'actualites':
        subcategories = ['specialise', 'generale']
    elif category == 'attaques':
        subcategories = ['attaques', 'domaines', 'ioc']

    articles_by_subcategory = get_articles_by_subcategories(category, subcategories)
    favoris = Favorite.query.all()
    return render_template('category.html', category=category, subcategories=subcategories, favoris=favoris, articles_by_subcategory=articles_by_subcategory)

@app.route('/delete_article/<int:id>', methods=['POST'])
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/hide_notification/<int:id>', methods=['POST'])
def hide_notification(id):
    article = Article.query.get_or_404(id)
    article.show_notification = False
    db.session.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/hide_all_notifications/<string:category>', methods=['POST'])
def hide_all_notifications(category):
    if category == 'all' :
        articles = Article.query.join(UrlConfig).filter(Article.show_notification == True).all()
    else :
        articles = Article.query.join(UrlConfig).filter(UrlConfig.category == category, Article.show_notification == True).all()
    for article in articles:
        article.show_notification = False
    db.session.commit()
    return jsonify({'status': 'success'}), 200

############
# FAVORITE #
############

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    data = request.get_json()
    name = data.get('name')
    color = data.get('color')
    if name and color:
        new_favorite = Favorite(name=name, color=color)
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({'message': 'Favorite category added successfully'}), 201
    return jsonify({'message': 'Name and color are required'}), 400

@app.route('/update_favorite/<int:favorite_id>', methods=['PUT'])
def update_favorite(favorite_id):
    data = request.get_json()
    favorite = Favorite.query.get_or_404(favorite_id)
    name = data.get('name')
    color = data.get('color')
    if name:
        favorite.name = name
    if color:
        favorite.color = color
    db.session.commit()
    return jsonify({'message': 'Favorite category updated successfully'}), 200

@app.route('/update_article_favorite', methods=['POST'])
def update_article_favorite():
    data = request.get_json()
    favorite_id = data.get('favorite_id')
    article_id = data.get('article_id')
    article = Article.query.get(article_id)
    if article:
        if favorite_id == 'None' or favorite_id is None:
            article.favorite_id = None  # Mettre à jour à null dans la base de données
        else:
            article.favorite_id = favorite_id
        db.session.commit()
        
        # Récupérer l'objet Favorite
        favorite = Favorite.query.get(favorite_id)
        if favorite and favorite != 'None'and favorite != 'none':
            # Construire l'HTML de l'icône
            updated_favorite_icon = f"<i class='fa-solid fa-bookmark' style='color: {favorite.color};'></i>"
        else:
            # Cas où favorite_id est None ou n'existe pas dans la table Favorite
            updated_favorite_icon = "<i class='empty-bookmark fa-regular fa-bookmark'></i>"
        
        return jsonify(success=True, updated_favorite_icon=updated_favorite_icon)
    return jsonify(success=False), 404

@app.route('/remove_all_favorites/<string:category>', methods=['POST'])
def remove_all_favorites(category):
    if category == 'all' :
        articles = Article.query.filter(and_(Article.favorite_id.isnot(None), Article.favorite_id != 'None')).all()
    else :
        articles = Article.query.filter(Article.favorite_id == int(category)).all()
    for article in articles:
        article.favorite_id = None
    db.session.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete_favorite/<int:favorite_id>', methods=['POST'])
def delete_favorite(favorite_id):
    favorite = Favorite.query.get_or_404(favorite_id)
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({'message': 'Favorite category deleted successfully'}), 200

@app.route('/articles_by_favorites', methods=['POST'])
def articles_by_favorites():
    data = request.get_json()
    favorite_ids = data.get('favorite_ids', [])

    if not favorite_ids:
        articles = Article.query.filter(and_(Article.favorite_id.isnot(None), Article.favorite_id != 'None')).all()
    else:
        articles = Article.query.filter(Article.favorite_id.in_(favorite_ids)).all()
    
    articles_data = [
        {
            'id' : article.id,
            'published': format_datetime(article.published),
            'link': article.link,
            'title': article.title,
            'website_title': article.url_config.website_title,
            'show_notification': article.show_notification,
            'favorite_name': article.favorite.name if article.favorite else '',
            'favorite_color': article.favorite.color if article.favorite else '#ffffff'
        } for article in articles
    ]
    return jsonify(articles=articles_data)

@app.route('/export_articles')
def export_articles():
    try:
        # Récupérer les articles avec une catégorie de favoris
        articles = Article.query.filter(Article.favorite_id.isnot(None)).order_by(Article.favorite_id, Article.published.desc()).all()
        
        if not articles:
                return "Aucun article trouvé", 404

        # Créer une liste de dictionnaires pour pandas DataFrame
        data = [{
            'Catégorie': article.favorite.name,
            'Date': article.published.strftime('%d-%m-%Y %H:%M'),
            'Titre': article.title,
            'Lien': article.link
        } for article in articles]

        # Créer un DataFrame pandas
        df = pd.DataFrame(data)
        
        if df.empty:
            return "Le dataframe est vide", 400

        # Trier d'abord par 'Catégorie', puis par 'Date'
        df.sort_values(by=['Catégorie', 'Date'], ascending=[True, False], inplace=True)

        # Sauvegarder dans un fichier Excel dans un buffer en mémoire
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Articles')
        
        # Récupérer le contenu du fichier Excel
        output.seek(0)

        # Envoyer le fichier Excel comme réponse
        return send_file(output, as_attachment=True, download_name='articles_favoris.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        print(f"Erreur lors de l'exportation des articles : {e}")
        return f"Erreur lors de l'exportation : {e}", 500

##############
# PARAMETRES #
##############

@app.route('/parametres', methods=['GET', 'POST'])
def parametres():
    if request.method == 'POST':
        if request.form.get('url'):
            new_url = request.form.get('url')
            website_title = extract_site_name(new_url)
            category = request.form.get('category')
            subcategory = request.form.get('subcategory')
            if new_url and category:
                existing_feed = UrlConfig.query.filter_by(url=new_url).first()
                if not existing_feed:
                    new_feed = UrlConfig(website_title=website_title, url=new_url, category=category, subcategory=subcategory if subcategory != '' else None)
                    db.session.add(new_feed)
                    db.session.commit()
                return redirect(url_for('parametres'))
            
        elif request.form.get('name'):
            new_name = request.form.get('name')
            color = request.form.get('color')
            if new_name and color:
                existing_favorite = Favorite.query.filter_by(name=new_name).first()
                if not existing_favorite:
                    new_favorite = Favorite(name=new_name, color=color)
                    db.session.add(new_favorite)
                    db.session.commit()
                return redirect(url_for('parametres'))

    config = read_config()
    skip_dialog = config['DEFAULT'].getboolean('skip_dialog', False)
    feeds = UrlConfig.query.all()
    favorites = Favorite.query.all()
    return render_template('parametres.html', feeds=feeds, favorites=favorites, skip_dialog=skip_dialog)

@app.route('/update_skip_dialog', methods=['POST'])
def update_skip_dialog():
    skip_dialog = 'skip_dialog' in request.form  # Vérifie si la case est cochée
    config = read_config()
    db_path = config['DEFAULT'].get('db_path', './outildeveille.db')
    save_config(db_path, skip_dialog)
    return redirect(url_for('parametres'))

@app.route('/delete_feed/<int:id>', methods=['POST'])
def delete_feed(id):
    feed = UrlConfig.query.get_or_404(id)
    db.session.delete(feed)
    db.session.commit()
    return redirect(url_for('parametres'))

@app.route('/set_rss_default', methods=['POST'])
def set_rss_default():
    # Fonction pour supprimer toutes les entrées de la table url_config et les articles associés
    def delete_all_url_configs():
        try:
            # Récupérer toutes les entrées de la table url_config
            url_configs = UrlConfig.query.all()

            # Supprimer chaque entrée
            for url_config in url_configs:
                db.session.delete(url_config)
            
            # Valider la transaction
            db.session.commit()
            print("Toutes les entrées de la table url_config et les articles associés ont été supprimées avec succès.")
        except Exception as e:
            # En cas d'erreur, annuler la transaction
            db.session.rollback()
            print(f"Une erreur est survenue: {e}")
    
    urls = get_urls()
    delete_all_url_configs()
    
    for url in urls:
        website_title = extract_site_name(url[0])
        category = url[1]
        if url[0] and category:
            existing_feed = UrlConfig.query.filter_by(url=url[0]).first()
            if not existing_feed:
                new_feed = UrlConfig(website_title=website_title, url=url[0], category=category, subcategory=url[2] if url[2] != '' else None)
                db.session.add(new_feed)
    db.session.commit()
    return redirect(url_for('parametres'))

@app.route('/show_shutdown')
def show_shutdown():
    return render_template('shutdown.html')

@app.route('/shutdown')
def shutdown():
    if os.name == 'nt':
        # Windows
        os.kill(os.getpid(), signal.CTRL_BREAK_EVENT)
    else:
        # Unix-like (Linux/Mac)
        os.kill(os.getpid(), signal.SIGINT)