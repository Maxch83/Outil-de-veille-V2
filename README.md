# Outil de veille - Urgence Cyber région Sud
![Logo UCRS](https://www.vigilance-cyber.fr/wp-content/uploads/2024/02/cropped-Logo_Urgence_Cyber_region_Sud1.png "logo UCRS")
#### Description
Cet outil a pour objectif une veille efficace des analystes d'urgence cyber région sud.


## A effectuer après un ajout dans le pipenv
```console
pipenv run pip freeze > requirements.txt
```

## Générer l'éxecutable
>[!IMPORTANT]
>
>Avoir [Python 3.12.3](https://www.python.org/downloads/release/python-3123/) sur la machine.
>Penser également à cocher (Add python.exe to PATH)

#### WINDOWS
```powershell
cd \Outil-de-veille-V2\
python -m venv .venv
```
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1
# cmd
.\.venv\Scripts\activate
```
>[!NOTE]
>
>Si vous avez un problème avec la politique de restriction d'exécution
>```powershell
>Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
>```
>Puis re exécuter l'étape précédente
```powershell
cd .\outil-de-veille-v2
pip install -r requirements.txt
pyinstaller 'Outil de veille - UCRS.spec'
```

#### LINUX
```console
cd Outil-de-veille-V2/
python -m venv .venv
source .venv/bin/activate
cd outil-de-veille-v2/
pip install -r requirements.txt
pyinstaller 'Outil de veille - UCRS.spec'
```

## Arreter l'application de force
#### WINDOWS
```powershell
tasklist | findstr 'Outil de veille - UCRS.exe'
```
#### LINUX
```console
ps aux | grep 'Outil de veille - UCRS'
kill -9 Id_de_l_application
```




## Crédits
* Nathan Giammellaro
* Torres Antoine ramon
* Benjamin Kraemer
* Thomas Moulins
