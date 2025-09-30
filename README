1. Objectif: créer une application pour traduite des docs office (docx, pptx) uploadé en conservant leur format

1.1 Indice: Il s'agit de dépackager le zip xml et de traduire balise par balise, et passer chaque paragraphe à un llm
1.2 Attention: à la prise en charge des mises en exergue (italique, blod) au sein de paragraphe, il faut le cas échéant
    assurer que le llm prenne en compte le paragraphe complet, en respectant les balises internes de mise en exergue sans rompre le sens.

2. archi
- UI Svelte
- Backend python
- LLM mistral
- CLI make (pour les target build test deploy)
- Always use docker for local dev env (no npm or pip install locally, use docker compose)
- Github action to execute make build test deploy targets
- Github pages for UI deployment and Scaleway container PaaS to deploy the python backend
- instruction IA pour l'instant dans le README avec un schema d'archi en mermaid

MISTRAL_API_KEY = clé mistral, teste si besoin
Tu as aussi en variables env et secrets :
SCW_ACCESS_KEY
SCW_SECRET_KEY
SCW_DEFAULT_ORGANIZATION_ID
SCW_DEFAULT_PROJECT_ID
SCW_NAMESPACE_ID

Fournis une première version avec UI backend test et déploiement fonctionnant de bout en bout.

Tu as comme model github pages + scw container le projet https://github.com/rhanka/nc-fullstack qui a un front svelte et un backend python une target make, docker, et un github action fonctionnant pour le deploiement. Je te suggère très fortement de t'inspirer du scaffolding de ce projet qui marche de bout en bout (la seule différence est l'utilisation de MISTRAL à la place d'OPENAI)

Mets bien à jour le README à la fin pour pouvoir itérer.

## Fonctionnalités

*   Traduction de fichiers texte brut (`.txt`, `.md`).
*   Traduction de documents DOCX en préservant les mises en forme complexes.
*   Interface web simple pour téléverser des fichiers et recevoir les traductions.
*   Traitement asynchrone pour gérer les fichiers volumineux sans blocage.
*   Mises à jour de la progression en temps réel.

## Traduction DOCX : Préservation Haute-Fidélité de la Mise en Forme

La traduction de fichiers DOCX tout en préservant la mise en forme est une tâche non triviale. Une simple extraction de texte supprime toutes les informations de style (gras, italique, couleurs, polices, hyperliens, etc.). Ce projet met en œuvre une méthodologie haute-fidélité de "Palette de Styles" pour surmonter ce défi.

### Le Défi Principal

Dans un fichier DOCX, la mise en forme est appliquée à un niveau granulaire appelé "run" (élément `<w:r>` dans le XML sous-jacent), qui est une séquence contiguë de caractères ayant un style identique. Un seul paragraphe peut contenir de nombreux "runs". Une approche naïve consistant à traduire le texte entier du paragraphe et à réappliquer un style "dominant" échoue car les traductions modifient l'ordre des mots et la structure des phrases, rendant impossible la réattribution correcte des styles au texte traduit.

### La Solution de la "Palette de Styles"

L'objectif est de donner pour instruction à un Grand Modèle de Langage (LLM) d'agir comme un éditeur méticuleux, préservant la structure originale tout en traduisant le contenu. Ceci est réalisé grâce à un processus en trois étapes : Déconstruction, Traduction par l'IA, et Reconstruction.

#### 1. Déconstruction et Génération du Prompt

Pour chaque paragraphe du document source :

1.  **Création d'une Palette de Styles** : Une "palette" unique de styles est générée. Le processus parcourt chaque "run" et chaque hyperlien à l'intérieur du paragraphe. Chaque combinaison unique de propriétés de mise en forme (gras, italique, souligné, couleur, taille de police, nom de la police, URL de l'hyperlien, etc.) est identifiée et se voit attribuer un identifiant simple et unique (par exemple, `[s1]`, `[s2]`).
2.  **Génération d'un Prompt Balisé** : Le contenu textuel du paragraphe est reconstruit en une chaîne de caractères pour le LLM. Chaque segment de texte est encapsulé dans les balises personnalisées correspondant à son ID de style de la palette.

**Exemple** :

Un paragraphe comme :
> Formé en tant qu'**ingénieur** de *recherche* en <a href="http://example.com">intelligence artificielle</a>...

Serait déconstruit en un prompt similaire à celui-ci :
> `[s1]Formé en tant qu'[/s1][s2]ingénieur[/s2][s1] de [/s1][s3]recherche[/s3][s1] en [/s1][s4]intelligence artificielle[/s4][s1]...[/s1]`

La palette de styles pour ce paragraphe mapperait :
*   `s1` : style de texte par défaut
*   `s2` : style de texte par défaut + gras
*   `s3` : style de texte par défaut + italique
*   `s4` : style de texte par défaut + hyperlien vers `http://example.com`

#### 2. L'IA en tant qu'Éditeur Méticuleux

Le prompt généré est envoyé au LLM avec une instruction système très spécifique. L'IA a pour ordre **non pas** de simplement traduire, mais de :
*   Préserver parfaitement les balises `[sX]` et leur placement autour du texte traduit correspondant.
*   Agir comme un éditeur pour consolider le texte sémantiquement lié mais structurellement fragmenté. Par exemple, si le document original contient `[s1]2[/s1][s2]3[/s2]` pour le nombre "23" (en raison d'une mise en forme différente sur chaque chiffre), l'IA est instruite pour fusionner intelligemment cela en une seule unité sémantique, comme `[s1]23[/s1]`.
*   Traduire uniquement le contenu textuel à l'intérieur des balises.

#### 3. Reconstruction Haute-Fidélité

À la réception de la chaîne de caractères traduite et balisée par l'IA :
1.  **Analyse de la Réponse** : Le backend analyse la réponse de l'IA, la divisant en segments de texte et leurs balises de style associées.
2.  **Effacement et Reconstruction** : Le contenu original du paragraphe dans l'objet `python-docx` est complètement effacé.
3.  **Reconstruction des Runs** : Le code parcourt les segments analysés. Pour chaque segment, il recherche l'ID de style (par exemple, `[s2]`) dans la palette de styles originale du paragraphe pour récupérer l'ensemble complet des propriétés de mise en forme. Il crée alors un **nouveau run** dans le paragraphe, applique toutes les propriétés originales et insère le segment de texte traduit.

Ce processus garantit que le document traduit est un clone structurel parfait de l'original, avec uniquement le contenu textuel modifié, assurant ainsi la plus haute fidélité possible.

### Performance : Traitement Asynchrone par Lots

Pour traiter efficacement les documents volumineux, les paragraphes sont regroupés en lots et envoyés simultanément à l'API de traduction à l'aide d'un client HTTP asynchrone. Un jeton séparateur unique et non ambigu (`[--translate-doc-paragraph-break--]`) est utilisé pour joindre les prompts des paragraphes, garantissant que l'IA puisse traiter plusieurs paragraphes en un seul appel et les retourner dans le bon ordre pour la reconstruction.

## Pour Commencer

### Prérequis

*   Docker et Docker Compose
*   Une clé d'API Mistral AI

### Installation et Exécution
