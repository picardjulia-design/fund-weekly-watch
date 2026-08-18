# Weekly Fund Monitor

Application Streamlit de veille hebdomadaire sur les valeurs d'un fonds thématique.

## Fonctionnalités

- import d'un fichier CSV contenant les sources de la semaine ;
- récupération automatique des cours via yfinance ;
- calcul des variations quotidiennes ;
- calcul de la performance hebdomadaire ;
- lecture automatique des articles ;
- génération d'un commentaire via Mistral ;
- édition manuelle des commentaires valeur par valeur.

## Format du CSV hebdomadaire

Le fichier doit contenir trois colonnes :

ticker;title;url

Exemple :

XNAS:AAPL;Apple news;https://example.com/article
XNAS:MSFT;Microsoft news;https://example.com/article

## Clé Mistral

La clé API doit être enregistrée dans les Secrets Streamlit :

MISTRAL_API_KEY = "..."
