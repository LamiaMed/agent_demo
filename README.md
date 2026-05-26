**** Configuration
google calendar
google gmail

Si modification, supprimer le fichier : token.json 

<<<<<<< HEAD
=======
## Lancer le backend

Depuis la racine du projet, avec le virtualenv local :

```bash
.venv/bin/uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Si besoin, tu peux aussi activer l'environnement avant :

```bash
source .venv/bin/activate
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Depuis le dossier `backend/`, la commande devient :

```bash
cd backend
PYTHONPATH=.. ../.venv/bin/uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

## Lancer backend + frontend

Dans deux terminaux séparés :

```bash
# Terminal 1
.venv/bin/uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Terminal 2
cd frontend
npm run dev
```

Version pratique depuis la racine, en une seule ligne par service :

```bash
(.venv/bin/uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000) &
cd frontend && npm run dev
```

Si tu veux en faire un vrai script de démarrage plus tard, on pourra créer un `launch.sh` ou un `Makefile`.

>>>>>>> 7d5f79e (project)

*** Ex : requete
"Titre: Consultation Suivi M. Martin ACTE-01, Date: 2026-05-24, Heure: 14h00"
"donne moi un rendez vous pour le 28/05/2026 à 11 heure pour ACTE-01"
"donne moi un rendez vous pour le 28/05/2026 à 10 heure pour ACTE-02"
"donne moi un rendez vous vendredi prochain à 1 heure pour ACTE-01"
"voici mon address francis.garcia81000@gmail.com"


*** Docker
liste en cours : sudo docker ps -a
detail         : sudo docker inspect mon-agent
<<<<<<< HEAD
liste image    : sudo docker image ls
=======
liste image    : sudo docker image ls
>>>>>>> 7d5f79e (project)
