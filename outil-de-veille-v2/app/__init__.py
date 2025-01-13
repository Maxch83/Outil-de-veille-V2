from datetime import datetime
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import configparser
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import webbrowser
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

def get_config_file_path():
    # Définir le répertoire permanent pour le fichier de configuration
    config_dir = Path.home() / ".outildeveille"
    config_dir.mkdir(exist_ok=True)  # Crée le répertoire s'il n'existe pas
    config_file_path = config_dir / "config.ini"
    
    # Si l'application est compilée (mode exécutable unique)
    if getattr(sys, 'frozen', False):
        # Répertoire temporaire utilisé par PyInstaller
        base_path = Path(sys._MEIPASS)
        bundled_config_path = base_path / 'config' / 'config.ini'
        
        # Copier le fichier de configuration dans le répertoire permanent s'il n'existe pas
        if not config_file_path.exists():
            shutil.copy(bundled_config_path, config_file_path)
    
    return config_file_path

CONFIG_FILE = get_config_file_path()

def read_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['DEFAULT'] = {'db_path': './outildeveille.db', 'skip_dialog': 'False'}
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config

def save_config(db_path, skip_dialog):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'db_path': db_path, 'skip_dialog': str(skip_dialog)}
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Définir le filtre personnalisé
def format_datetime(value, format="%d-%m-%Y<br>%H:%M"):
    if isinstance(value, str):
        date_obj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    elif isinstance(value, datetime):
        date_obj = value
    else:
        raise ValueError("Valeur non supportée pour la conversion")
    return date_obj.strftime(format)

# Enregistrer le filtre
app.jinja_env.filters['format_datetime'] = format_datetime

# Fonction pour vérifier si une date est aujourd'hui
def is_today(value):
    if isinstance(value, str):
        date_obj = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    elif isinstance(value, datetime):
        date_obj = value
    else:
        raise ValueError("Valeur non supportée pour la conversion")
    return date_obj.date() == datetime.now().date()

# Enregistrer la fonction comme filtre Jinja2
app.jinja_env.filters['is_today'] = is_today

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images', 'favicon.ico')

class CustomDialog(simpledialog.Dialog):
    def body(self, master):
        config = read_config()
        initial_db_path = config['DEFAULT'].get('db_path', './outildeveille.db')
        self.skip_dialog = tk.BooleanVar(value=config['DEFAULT'].getboolean('skip_dialog', False))
        tk.Label(master, text="Chemin de votre BDD:").grid(row=0)
        self.entry = tk.Entry(master)
        self.entry.grid(row=0, column=1)
        self.entry.insert(0, initial_db_path)
        self.browse_button = tk.Button(master, text="Parcourir", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)
        self.checkbox = tk.Checkbutton(master, text="Ne plus afficher cette fenêtre", variable=self.skip_dialog)
        self.checkbox.grid(row=1, columnspan=3, sticky="w", pady=5)
        return self.entry

    def buttonbox(self):
        box = tk.Frame(self)
        self.ok_button = tk.Button(box, text="Confirmer", width=20, command=self.ok, default=tk.ACTIVE)
        self.ok_button.grid(row=0, column=0, padx=5, pady=5)
        self.default_button = tk.Button(box, text="Par défault", width=10, command=self.create_default_db)
        self.default_button.grid(row=0, column=1, padx=5, pady=5)
        self.cancel_button = tk.Button(box, text="Annuler", width=10, command=self.cancel)
        self.cancel_button.grid(row=0, column=2, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()
        
    def browse_file(self):
        file_path = filedialog.askopenfilename(title="Sélectionner le fichier de la BDD")
        if file_path:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, file_path)
        
    def create_default_db(self):
        self.result = "./outildeveille.db"
        if not os.path.exists(self.result):
            # Créer la base de données si elle n'existe pas
            conn = sqlite3.connect(self.result)
            conn.close()
        self.ok()
        
    def apply(self):
        self.result = self.entry.get()
        self.skip_dialog = self.skip_dialog.get()

def is_valid_db_path(db_path):
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute('SELECT 1')
            conn.close()
            return True
        except:
            return False
    return False

def prompt_db_path():
    root = tk.Tk()
    root.withdraw()  # Cacher la fenetre principale

    config = read_config()
    if config['DEFAULT'].getboolean('skip_dialog', False):
        db_path = config['DEFAULT'].get('db_path', './outildeveille.db')
        if is_valid_db_path(db_path):
            return db_path
    
    while True:
        dialog = CustomDialog(root, "Chemin vers la BDD")
        db_path = dialog.result
        skip_dialog = dialog.skip_dialog
        if db_path and db_path.startswith('~'):
            db_path = os.path.expanduser(db_path)
        if db_path is None: # Action du bouton annuler
            root.destroy()
            sys.exit()
        elif not db_path:
            messagebox.showerror("Chemin invalide", "Le chemin donné est vide. Merci d'entrer un chemin")
        elif not db_path.endswith('.db'):
            messagebox.showerror("Chemin invalide", "Le chemin doit se terminer par .db")
        elif is_valid_db_path(db_path):
            save_config(db_path, skip_dialog)
            return db_path
        else:
            messagebox.showerror("Chemin invalide", "Le chemin donné n'est pas valide. Merci de réessayer.")

    root.destroy()

# Définir le chemin de la base de données
db_path = prompt_db_path()
if db_path:
    print(f"Chemin de la BDD: {db_path}")
else:
    print("Action annulée.")

# Convertir le chemin en chemin absolu
db_path = os.path.abspath(db_path)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10  # Taille du pool de connexions
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20  # Nombre maximum de connexions supplémentaires
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 60  # Timeout en secondes pour obtenir une connexion du pool

db = SQLAlchemy(app)
webbrowser.open('http://localhost:55555')

# Importez tous les modules ici pour éviter les problèmes de dépendances circulaires.
# Par exemple, si vous avez un fichier views.py ou models.py, vous pouvez l'importer après l'initialisation de db.
from app.models import article, url_config, favorite
from app.routes import routes
