#   Domato - main generator script
#   --------------------------------------
#
#   Written and maintained by Ivan Fratric <ifratric@google.com>
#
#   Copyright 2017 Google Inc. All Rights Reserved.
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from __future__ import print_function
import os
import argparse
from pathlib import Path

from grammar import Grammar

def _load_grammar(grammar_file: str, overlay_file: str | None = None) -> Grammar | None:
    """Load any grammar inside the main html grammar.

    If overlay_file is given, it is parsed into the SAME Grammar object after the
    base. domato appends rules per symbol (grammar.py: _creators[...].append) and
    re-normalises probabilities on each parse, so the overlay extends <mxss_payload>
    and any shared pool without clobbering the base. The overlay must NOT declare a
    root=true rule (the base owns the root).
    """

    grammar_dir = os.path.join(os.path.dirname(__file__), 'rules')
    grammar = Grammar()
    err = grammar.parse_from_file(os.path.join(grammar_dir, grammar_file))
    if err > 0:
        print(f'There were errors parsing grammar: {grammar_file}')
        return None

    # composition base + overlay (même objet Grammar)
    if overlay_file:
        err = grammar.parse_from_file(os.path.join(grammar_dir, overlay_file))
        if err > 0:
            print(f'There were errors parsing overlay grammar: {overlay_file}')
            return None

    if grammar_file == 'html.txt':
        cssgrammar = Grammar()
        cssgrammar.parse_from_file(os.path.join(grammar_dir, 'css.txt'))
        if err > 0:
            print(f'There were errors parsing grammar: {grammar_file}')
            return None
        grammar.add_import('cssgrammar', cssgrammar)
    return grammar

def _apply_diff_attrs(htmlgrammar: Grammar):
    """Silence tag-specific *_attributes symbols to reduce diff noise.
    Preserves <attributes> and <attributestring> so mXSS payloads stay active.
    """
    lines = []
    _ATTR_EXCEPTIONS = {'attributes', 'attributestring', 'attributechar'}
    _ATTR_SINGLETONS  = {'animateattr', 'setattr'}
    for sym in list(htmlgrammar._creators):
        if sym in _ATTR_EXCEPTIONS:
            continue
        if (sym.endswith('_attributes')
                or sym.startswith(('svgattrs_', 'svgattrx_', 'mathmlattrs_'))
                or sym in _ATTR_SINGLETONS):
            lines.append(f'<{sym} p=100> = ')
    if not lines:
        return
    err = htmlgrammar.parse_from_string('\n'.join(lines) + '\n')
    if err > 0:
        print(f'Warning: {err} error(s) injecting diff attribute rules')

def generate(grammar_file='html.txt', count=100, generate_file_mode=False, sample_per_run=20, overlay_file=None):
    """Compare DOMParser, PHP DOM, and Lexbor 2.7.0.
    Saves HTML to findings/ only on divergence.
    """
    try:
        from diff_compare import DiffComparator
    except ImportError as e:
        print(f"[ERROR] Could not import diff_compare: {e}")
        print("Make sure you are running with .venv/bin/python")
        return

    htmlgrammar = _load_grammar(grammar_file=grammar_file, overlay_file=overlay_file)
    #Noisy
    # cssgrammar = _load_grammar(grammar_file='css.txt')
    if htmlgrammar is None:
        return
    _apply_diff_attrs(htmlgrammar)

    findings_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'findings'
    output_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'generated_files'
    found = 0
    
    print(f"[DIFF] Starting differential comparison — {count} samples")
    print(f"[DIFF] Findings will be saved to: {findings_dir}/", end='\n\n')
    
    with DiffComparator(findings_dir) as cmp:
        for i in range(1, count + 1):
            fragment = '\n'.join(htmlgrammar.generate_root() for _ in range(sample_per_run))
            html = f'<!DOCTYPE html><html><body>{fragment}</body></html>'
            # Noisy
            # css = cssgrammar.generate_symbol('rules')
            # html = html.replace('<cssfuzzer>', css)
            diverged = cmp.compare(html)
            if diverged:
                found += 1
            else:
                print(f"\r[DIFF] {i}/{count} — findings: {found}", end='', flush=True)
            if generate_file_mode == True:
                outfile = os.path.join(output_dir, f'fuzz-{str(i).zfill(5)}.html')
                with open(outfile, 'w') as f:
                    f.write(html)

    print(f"")
 
    print(f"\n\n[DIFF] Done. {found} divergence(s) found in {count} samples.\n[DIFF] See: {findings_dir}/") if found \
        else print("[Diff] Everything seems to be OK !")

def get_argument_parser():
    
    parser = argparse.ArgumentParser(description="DOMUTO (A DOM MUTATION FUZZER)")

    parser.add_argument('-g', '--grammar', type=str, default='html.txt', metavar='FILE',
                    help='Grammar file that will be used, relative to rules/ (default: html.txt)')
    # — overlay optionnel chargé par-dessus la grammaire de base (append)
    parser.add_argument('-o', '--overlay', type=str, default=None, metavar='FILE',
                    help='Optional overlay grammar parsed into the same object after -g (relative to rules/). Must not declare a root.')
    parser.add_argument('-n', '--number', type=int, default=100, metavar='N',
                    help='Number of samples that will be generated (default: 100). If --write-html is True, X files will be generated from the html AND X html string will be compared.')
    parser.add_argument('-w', '--write-html', type=bool, default=False,
                    help='Wether to write generated html in `generated_files` directory or not, no matter if a diff was found.')
    parser.add_argument('-s', '--sample-per-run', type=int, default=20,
                    help='Will generate X time the `root` element inside the grammar file. If you have recursion in it, with a large number (ie 100), the generated html will likely break the targeted server. Default to 20.')
    return parser

def main():

    parser = get_argument_parser()

    args = parser.parse_args()

    generate(grammar_file=args.grammar, count=args.number, generate_file_mode=args.write_html, sample_per_run=args.sample_per_run, overlay_file=args.overlay)

if __name__ == '__main__':
    
    main()
