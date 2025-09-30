# Translate Doc

Application full-stack pour traduire des fichiers texte, DOCX et PPTX en préservant leur mise en forme, construite avec un front-end Svelte et un back-end FastAPI. La traduction est confiée au modèle Mistral via des appels asynchrones et la conservation des styles est assurée par une "palette de styles" appliquée run par run.

## Architecture

```mermaid
flowchart TD
    A[UI Svelte<br/>Github Pages] -->|HTTP| B[FastAPI Backend<br/>Scaleway Container]
    B -->|Async LLM Calls| C[Mistral API]
    B --> D[Stockage local (.data)]
    subgraph Local Dev
        E[docker compose]
        E --> A
        E --> B
    end
```

### Composants

- **frontend/** : application Svelte (Vite) pour téléverser les fichiers, visualiser la progression et télécharger le résultat.
- **backend/** : API FastAPI gérant les uploads, le suivi de jobs et la traduction haute-fidélité des fichiers texte, DOCX et PPTX.
- **docker-compose.yml** : environnement de développement local complet.
- **Makefile** : commandes clés (`build`, `test`, `deploy`, etc.).
- **.github/workflows/ci.yml** : pipeline CI exécutant build, tests et déploiement.

## Traduction DOCX/PPTX à Haute Fidélité

La conservation de la mise en forme est assurée en trois étapes :

1. **Déconstruction** : chaque paragraphe est parcouru run par run. Une palette de styles (`s1`, `s2`, …) capture les attributs (gras, italique, taille, couleur, etc.). Le texte est envoyé au LLM encapsulé dans des balises `<sX>...</sX>`.
2. **Traduction** : le prompt guide Mistral pour traduire en français tout en conservant strictement les balises et en fusionnant intelligemment les segments de sens.
3. **Reconstruction** : les balises retournées sont analysées, le paragraphe est vidé et reconstruit run par run en réappliquant exactement la palette de styles d'origine.

Le traitement est effectué par lots avec le séparateur `[--translate-doc-paragraph-break--]` afin d'accélérer les appels au LLM tout en garantissant l'ordre et la synchronisation.

Cette approche est identique pour les fichiers DOCX et PPTX, en s'appuyant respectivement sur `python-docx` et `python-pptx`.

## Prérequis

- Docker et Docker Compose
- Accès API Mistral (`MISTRAL_API_KEY`)
- Accès au Container Registry Scaleway (`SCW_*`)
- GitHub token (fourni automatiquement dans GitHub Actions)

## Variables d'environnement

Copiez `.env.example` pour créer votre `.env` puis renseignez les valeurs :

| Variable | Description |
| --- | --- |
| `MISTRAL_API_KEY` | Clé d'API Mistral pour le back-end |
| `VITE_BACKEND_URL` | URL publique du back-end pour le front |
| `FRONTEND_ORIGIN` | Origine autorisée (CORS) côté back |
| `SCW_ACCESS_KEY`, `SCW_SECRET_KEY` | Identifiants Scaleway |
| `SCW_DEFAULT_ORGANIZATION_ID`, `SCW_DEFAULT_PROJECT_ID` | Contexte Scaleway |
| `SCW_NAMESPACE_ID` | Namespace du registre container |
| `SCW_BACKEND_CONTAINER_ID` | Identifiant du container managé Scaleway |

## Démarrage local

```bash
cp .env.example .env
make build
make up
```

- Frontend : http://localhost:5173
- Backend : http://localhost:8000

Pour arrêter : `make down`

Ou lancez le tout en une seule commande : `make dev`.

## Tests

```bash
make test
```

Les tests s'exécutent dans le container backend via `pytest` et couvrent la reconstruction haute-fidélité des runs DOCX ainsi que le pipeline de traduction texte.

Pour repartir de zéro : `make clean`.

## Déploiement

La cible `make deploy` orchestre l'ensemble du déploiement Dockerisé :

```bash
make deploy
```

1. **Frontend** : build dans un container Node, puis publication sur la branche `gh-pages` via `npx gh-pages`.
2. **Backend** : build de l'image `backend` (target `production`), push sur le registre Scaleway, puis déploiement via `scw container container deploy`.

> Définissez `SKIP_FRONTEND_DEPLOY=1` ou `SKIP_BACKEND_DEPLOY=1` pour ne déployer qu'un seul composant.

## CI/CD

Le workflow GitHub Actions (`ci.yml`) exécute :

1. `make build`
2. `make test`
3. `make deploy` (uniquement sur `main`)

Assurez-vous de configurer les secrets GitHub (`SCW_*`, `GITHUB_TOKEN` automatique) pour permettre le déploiement.

## API

- `POST /api/jobs` : téléverse un fichier et crée un job de traduction.
- `GET /api/jobs/{job_id}` : état courant d'un job (progression, message, statut).
- `GET /api/jobs` : historique récent des jobs (ordre décroissant).
- `GET /api/jobs/{job_id}/result` : téléchargement du fichier traduit.
- `GET /health` : vérification de l'état du service.

Les fichiers traduits sont stockés dans `.data/<job_id>/` avec le suffixe `_translated`.

## Roadmap

- Gestion des hyperliens DOCX/PPTX au niveau run.
- Support de formats supplémentaires (XLSX, PDF texte).
- Persistance des jobs (base de données) et notifications temps réel (SSE/WebSocket).
