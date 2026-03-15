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
import gc  # [PAI] periodic GC in diff loop
import os
import re
import random
import argparse
from pathlib import Path

from grammar import Grammar
from svg_tags import _SVG_TYPES
from html_tags import _HTML_TYPES
from mathml_tags import _MATHML_TYPES

_N_MAIN_LINES = 1000
_N_EVENTHANDLER_LINES = 500

_N_ADDITIONAL_HTMLVARS = 5

def generate_html_elements(ctx, n):
    for i in range(n):
        tag = random.choice(list(_HTML_TYPES))
        tagtype = _HTML_TYPES[tag]
        ctx['htmlvarctr'] += 1
        varname = 'htmlvar%05d' % ctx['htmlvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': tagtype})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + tagtype + '} */ var ' + varname + ' = document.createElement(\"' + tag + '\"); //' + tagtype + '\n'


def add_html_ids(matchobj, ctx):
    tagname = matchobj.group(0)[1:-1]
    if tagname in _HTML_TYPES:
        ctx['htmlvarctr'] += 1
        varname = 'htmlvar%05d' % ctx['htmlvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': _HTML_TYPES[tagname]})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + _HTML_TYPES[tagname] + '} */ var ' + varname + ' = document.getElementById(\"' + varname + '\"); //' + _HTML_TYPES[tagname] + '\n'
        return matchobj.group(0) + 'id=\"' + varname + '\" '
    elif tagname in _SVG_TYPES:
        ctx['svgvarctr'] += 1
        varname = 'svgvar%05d' % ctx['svgvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': _SVG_TYPES[tagname]})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + _SVG_TYPES[tagname] + '} */ var ' + varname + ' = document.getElementById(\"' + varname + '\"); //' + _SVG_TYPES[tagname] + '\n'
        return matchobj.group(0) + 'id=\"' + varname + '\" '
    elif tagname in _MATHML_TYPES:
        ctx['mathmlvarctr'] += 1
        varname = 'mathmlvar%05d' % ctx['mathmlvarctr']
        ctx['htmlvars'].append({'name': varname, 'type': _MATHML_TYPES[tagname]})
        ctx['htmlvargen'] += '/* newvar{' + varname + ':' + _MATHML_TYPES[tagname] + '} */ var ' + varname + ' = document.getElementById(\"' + varname + '\"); //' + _MATHML_TYPES[tagname] + '\n'
        return matchobj.group(0) + 'id=\"' + varname + '\" '
    else:
        return matchobj.group(0)


def generate_function_body(jsgrammar, htmlctx, num_lines):
    js = ''
    js += 'var fuzzervars = {};\n\n'
    js += "SetVariable(fuzzervars, window, 'Window');\nSetVariable(fuzzervars, document, 'Document');\nSetVariable(fuzzervars, document.body.firstChild, 'Element');\n\n"
    js += '//beginjs\n'
    js += htmlctx['htmlvargen']
    js += jsgrammar._generate_code(num_lines, htmlctx['htmlvars'])
    js += '\n//endjs\n'
    js += 'var fuzzervars = {};\nfreememory()\n'
    return js


def check_grammar(grammar):
    """Checks if grammar has errors and if so outputs them.
    Args:
      grammar: The grammar to check.
    """

    for rule in grammar._all_rules:
        for part in rule['parts']:
            if part['type'] == 'text':
                continue
            tagname = part['tagname']
            # print tagname
            if tagname not in grammar._creators:
                print('No creators for type ' + tagname)


def generate_new_sample(template, htmlgrammar, cssgrammar, jsgrammar):
    """Parses grammar rules from string.
    Args:
      template: A template string.
      htmlgrammar: Grammar for generating HTML code.
      cssgrammar: Grammar for generating CSS code.
      jsgrammar: Grammar for generating JS code.
    Returns:
      A string containing sample data.
    """

    result = template

    css = cssgrammar.generate_symbol('rules')
    html = htmlgrammar.generate_symbol('bodyelements')

    htmlctx = {
        'htmlvars': [],
        'htmlvarctr': 0,
        'svgvarctr': 0,
        'mathmlvarctr': 0,
        'htmlvargen': ''
    }
    html = re.sub(
        r'<[a-zA-Z0-9_-]+ ',
        lambda match: add_html_ids(match, htmlctx),
        html
    )
    generate_html_elements(htmlctx, _N_ADDITIONAL_HTMLVARS)

    result = result.replace('<cssfuzzer>', css)
    result = result.replace('<htmlfuzzer>', html)

    handlers = False
    while '<jsfuzzer>' in result:
        numlines = _N_MAIN_LINES
        if handlers:
            numlines = _N_EVENTHANDLER_LINES
        else:
            handlers = True
        result = result.replace(
            '<jsfuzzer>',
            generate_function_body(jsgrammar, htmlctx, numlines),
            1
        )

    return result


# [PAI] BEGIN — inject nesting rules into grammar based on --max-nest value
# 4 container tags: enough variety, small enough to keep base-case probability sane.
_NEST_WRAP_TAGS = [
    ('div',        'attributes'),
    ('form',       'form_attributes'),
    ('section',    'attributes'),
    ('blockquote', 'attributes'),
]

def _apply_nesting(htmlgrammar, max_nest):
    """Injects a recursive <nestedelement> symbol into the grammar.

    Design:
    - <nestedelement> wraps a single <nestedelement> inside a container tag
      (linear depth growth, no exponential blowup).
    - The nonrecursive base case weight is tuned so the expected nesting depth
      equals max_nest: p(stop) = k/(k + k*(max_nest-1)) = 1/max_nest
      where k = len(_NEST_WRAP_TAGS) = 4.
    - recursion_max is raised to max_nest + 10 so the limit is rarely hit.
    - <innerelements> is intentionally NOT modified — adding multi-child
      alternatives causes exponential blowup (width^depth nodes).
    """
    k = len(_NEST_WRAP_TAGS)
    # Weight of base case: w = k / (max_nest - 1), clamped to [0.05, k]
    base_weight = round(max(0.05, k / max(1, max_nest - 1)), 3)
    htmlgrammar._recursion_max = max_nest + 10

    lines = []

    # Base case (nonrecursive): stop recursion, emit a plain element
    lines.append(f'<nestedelement nonrecursive=true p={base_weight}> = <element>')

    # Recursive cases: each wraps a single <nestedelement> (linear, not branching)
    for tag, attrs in _NEST_WRAP_TAGS:
        lines.append(
            f'<nestedelement> = <lt>{tag} <{attrs}> <attributes><gt>'
            f'<newline><nestedelement><newline>'
            f'<lt>/{tag}<gt>'
        )

    # Add <nestedelement> alternatives to <bodyelements> (1 to 4 at body level)
    for count in [1, 2, 3, 4]:
        lines.append(
            '<bodyelements> = '
            + '<newline><nestedelement>' * count
            + '<newline>'
        )

    extra = '\n'.join(lines) + '\n'
    err = htmlgrammar.parse_from_string(extra)
    if err > 0:
        print(f'Warning: {err} error(s) injecting nesting rules')
# [PAI] END


# [PAI] BEGIN — génération standalone depuis une grammaire custom (mxss.txt, etc.)
_STANDALONE_ELEMENTS_PER_FILE = 50

def generate_grammar_samples(grammar_file, outfiles):
    """Génère des fichiers HTML depuis une grammaire standalone (ex: mxss.txt).
    Pas de JS/CSS grammar. Pas d'injection d'IDs HTML. Root symbol uniquement.
    """
    grammar_dir = os.path.join(os.path.dirname(__file__), 'rules')
    grammar = Grammar()
    err = grammar.parse_from_file(os.path.join(grammar_dir, grammar_file))
    if err > 0:
        print(f'There were errors parsing grammar: {grammar_file}')
        return
    for outfile in outfiles:
        try:
            parts = [grammar.generate_root() for _ in range(_STANDALONE_ELEMENTS_PER_FILE)]
            result = f'<!DOCTYPE html>\n<html>\n<body>\n' + '\n'.join(parts) + '\n</body>\n</html>\n'
            print(f'Writing a sample to {outfile}')
            with open(outfile, 'w') as f:
                f.write(result)
        except Exception as e:
            print(f'Error generating {outfile}: {e}')
# [PAI] END


# [PAI] BEGIN — differential comparison mode
def _load_html_grammar(grammar_file='html.txt', max_nest=0):
    """Load htmlgrammar (+ cssgrammar import). Used by diff mode."""
    grammar_dir = os.path.join(os.path.dirname(__file__), 'rules')
    htmlgrammar = Grammar()
    err = htmlgrammar.parse_from_file(os.path.join(grammar_dir, grammar_file))
    if err > 0:
        print(f'There were errors parsing grammar: {grammar_file}')
        return None
    cssgrammar = Grammar()
    cssgrammar.parse_from_file(os.path.join(grammar_dir, 'css.txt'))
    htmlgrammar.add_import('cssgrammar', cssgrammar)
    if max_nest > 0 and 'element' in htmlgrammar._creators:
        _apply_nesting(htmlgrammar, max_nest)
    return htmlgrammar


def _apply_diff_attrs(htmlgrammar):
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


def run_diff_mode(count=500, max_nest=0, grammar_file='html.txt'):
    """Compare DOMParser, PHP DOM, and Lexbor 2.7.0.
    Saves HTML to findings/ only on divergence.
    """
    try:
        from diff_compare import DiffComparator
    except ImportError as e:
        print(f"[ERROR] Could not import diff_compare: {e}")
        print("Make sure you are running with .venv/bin/python")
        return

    htmlgrammar = _load_html_grammar(grammar_file=grammar_file, max_nest=max_nest)
    if htmlgrammar is None:
        return
    _apply_diff_attrs(htmlgrammar)

    findings_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'findings'
    found = 0
    _N_MXSS_ELEMENTS = 20
    has_bodyelements = 'bodyelements' in htmlgrammar._creators

    print(f"[DIFF] Starting differential comparison — {count} samples")
    print(f"[DIFF] Findings will be saved to: {findings_dir}/")
    print()

    with DiffComparator(findings_dir) as cmp:
        for i in range(1, count + 1):
            if has_bodyelements:
                fragment = htmlgrammar.generate_symbol('bodyelements')
            else:
                fragment = '\n'.join(htmlgrammar.generate_root() for _ in range(_N_MXSS_ELEMENTS))
            html = f'<!DOCTYPE html><html><body>{fragment}</body></html>'
            diverged = cmp.compare(html)
            if diverged:
                found += 1
            else:
                print(f"\r[DIFF] {i}/{count} — findings: {found}", end='', flush=True)
            if i % 1000 == 0:
                gc.collect()

    print(f"\n\n[DIFF] Done. {found} divergence(s) found in {count} samples.")
    if found:
        print(f"[DIFF] See: {findings_dir}/")
# [PAI] END


def generate_samples(template, outfiles, max_nest=0):
    """Generates a set of samples and writes them to the output files.
    Args:
      grammar_dir: directory to load grammar files from.
      outfiles: A list of output filenames.
      max_nest: maximum nesting depth (0 = disabled, 1-100 = enabled).
    """

    grammar_dir = os.path.join(os.path.dirname(__file__), 'rules')
    htmlgrammar = Grammar()

    err = htmlgrammar.parse_from_file(os.path.join(grammar_dir, 'html.txt'))
    # CheckGrammar(htmlgrammar)
    if err > 0:
        print('There were errors parsing html grammar')
        return

    cssgrammar = Grammar()
    err = cssgrammar.parse_from_file(os.path.join(grammar_dir ,'css.txt'))
    # CheckGrammar(cssgrammar)
    if err > 0:
        print('There were errors parsing css grammar')
        return

    jsgrammar = Grammar()
    err = jsgrammar.parse_from_file(os.path.join(grammar_dir,'js.txt'))
    # CheckGrammar(jsgrammar)
    if err > 0:
        print('There were errors parsing js grammar')
        return

    # JS and HTML grammar need access to CSS grammar.
    # Add it as import
    htmlgrammar.add_import('cssgrammar', cssgrammar)
    jsgrammar.add_import('cssgrammar', cssgrammar)

    # [PAI] apply nesting rules if requested
    if max_nest > 0:
        _apply_nesting(htmlgrammar, max_nest)

    for outfile in outfiles:
        result = generate_new_sample(template, htmlgrammar, cssgrammar, jsgrammar)
        if result is not None:
            print('Writing a sample to ' + outfile)
            try:
                with open(outfile, 'w') as f:
                    f.write(result)
            except IOError:
                print('Error writing to output')

def get_argument_parser():
    
    parser = argparse.ArgumentParser(description="DOMATO (A DOM FUZZER)")
    
    parser.add_argument("-f", "--file", 
    help="File name which is to be generated in the same directory")

    parser.add_argument('-o', '--output_dir', type=str,
                    help='The output directory to put the generated files in')

    parser.add_argument('-n', '--no_of_files', type=int,
                    help='number of files to be generated')

    parser.add_argument('-t', '--template', type=Path, default=(Path(__file__).parent).joinpath('template.html'),
                    help='template file you want to use')
    # [PAI] --max-nest option
    parser.add_argument('--max-nest', type=int, default=0, metavar='N',
                    help='Enable random tag nesting up to depth N (0=disabled, 1-100)')
    # [PAI] BEGIN — --grammar option
    parser.add_argument('--grammar', type=str, default=None, metavar='FILE',
                    help='Grammar file for standalone generation (relative to rules/), skips JS/CSS/HTML-ID injection')
    # [PAI] END
    # [PAI] BEGIN — --diff mode options
    parser.add_argument('--diff', action='store_true',
                    help='Differential parser comparison mode (requires .venv with playwright and requests)')
    parser.add_argument('--diff-count', type=int, default=500, metavar='N',
                    help='Number of samples in --diff mode (default: 500)')
    parser.add_argument('--diff-grammar', type=str, default='html.txt', metavar='FILE',
                    help='Grammar file for --diff mode, relative to rules/ (default: html.txt)')
    # [PAI] END
    return parser

def main():

    parser = get_argument_parser()

    args = parser.parse_args()

    # [PAI] validate --max-nest range
    max_nest = max(0, min(100, args.max_nest))

    # [PAI] BEGIN — --diff mode
    if args.diff:
        run_diff_mode(count=args.diff_count, max_nest=max_nest, grammar_file=args.diff_grammar)
        return
    # [PAI] END

    # [PAI] BEGIN — --grammar mode
    if args.grammar:
        if args.file:
            generate_grammar_samples(args.grammar, [args.file])
        elif args.output_dir:
            if not args.no_of_files:
                print("Please use switch -n to specify the number of files")
            else:
                out_dir = args.output_dir
                if not os.path.exists(out_dir):
                    os.mkdir(out_dir)
                outfiles = [os.path.join(out_dir, f'fuzz-{str(i).zfill(5)}.html') for i in range(args.no_of_files)]
                generate_grammar_samples(args.grammar, outfiles)
        else:
            parser.print_help()
        return
    # [PAI] END

    with args.template.open("r") as f:
        template = f.read()

    if args.file:
        generate_samples(template, [args.file], max_nest=max_nest)

    elif args.output_dir:
        if not args.no_of_files:
            print("Please use switch -n to specify the number of files")
        else:
            print('Running on ClusterFuzz')
            out_dir = args.output_dir
            nsamples = args.no_of_files
            print('Output directory: ' + out_dir)
            print('Number of samples: ' + str(nsamples))
            if max_nest > 0:
                print(f'Nesting mode: max-nest={max_nest}, recursion_max={min(50 + max_nest, 80)}')

            if not os.path.exists(out_dir):
                os.mkdir(out_dir)

            outfiles = []
            for i in range(nsamples):
                outfiles.append(os.path.join(out_dir, 'fuzz-' + str(i).zfill(5) + '.html'))

            generate_samples(template, outfiles, max_nest=max_nest)
                

    else:
        parser.print_help()


if __name__ == '__main__':
    
    main()
