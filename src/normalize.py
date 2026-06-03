"""
normalize.py — Normalisation des libellés d'indicateurs financiers.

Le fichier SFBT contient ~294 variantes de libellés pour un nombre bien plus
petit de concepts réels (ex. « Résultat net de l'exercice » s'écrit de 15
façons : espaces insécables \\xa0, retours ligne, accents « aprés/après »,
astérisques « (*) », abréviations...).

Deux niveaux sont fournis :
  1. clean_label()  -> libellé LISIBLE et propre (pour affichage).
  2. cle_indicateur() -> CLÉ agressive (minuscule, sans accent ni ponctuation)
       servant de clé de jointure pour reconstituer les séries temporelles.
       C'est elle qui fusionne mécaniquement la grande majorité des variantes.

Les variantes restantes (abréviations divergentes) sont traitées via un
dictionnaire d'alias curé : ALIAS (clé brute normalisée -> clé canonique).
"""

import re
import unicodedata

# Espaces « exotiques » à ramener à un espace standard.
_ESPACES = {
    "\xa0": " ",   # espace insécable
    " ": " ", # espace fine insécable
    "\t": " ",
    "\n": " ",
    "\r": " ",
}


def clean_label(texte) -> str:
    """Nettoie un libellé pour AFFICHAGE : conserve accents et casse, mais
    supprime le bruit (espaces multiples/insécables, retours ligne, astérisques
    et annotations de bas de page, espaces avant ponctuation)."""
    if texte is None:
        return ""
    s = str(texte)
    for k, v in _ESPACES.items():
        s = s.replace(k, v)
    # Supprime les annotations de note de bas de page : (*), (**), * en fin, etc.
    s = re.sub(r"\(\*+\)", " ", s)        # (*) (**)
    s = re.sub(r"\*+", " ", s)            # astérisques isolés
    s = re.sub(r"\s*;\s*", " ", s)        # ';' parasites (ex. « financ . »)
    s = re.sub(r"\s+", " ", s)            # espaces multiples -> simple
    s = re.sub(r"\s+([.,])", r"\1", s)    # espace avant point/virgule
    return s.strip(" .")


def cle_indicateur(texte) -> str:
    """Clé de regroupement AGRESSIVE : minuscule, sans accent, sans ponctuation,
    sans espace. Fusionne « Résultat\\xa0net de l'exercice », « Résultat Net de
    l'exercice », « Résultat net de  l'exercice » -> 'resultatnetdelexercice'.
    """
    s = clean_label(texte).lower()
    # Décompose les accents puis retire les diacritiques.
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Apostrophes typographiques -> rien ; tout caractère non alphanumérique -> rien.
    s = s.replace("’", "").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


# --- Dictionnaire d'alias curé ------------------------------------------------
# Pour les variantes que la normalisation NE fusionne pas (abréviations,
# reformulations). Clé = cle_indicateur(variante) ; Valeur = cle_indicateur du
# libellé de référence. Étendre au fil de la validation métier (avec Malik).
# Exemple typique : « Résultat des activités ordinaires avant réinvestis. et
# impôt » vs « ...avant réinvestissements et impôt ».
ALIAS_RAW = {
    # variante (telle qu'écrite) : libellé de référence
    "Résultat des activités ordinaires avant réinvestis. et impôt":
        "Résultat des activités ordinaires avant réinvestissements et impôt",
    "Résultat des activités ordinaires avant réinvesti.s et impôt":
        "Résultat des activités ordinaires avant réinvestissements et impôt",
    "Résultat des activités ordinaires avant réinvestis et impôt":
        "Résultat des activités ordinaires avant réinvestissements et impôt",
    "Résultat des activités ordinaires avant réinvest et impôt":
        "Résultat des activités ordinaires avant réinvestissements et impôt",
    "Résultat des activités ordinaires avant réinvest. et impôt":
        "Résultat des activités ordinaires avant réinvestissements et impôt",
    "Immobilisations incorporelle":
        "Immobilisations incorporelles",
    "Résultat net de la période":
        "Résultat net de l'exercice",
    "Résultat de la période":
        "Résultat de l'exercice",
    "RESULTAT NET DE LA PERIODE":
        "Résultat net de l'exercice",
    "RESULTAT NET DE L'EXERCICE":
        "Résultat net de l'exercice",
    "Résultat Net":
        "Résultat net de l'exercice",
    "Résultat net":
        "Résultat net de l'exercice",
}

# Pré-calcule la table {clé_normalisée_variante : clé_normalisée_référence}.
ALIAS = {cle_indicateur(k): cle_indicateur(v) for k, v in ALIAS_RAW.items()}


def cle_canonique(texte) -> str:
    """Clé finale après application des alias curés."""
    k = cle_indicateur(texte)
    return ALIAS.get(k, k)


if __name__ == "__main__":
    # Démonstration rapide.
    exemples = [
        "Résultat net de l'exercice",
        "RESULTAT\xa0NET\xa0DE\xa0L'EXERCICE",
        "Résultat net de  l'exercice",
        "Résultat Net de l'exercice",
        "Résultat net de l’exercice",
        "Résultat net de la période",
        "Fournisseurs et comptes rattachés  (*)",
        "Autres passifs courants                                                             *",
    ]
    for e in exemples:
        print(f"{cle_canonique(e):35s} <- {e!r}")
