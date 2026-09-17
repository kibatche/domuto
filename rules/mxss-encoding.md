# mxss-encoding.md (IA) — PROFIL ISOLÉ : axe entités/encodage + états de commentaire + CDATA.
# Coeur du canon mXSS (asymétrie parse -> sérialise -> reparse). ATTENTION : invisible à un harness
# qui ne fait qu'UN parse (diff_compare.py actuel) — exige un banc round-trip (PHP DOM -> innerHTML
# -> reparse navigateur -> compare) pour produire des findings. Lançable seul : -g mxss-encoding.md
!include mxss-vocab.md

<mxss_payload nonrecursive=true p=0.1> = <lt>a<gt>SAFE FALLBACK AFTER TOO LONG RECURSION<lt>/a<gt>
<mxss_payload> = <mxss_encoding>
<mxss_payload> = <mxss_comment>

<HTMLmxssElement root=true> = <mxss_payload>
