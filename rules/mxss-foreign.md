# [PAI] mxss-foreign.md (IA) — PROFIL ISOLÉ : confusion de namespace (HTML/MathML/SVG + points d'intégration).
# C'est la classe historiquement à l'origine des bypass DOMPurify (confusion de namespace).
# <mxss_payload> lié à <mxss_foreign_confusion> (le wrapper <template> reste inclus, c'est une
# composante légitime de la technique, pas du bruit foster/AFE). Lançable seul : -g mxss-foreign.md
!include mxss-vocab.md

<mxss_payload nonrecursive=true p=0.1> = <lt>a<gt>SAFE FALLBACK AFTER TOO LONG RECURSION<lt>/a<gt>
<mxss_payload> = <mxss_foreign_confusion>

<HTMLmxssElement root=true> = <mxss_payload>
