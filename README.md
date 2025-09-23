# Translate Doc

Translate Doc est une application full-stack qui permet d'uploader des documents texte (Markdown, HTML, texte brut, JSON/YAML...) et de les traduire en conservant leur format. L'interface web est réalisée avec Svelte, le backend repose sur FastAPI et les traductions sont effectuées via l'API Mistral.

## Architecture

```mermaid
flowchart LR
    subgraph Client
        UI[Svelte UI]
    end

    subgraph Infrastructure
        FE[GitHub Pages]
        BE[Scaleway Container]
    end

    subgraph Services
        API[(Translate Doc API\nFastAPI)]
        Mistral[(Mistral LLM API)]
    end

    UI -->|HTTP (fetch)| FE
    FE -->|Reverse proxy| API
    API -->|REST /translate| Mistral
    API -->|Static assets| FE
```

- **Frontend** : Svelte + Vite, construit puis publié sur GitHub Pages.
- **Backend** : FastAPI empaqueté dans un conteneur Docker et déployé sur Scaleway Container.
- **LLM** : API `chat/completions` de Mistral (`mistral-large-latest` par défaut).
- **CI/CD** : GitHub Actions exécute `make build`, `make test` et `make deploy` puis publie.

## Prérequis

- Docker et Docker Compose pour le développement local.
- Un compte Mistral avec une clé API disponible dans la variable d'environnement `MISTRAL_API_KEY`.
- Accès Scaleway : `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_ORGANIZATION_ID`, `SCW_DEFAULT_PROJECT_ID`, `SCW_NAMESPACE_ID`.

Créez un fichier `.env` à la racine avec les secrets nécessaires pour le backend :

```bash
MISTRAL_API_KEY=sk-...
MISTRAL_MODEL=mistral-large-latest
MISTRAL_API_BASE=https://api.mistral.ai/v1
```

## Démarrage local

Toute l'expérience de dev se fait via Docker :

```bash
make up           # démarre frontend + backend en mode hot-reload
make down         # stoppe les conteneurs
```

Les services exposent :

- UI : http://localhost:5173
- API : http://localhost:8000

## Tests

Les tests s'exécutent dans des conteneurs éphémères :

```bash
make test         # lance pytest côté backend et vitest côté frontend
```

## Commandes Make principales

| Commande      | Description                                                |
|---------------|------------------------------------------------------------|
| `make build`  | Build des images Docker frontend (build) et backend (prod) |
| `make test`   | Tests frontend + backend                                   |
| `make up`     | Lancement de l'environnement de dev                         |
| `make down`   | Arrêt des services                                         |
| `make deploy` | Déploiement complet : backend Scaleway + build frontend    |

## Déploiement

### Backend (Scaleway Container)

Le script `scripts/deploy_backend.sh` :

1. Récupère l'endpoint du registre du namespace Scaleway.
2. Build l'image Docker `backend/Dockerfile` (stage `prod`).
3. Authentifie Docker via `scw registry login`.
4. Pousse l'image taggée (`git rev-parse --short HEAD`).
5. Met à jour le conteneur Scaleway cible (`BACKEND_CONTAINER_NAME`, `translate-doc-backend` par défaut).
6. Attend que le déploiement soit en statut `ready`.

Variables importantes :

- `SCW_NAMESPACE_ID` (obligatoire)
- `BACKEND_IMAGE_NAME` (optionnel, `translate-doc-backend` par défaut)
- `BACKEND_CONTAINER_NAME`
- `IMAGE_TAG` (override possible)

### Frontend (GitHub Pages)

`make deploy` appelle `scripts/build_frontend.sh` qui :

1. Installe les dépendances (`npm ci`).
2. Construit le bundle (`npm run build`).
3. Expose le dossier `frontend/dist` prêt à être uploadé par GitHub Pages.

Définissez `VITE_API_BASE_URL` lors du build pour pointer vers le backend déployé (ex : `https://api.example.com`).

### GitHub Actions

Le workflow CI :

1. Checkout du dépôt.
2. Exécution des cibles `make build`, `make test`, `make deploy`.
3. Publication du frontend sur GitHub Pages via `actions/deploy-pages`.
4. Déploiement du backend via Scaleway CLI (`scaleway/action-scw`).

Les secrets nécessaires doivent être configurés dans GitHub :

- `MISTRAL_API_KEY`
- `SCW_ACCESS_KEY`
- `SCW_SECRET_KEY`
- `SCW_DEFAULT_ORGANIZATION_ID`
- `SCW_DEFAULT_PROJECT_ID`
- `SCW_NAMESPACE_ID`
- `SCW_CONTAINER_NAME` (optionnel)
- `VITE_API_BASE_URL` (pour le build front en production)

## API

### `POST /translate`

- **Body** : `multipart/form-data`
  - `file` (obligatoire) : fichier texte/markdown/html/json/yaml
  - `target_language` (obligatoire) : langue souhaitée (ex. `French`)
- **Réponse** (`200`) :

```json
{
  "filename": "document.french.md",
  "translated_text": "..."
}
```

Codes d'erreur :

- `400` : fichier vide / encodage non supporté
- `502` : erreur de traduction (Mistral indisponible, clé absente...)

### `GET /health`

Renvoie `{ "status": "ok" }`.

## UI

- Upload d'un fichier, choix de la langue, appel au backend.
- Affichage du texte traduit avec possibilité de téléchargement.
- Style responsive simple sans dépendances supplémentaires.

## Tests unitaires

- **Backend** : `pytest` couvre le service de traduction et la route `/translate` (via `TestClient`).
- **Frontend** : `vitest` mocke `fetch` et vérifie la fonction `translateDocument`.

## Aller plus loin

- Supporter les fichiers binaires (`.docx`, `.pptx`) via libs dédiées.
- Historiser les traductions côté backend avec base de données.
- Authentification des utilisateurs.
- Ajout d'un mode "batch" pour plusieurs documents.

## Licence

MIT
