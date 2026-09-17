# domuto

Un fuzzer différentiel de parseurs HTML, spécialisé dans la recherche de mutations (mXSS).

domuto génère du HTML à partir de grammaires formelles, le fait analyser par trois parseurs
différents, et ne conserve que les cas où leurs arbres DOM divergent. Une divergence entre deux
parseurs placés de part et d'autre d'un assainisseur est le mécanisme de base d'une mutation XSS :
ce qu'un parseur lit comme du texte, l'autre le lit comme du balisage.

Les trois parseurs comparés sont `DOMParser` dans Firefox, le DOM de PHP 8.4, et Lexbor 2.7.0.

---

## Crédit

**Le moteur génératif est le travail d'Ivan Fratric (Google Project Zero), pas le mien.**

- Projet d'origine : [Domato](https://github.com/googleprojectzero/domato)
- Auteur : Ivan Fratric, `<ifratric@google.com>`
- Copyright 2017 Google Inc. All Rights Reserved.
- Licence : Apache License 2.0 — voir `LICENSE`

Domato est un fuzzer de DOM generation-based dont le moteur de grammaire est remarquable : un
format de règles minuscule, une gestion propre de la récursion, des probabilités normalisées, et
une expressivité suffisante pour décrire la quasi-totalité du HTML, du SVG et de MathML. C'est
cette pièce-là que ce dépôt réutilise.

Ce dépôt n'est pas un fork GitHub de Domato mais un dépôt autonome, parce que la quasi-totalité de
Domato en a été retirée : il ne reste que le moteur. Ce n'est pas un produit Google, et Ivan
Fratric n'y est pour rien au-delà du moteur qu'il a écrit.

### Ce qui vient de Domato

| Fichier | État |
|---|---|
| `grammar.py` | moteur de grammaire, conservé et réduit |
| `generator.py` | point d'entrée, largement réécrit ; ne reste que le chargement de grammaire |
| `rules/html.txt.original` | grammaire HTML d'origine gardée comme référence, à sept commentaires près qui neutralisent des symboles fantômes (`<HTMLMenuElement>`, `<attribute_contextmenu>`, `<attribute_menu>`) jamais définis dans Domato |
| `rules/css.txt`, `common.txt`, `svg.txt`, `mathml.txt`, `attributevalues.txt`, `tagattributes.txt`, `svgattrvalues.txt`, `mathmlattrvalues.txt`, `cssproperties.txt` | grammaires d'origine, non modifiées |
| `LICENSE`, `CONTRIBUTING.md` | d'origine |

### Ce qui a été ajouté

| Fichier | Rôle |
|---|---|
| `diff_compare.py` | comparateur différentiel des trois parseurs, cœur de l'outil |
| `analyze_findings.py` | rejoue les divergences enregistrées et détaille le contexte DOM |
| `rules/mxss.md` | grammaire des payloads de mutation |
| `rules/mxss-*.md` | grammaires ciblées par famille, chacune lançable seule via `-g` : agence d'adoption et éléments de formatage actifs (`mxss-afe.md`), foreign content (`mxss-foreign.md`), foster parenting (`mxss-foster.md`), raw text (`mxss-rawtext.md`), encodage (`mxss-encoding.md`), plus le vocabulaire partagé inclus par toutes (`mxss-vocab.md`) |
| `rules/html.txt` | grammaire HTML modifiée pour le contexte mXSS |

### Ce qui a été retiré

La génération de JavaScript de Domato (`!begin lines`, `<lines count=N>`, `!varformat`,
`!lineguard`, réutilisation de variables typées), son mécanisme de template HTML
(`<htmlfuzzer>` / `<jsfuzzer>` / `<cssfuzzer>`), les fonctions Python embarquées
(`beforeoutput`, `<call>`), et les grammaires JS. domuto ne produit que du balisage :
la comparaison porte sur l'arbre DOM, pas sur l'exécution.

Conformément à l'article 4(b) de la licence Apache 2.0, les fichiers modifiés portent une mention
de modification et les en-têtes de copyright d'origine sont conservés.

---

## Prérequis

domuto ne fonctionne pas seul : il interroge un serveur PHP externe qui expose les deux
implémentations Lexbor.

1. **Python 3.10 ou plus** — le code utilise la syntaxe `str | None`. Testé avec 3.14.
2. **Playwright et son Firefox**, pour le parseur navigateur. C'est bien Firefox et non Chromium :
   `diff_compare.py` et `analyze_findings.py` appellent `pw.firefox.launch()`.
3. **`requests`**, pour parler au serveur PHP.
4. **Le serveur PHP `lexborParser.php`**, écouté sur `http://127.0.0.1:5000`. Il ne vit pas dans
   ce dépôt : il fait partie du projet `MXSS_HtmlSanitizer_Symfony`, sous `backend/`, avec les
   binaires `php-8.4.18` et `lexbor_tree-2.7.0`. Sans lui, chaque comparaison échoue sur
   `[ERROR] PHP server unreachable`.

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install firefox
```

Démarrer ensuite le serveur PHP du projet `MXSS_HtmlSanitizer_Symfony` sur le port 5000, puis
vérifier qu'il répond :

```bash
curl -s -X POST http://127.0.0.1:5000/lexborParser.php \
  -H 'Content-Type: application/json' \
  -d '{"html":"<p>x</p>","lexborVersion":"2.7.0"}'
```

## Usage

```bash
# 100 comparaisons avec la grammaire HTML complète
.venv/bin/python generator.py

# Grammaire mXSS ciblée, 5000 tirages
.venv/bin/python generator.py --grammar mxss.md --number 5000

# Grammaire de base enrichie d'un overlay (le fichier d'overlay ne déclare pas de racine)
.venv/bin/python generator.py --grammar html.txt --overlay mxss-foreign.md

# Conserver tous les HTML générés, divergence ou non
.venv/bin/python generator.py --write-html True
```

| Option | Défaut | Rôle |
|---|---|---|
| `-g`, `--grammar` | `html.txt` | Fichier de grammaire, relatif à `rules/` |
| `-o`, `--overlay` | aucun | Grammaire supplémentaire chargée dans le même objet après la base ; elle étend les symboles existants et ne doit pas déclarer de racine |
| `-n`, `--number` | `100` | Nombre d'échantillons comparés |
| `-w`, `--write-html` | `False` | Écrire chaque HTML généré dans `generated_files/` |
| `-s`, `--sample-per-run` | `20` | Nombre d'expansions de la racine concaténées dans un même document |

Les divergences sont écrites dans `findings/`, qui n'est pas versionné. Pour les rejouer avec le
détail des arbres :

```bash
.venv/bin/python analyze_findings.py
```

La syntaxe des grammaires est décrite dans `USAGE.md`.

## Debug

- La progression s'écrit sur la sortie standard, en ligne réécrite (`\r`) : rediriger vers un
  fichier produit une seule ligne illisible. Pour garder une trace, préférer
  `--write-html True` et l'inspection de `generated_files/`.
- `[ERROR] PHP server unreachable` signifie que le port 5000 ne répond pas. Le fuzzing continue
  alors sans jamais rien trouver : la fonction renvoie « pas de divergence » sur erreur réseau.
- `[WARN] Could not locate <body>` indique que le serveur a rendu un arbre sans `<body>`,
  généralement sur un HTML dégénéré. L'échantillon est ignoré.
- Une valeur élevée de `--sample-per-run` combinée à une grammaire récursive produit des documents
  très lourds qui peuvent faire tomber le serveur PHP. La valeur par défaut de 20 est un compromis.
- Playwright garde une page ouverte et la recycle toutes les 500 comparaisons
  (`_PAGE_RESTART_EVERY` dans `diff_compare.py`) pour libérer la mémoire du moteur JS ; une fuite
  observée au-delà de quelques milliers d'itérations vient généralement de là.

## Licence

Apache License 2.0, comme le projet d'origine. Voir `LICENSE`.

Ce n'est pas un produit officiel Google.
