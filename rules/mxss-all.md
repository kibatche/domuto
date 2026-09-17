# mxss-all.md (IA) — GLOBAL : découverte en largeur par composition des profils.
# N'inclut PAS de vocabulaire : chaque profil est autonome (il !include déjà mxss-vocab.md).
# Ici on les !import comme sous-grammaires et la racine en tire un au hasard (pondéré).
# -> reconstitue la couverture large, mais par assemblage de classes isolées, pas une méga-grammaire.
# Pour étudier UNE classe, lance le profil directement (-g mxss-foster.md, etc.).
# Lancement : -g mxss-all.md
!import mxss-foreign.md
!import mxss-afe.md
!import mxss-foster.md
!import mxss-encoding.md
!import mxss-rawtext.md
!import mxss-findings.md

<HTMLmxssElement root=true p=0.24> = <import from=mxss-foreign.md>
<HTMLmxssElement root=true p=0.24> = <import from=mxss-afe.md>
<HTMLmxssElement root=true p=0.20> = <import from=mxss-foster.md>
<HTMLmxssElement root=true p=0.16> = <import from=mxss-encoding.md>
<HTMLmxssElement root=true p=0.10> = <import from=mxss-rawtext.md>
<HTMLmxssElement root=true p=0.06> = <import from=mxss-findings.md>
