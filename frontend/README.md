# Frontend Next.js

Interface web pour dialoguer avec l'agent IA via l'API FastAPI existante.

## Ce que fait ce frontend

- page principale avec champ de saisie
- bouton d'envoi
- affichage de la réponse
- état de chargement
- gestion simple des erreurs
- aucun appel direct à OpenAI depuis le navigateur

## Prérequis

- Node.js 18+ ou 20+
- l'API FastAPI lancée localement ou accessible à distance

## Structure

```txt
frontend/
  app/
    globals.css
    layout.tsx
    page.tsx
  next-env.d.ts
  next.config.ts
  package.json
  postcss.config.mjs
  tailwind.config.ts
  tsconfig.json
```

## Variable d'environnement

Créer un fichier `frontend/.env.local` avec l'URL du backend FastAPI :

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Important :
- cette variable est lue côté frontend
- la clé OpenAI reste côté backend
- ne pas mettre de secret dans `NEXT_PUBLIC_*`

## Installation

Depuis la racine du projet :

```bash
cd frontend
npm install
```

## Démarrage en local

Lancer le frontend :

```bash
cd frontend
npm run dev
```

Puis ouvrir :

```bash
http://localhost:3000
```

## Vérifier le backend

Avant de tester l'interface, vérifier que l'API répond :

```bash
curl http://localhost:8000/health
```

Test de l'endpoint chat :

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Bonjour"}'
```

## Build de production

```bash
cd frontend
npm run build
```

Puis démarrer la version de production :

```bash
npm run start
```

## Contrat API attendu

Le frontend appelle :

```http
POST /chat
Content-Type: application/json
```

Corps attendu :

```json
{
  "message": "Votre question"
}
```

Réponse attendue :

```json
{
  "reply": "Réponse de l'agent"
}
```

## Dépannage rapide

- Si le bouton reste désactivé, vérifier `NEXT_PUBLIC_API_BASE_URL`
- Si la requête échoue, vérifier que FastAPI tourne bien sur l'URL configurée
- Si le backend change de port, mettre à jour `frontend/.env.local`

