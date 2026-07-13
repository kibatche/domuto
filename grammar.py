#   Domuto - grammar parser and generator
#   --------------------------------------
#   Fork of Domato (Ivan Fratric, Google)
#   Stripped to HTML/mXSS grammar mode only.
#   Removed: JS code generation, variable tracking, exec() functions, binary packing.

from __future__ import print_function

import bisect
try:
    from html import escape as _escape
except ImportError:
    from cgi import escape as _escape
import os
import random
import re

_INT_RANGES = {
    'int':    [-2147483648, 2147483647],
    'int32':  [-2147483648, 2147483647],
    'uint32': [0, 4294967295],
    'int8':   [-128, 127],
    'uint8':  [0, 255],
    'int16':  [-32768, 32767],
    'uint16': [0, 65536],
    'int64':  [-9223372036854775808, 9223372036854775807],
    'uint64': [0, 18446744073709551615],
}


class Error(Exception):
    pass


class GrammarError(Error):
    pass


class RecursionError(Error):
    pass


class Grammar(object):
    """Parses grammar and generates corresponding languages.

    Usage:
    >>> grammar = Grammar()
    >>> grammar.parse_from_file('rules/html.txt')
    >>> html = grammar.generate_root()
    """

    def __init__(self):
        self._root = ''
        self._creators = {}
        self._nonrecursive_creators = {}
        self._all_rules = []
        self._creator_cdfs = {}
        self._nonrecursivecreator_cdfs = {}
        self._definitions_dir = '.'
        self._imports = {}
        self._recursion_max = 50

        self._constant_types = {
            'lt':    '<',
            'gt':    '>',
            'hash':  '#',
            'cr':    chr(13),
            'lf':    chr(10),
            'space': ' ',
            'tab':   chr(9),
            'ex':    '!',
        }

        self._built_in_types = {
            'int':            self._generate_int,
            'int32':          self._generate_int,
            'uint32':         self._generate_int,
            'int8':           self._generate_int,
            'uint8':          self._generate_int,
            'int16':          self._generate_int,
            'uint16':         self._generate_int,
            'int64':          self._generate_int,
            'uint64':         self._generate_int,
            'float':          self._generate_float,
            'double':         self._generate_float,
            'char':           self._generate_char,
            'string':         self._generate_string,
            'htmlsafestring': self._generate_html_string,
            'hex':            self._generate_hex,
            'import':         self._generate_import,
        }

        self._command_handlers = {
            'include':       self._include_from_file,
            'import':        self._import_grammar,
            'max_recursion': self._set_recursion_depth,
        }

    # -------------------------------------------------------------------------
    # Built-in type generators
    # -------------------------------------------------------------------------

    def _string_to_int(self, s):
        return int(s, 0)

    def _generate_int(self, tag):
        r = _INT_RANGES[tag['tagname']]
        min_val = self._string_to_int(tag['min']) if 'min' in tag else r[0]
        max_val = self._string_to_int(tag['max']) if 'max' in tag else r[1]
        if min_val > max_val:
            raise GrammarError('Range error in integer tag')
        return str(random.randint(min_val, max_val))

    def _generate_float(self, tag):
        min_val = float(tag.get('min', '0'))
        max_val = float(tag.get('max', '1'))
        if min_val > max_val:
            raise GrammarError('Range error in float tag')
        return str(min_val + random.random() * (max_val - min_val))

    def _generate_char(self, tag):
        if 'code' in tag:
            return chr(self._string_to_int(tag['code']))
        min_val = self._string_to_int(tag.get('min', '0'))
        max_val = self._string_to_int(tag.get('max', '255'))
        if min_val > max_val:
            raise GrammarError('Range error in char tag')
        return chr(random.randint(min_val, max_val))

    def _generate_string(self, tag):
        min_val = self._string_to_int(tag.get('min', '0'))
        max_val = self._string_to_int(tag.get('max', '255'))
        if min_val > max_val:
            raise GrammarError('Range error in string tag')
        minlen = self._string_to_int(tag.get('minlength', '0'))
        maxlen = self._string_to_int(tag.get('maxlength', '20'))
        length = random.randint(minlen, maxlen)
        charset = range(min_val, max_val + 1)
        return ''.join(chr(charset[int(random.random() * len(charset))]) for _ in range(length))

    def _generate_html_string(self, tag):
        return _escape(self._generate_string(tag), quote=True)

    def _generate_hex(self, tag):
        return ('%X' if 'up' in tag else '%x') % random.randint(0, 15)

    def _generate_import(self, tag):
        if 'from' not in tag:
            raise GrammarError('import tag without from attribute')
        grammarname = tag['from']
        if grammarname not in self._imports:
            raise GrammarError('unknown import ' + grammarname)
        grammar = self._imports[grammarname]
        if 'symbol' in tag:
            return grammar.generate_symbol(tag['symbol'])
        return grammar.generate_root()

    # -------------------------------------------------------------------------
    # Symbol expansion
    # -------------------------------------------------------------------------

    def _select_creator(self, symbol, recursion_depth, force_nonrecursive):
        if symbol not in self._creators:
            raise GrammarError('No creators for type ' + symbol)
        if recursion_depth >= self._recursion_max:
            raise RecursionError('Maximum recursion level reached for type ' + symbol)
        if force_nonrecursive and symbol in self._nonrecursive_creators:
            creators = self._nonrecursive_creators[symbol]
            cdf = self._nonrecursivecreator_cdfs[symbol]
        else:
            creators = self._creators[symbol]
            cdf = self._creator_cdfs[symbol]
        if not cdf:
            return creators[random.randint(0, len(creators) - 1)]
        return creators[bisect.bisect_left(cdf, random.random(), 0, len(cdf))]

    def _generate(self, symbol, recursion_depth=0, force_nonrecursive=False):
        creator = self._select_creator(symbol, recursion_depth, force_nonrecursive)
        return self._expand_rule(creator, recursion_depth, force_nonrecursive)

    def _expand_rule(self, rule, recursion_depth, force_nonrecursive):
        variable_ids = {}
        ret_parts = []
        for part in rule['parts']:
            if 'id' in part and part['id'] in variable_ids:
                ret_parts.append(variable_ids[part['id']])
                continue

            if part['type'] == 'text':
                expanded = part['text']
            elif part['tagname'] in self._constant_types:
                expanded = self._constant_types[part['tagname']]
            elif part['tagname'] in self._built_in_types:
                expanded = self._built_in_types[part['tagname']](part)
            else:
                try:
                    expanded = self._generate(part['tagname'], recursion_depth + 1, force_nonrecursive)
                except RecursionError:
                    if not force_nonrecursive:
                        expanded = self._generate(part['tagname'], recursion_depth + 1, True)
                    else:
                        raise

            if 'id' in part:
                variable_ids[part['id']] = expanded
            ret_parts.append(expanded)

        return ''.join(ret_parts)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate_root(self):
        if not self._root:
            print('Error: No root element defined.')
            return ''
        return self._generate(self._root)

    def generate_symbol(self, name):
        return self._generate(name)

    def add_import(self, name, grammar):
        self._imports[name] = grammar

    # -------------------------------------------------------------------------
    # Grammar parsing
    # -------------------------------------------------------------------------

    def _parse_tag_and_attributes(self, string):
        parts = string.split()
        if not parts:
            raise GrammarError('Empty tag encountered')
        ret = {'type': 'tag', 'tagname': parts[0]}
        for attr in parts[1:]:
            attrparts = attr.split('=')
            if len(attrparts) == 2:
                ret[attrparts[0]] = attrparts[1]
            elif len(attrparts) == 1:
                ret[attrparts[0]] = True
            else:
                raise GrammarError('Error parsing tag ' + string)
        return ret

    def _parse_grammar_line(self, line):
        match = re.match(r'^<([^>]*)>\s*=\s*(.*)$', line)
        if not match:
            raise GrammarError('Error parsing rule ' + line)

        rule = {
            'type': 'grammar',
            'creates': self._parse_tag_and_attributes(match.group(1)),
            'parts': [],
            'recursive': False,
        }

        rule_parts = re.split(r'<([^>)]*)>', match.group(2))
        for i, rp in enumerate(rule_parts):
            if i % 2 == 0:
                if rp:
                    rule['parts'].append({'type': 'text', 'text': rp})
            else:
                parsedtag = self._parse_tag_and_attributes(rp)
                rule['parts'].append(parsedtag)
                if parsedtag['tagname'] == rule['creates']['tagname']:
                    rule['recursive'] = True

        create_tag_name = rule['creates']['tagname']
        if create_tag_name in self._creators:
            self._creators[create_tag_name].append(rule)
        else:
            self._creators[create_tag_name] = [rule]
        if 'nonrecursive' in rule['creates']:
            if create_tag_name in self._nonrecursive_creators:
                self._nonrecursive_creators[create_tag_name].append(rule)
            else:
                self._nonrecursive_creators[create_tag_name] = [rule]
        self._all_rules.append(rule)
        if 'root' in rule['creates']:
            self._root = create_tag_name

    def _remove_comments(self, line):
        if '#' in line:
            return line[:line.index('#')].strip()
        return line.strip()

    def _include_from_string(self, grammar_str):
        num_errors = 0
        for line in grammar_str.split('\n'):
            cleanline = self._remove_comments(line)
            if not cleanline:
                continue
            match = re.match(r'^!([a-z_]+)\s*(.*)$', cleanline)
            if match:
                command = match.group(1)
                params = match.group(2)
                if command in self._command_handlers:
                    self._command_handlers[command](params)
                # unknown commands (!extends, !lineguard, !varformat, etc.) are silently skipped
                continue
            try:
                self._parse_grammar_line(cleanline)
            except GrammarError:
                print('Error parsing line ' + line)
                num_errors += 1
        return num_errors

    def _include_from_file(self, filename):
        filepath = os.path.join(self._definitions_dir, filename)
        try:
            with open(filepath) as f:
                content = f.read()
        except IOError:
            print('Error reading ' + filename)
            return 1
        saved_dir = self._definitions_dir
        self._definitions_dir = os.path.dirname(filepath)
        errors = self.parse_from_string(content)
        self._definitions_dir = saved_dir
        return errors

    def _import_grammar(self, filename):
        basename = os.path.basename(filename)
        path = os.path.join(self._definitions_dir, filename)
        subgrammar = Grammar()
        num_errors = subgrammar.parse_from_file(path)
        if num_errors:
            raise GrammarError('There were errors when parsing ' + filename)
        self._imports[basename] = subgrammar

    def parse_from_string(self, grammar_str):
        errors = self._include_from_string(grammar_str)
        if errors:
            return errors
        self._normalize_probabilities()
        return 0

    def parse_from_file(self, filename, extra=None):
        try:
            with open(filename) as f:
                content = f.read()
        except IOError:
            print('Error reading ' + filename)
            return 1
        self._definitions_dir = os.path.dirname(filename)
        if extra:
            content = extra + content
        return self.parse_from_string(content)

    # -------------------------------------------------------------------------
    # Probability computation
    # -------------------------------------------------------------------------

    def _get_cdf(self, creators):
        probabilities = []
        defined = []

        for creator in creators:
            create_tag = creator['creates']
            if 'p' in create_tag:
                probabilities.append(float(create_tag['p']))
                defined.append(True)
            else:
                probabilities.append(0.0)
                defined.append(False)

        if not any(defined):
            return []  # uniform — faster path in _select_creator

        p_sum = sum(probabilities)
        nondef_count = defined.count(False)
        if p_sum > 1 or nondef_count == 0:
            norm_factor = 1.0 / p_sum
            nondef_value = 0.0
        else:
            norm_factor = 1.0
            nondef_value = (1.0 - p_sum) / nondef_count

        cdf = []
        cumulative = 0.0
        for i, p in enumerate(probabilities):
            cumulative += p * norm_factor if defined[i] else nondef_value
            cdf.append(cumulative)
        return cdf

    def _normalize_probabilities(self):
        for symbol, creators in self._creators.items():
            self._creator_cdfs[symbol] = self._get_cdf(creators)
        for symbol, creators in self._nonrecursive_creators.items():
            self._nonrecursivecreator_cdfs[symbol] = self._get_cdf(creators)

    def _set_recursion_depth(self, depth_str):
        depth_str = depth_str.strip()
        if depth_str.isdigit():
            self._recursion_max = int(depth_str)
        else:
            raise GrammarError('Argument to max_recursion is not an integer')
