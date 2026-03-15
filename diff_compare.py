# [PAI] BEGIN — diff_compare.py — Differential parser comparator
# Compare DOM trees from DOMParser (browser), PHP DOM, and Lexbor 2.7.0.
# Comparison: element name + namespaceURI only, DFS from <body>, <template> skipped.

import ctypes
import gc
import json
import sys
from pathlib import Path

# [PAI] BEGIN — malloc_trim shim: forces libc to return freed pages to OS
# pymalloc doesn't do this; without it, RSS grows without bound over 100k iterations.
try:
    _libc = ctypes.CDLL("libc.so.6", use_errno=True)
    def _malloc_trim():
        _libc.malloc_trim(0)
except OSError:
    def _malloc_trim():  # no-op on non-glibc platforms
        pass
# [PAI] END

try:
    import requests
except ImportError:
    print("[ERROR] 'requests' not installed. Run: .venv/bin/pip install requests playwright")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[ERROR] 'playwright' not installed. Run: .venv/bin/pip install playwright && .venv/bin/playwright install chromium")
    sys.exit(1)

_PHP_SERVER = "http://127.0.0.1:5000/lexborParser.php"
_ELEM_NODE  = 1  # DOM nodeType for Element

# [PAI] BEGIN — AFE elements per HTML5 spec §13.2.3.3
_AFE_ELEMENTS = frozenset({
    'a', 'b', 'big', 'code', 'em', 'font', 'i',
    'nobr', 's', 'small', 'strike', 'strong', 'tt', 'u',
})
# [PAI] END

# [PAI] BEGIN — tuning constants
_PAGE_RESTART_EVERY  = 500   # close+reopen Playwright page to flush V8 heap
_MALLOC_TRIM_EVERY   = 2000  # force libc to return freed pages to OS
# [PAI] END

# JS function evaluated in the browser via Playwright.
# Walks doc.body recursively, collects [localName, namespaceURI] for element nodes.
# Skips <template> elements and their entire subtree.
_DOM_SERIALIZE_JS = """(html) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const result = [];
    function walk(node) {
        if (node.nodeType !== 1) return;
        if (node.localName === 'template' && node.namespaceURI === 'http://www.w3.org/1999/xhtml') return;
        const attrs = Array.from(node.attributes).map(a => a.name + '="' + a.value + '"').join(' '); // [PAI] canary: include attrs for divergence display
        result.push([node.localName.toLowerCase(), node.namespaceURI, attrs]);
        for (const child of node.childNodes) {
            walk(child);
        }
    }
    walk(doc.body);
    return JSON.stringify(result);
}"""


def _find_body(tree: dict) -> dict | None:
    """Navigate LexborHtmlDocument JSON: document -> html -> body."""
    for child in tree.get("childNodes", []):
        if child.get("nodeType") == _ELEM_NODE and child.get("localName", "").lower() == "html":
            for html_child in child.get("childNodes", []):
                if html_child.get("nodeType") == _ELEM_NODE and html_child.get("localName", "").lower() == "body":
                    return html_child
    return None


def _flatten(node: dict) -> list:
    """
    DFS over element nodes only, starting from the given node (included).
    Returns list of (localName, namespaceURI) tuples.
    Skips <template> nodes and their subtrees entirely.
    """
    if node.get("nodeType") != _ELEM_NODE:
        return []
    ns    = node.get("namespaceURI") or ""
    local = node.get("localName") or ""
    # Skip template: isTemplate flag covers both PHP and Lexbor binary
    local = local.lower()  # [PAI] normalize: Lexbor 2.7.0 lowercases SVG names (e.g. foreignobject vs foreignObject)
    if node.get("isTemplate") or (local == "template" and ns == "http://www.w3.org/1999/xhtml"):
        return []
    # [PAI] BEGIN — include attrs string as canary (3rd element, not used in comparison)
    attrs_list = node.get("attributes") or []
    attrs_str  = " ".join(f'{a["name"]}="{a.get("value", "")}"' for a in attrs_list if isinstance(a, dict))  # [PAI] .get(): boolean attrs have no "value" key in Lexbor JSON
    result = [(local, ns, attrs_str)]
    # [PAI] END
    for child in node.get("childNodes", []):
        result.extend(_flatten(child))
    return result


def _first_diff(list_a: list, list_b: list):
    """Return (index, elem_a, elem_b) for the first differing element, or None if same prefix."""
    for i, (a, b) in enumerate(zip(list_a, list_b)):
        if a[:2] != b[:2]:  # [PAI] compare only (localName, namespaceURI), ignore attrs canary
            return (i, a, b)
    return None


# [PAI] BEGIN — known divergence classifier
def _classify_divergence(html: str, list_a: list, list_b: list, first) -> str | None:
    """
    Classify a divergence against known classes.
    Returns the class name if known, None if the divergence is unrecognised.

    Rules (ordered from most specific to least):
      0. DIALOG_DETAILS  — html contains <dialog or <details (source-level filter).
         Both elements cause systematic table foster-parenting divergences in Firefox vs Lexbor.
         Applied first, before element-level checks.
      1. NAMESPACE_STRIP — same localName, different namespace.
      2. SERIALIZATION_IMG — <img> at divergence + SVG context in html source.
      3. SERIALIZATION_AFE — AFE element at divergence + <table> in html source.
         Also catches TABLE_AFE_RAWTEXT_CAPTURE (same structural signature).

    Anything not matching a rule returns None → saved as finding.
    """
    # Rule 0 — source-level filter: dialog/details cause known systematic divergences
    if '<dialog' in html or '<details' in html:  # [PAI] covers both opening tags and attributes
        return 'DIALOG_DETAILS'

    if first:
        _, ea, eb = first
        name_a, ns_a = ea[0], ea[1]
        name_b, ns_b = eb[0], eb[1]

        # Rule 1 — pure namespace divergence (always NAMESPACE_STRIP)
        if name_a == name_b and ns_a != ns_b:
            return 'NAMESPACE_STRIP'

        # Rule 2 — img foreign content breakout
        if (name_a == 'img' or name_b == 'img') and ('<svg' in html or '<foreignObject' in html):
            return 'SERIALIZATION_IMG'

        # Rule 3 — AFE element at divergence point + table context
        if (name_a in _AFE_ELEMENTS or name_b in _AFE_ELEMENTS) and '<table' in html:
            return 'SERIALIZATION_AFE'

    else:
        # Length-only divergence: check the extra element
        extra = (list_a if len(list_a) > len(list_b) else list_b)[min(len(list_a), len(list_b))]
        if extra[0] in _AFE_ELEMENTS and '<table' in html:
            return 'SERIALIZATION_AFE'

    return None  # unknown — caller should save as finding
# [PAI] END


class DiffComparator:
    """
    Context manager that holds a single persistent Playwright browser instance.
    Call compare(html) for each generated document.
    """

    def __init__(self, findings_dir: Path):
        self.findings_dir = findings_dir
        self.findings_dir.mkdir(exist_ok=True)
        self._pw         = None
        self._browser    = None
        self._page       = None
        self._counter       = 0
        self._page_uses     = 0  # [PAI] tracks evaluate() calls; page is recycled every _PAGE_RESTART_EVERY
        self._compare_calls = 0  # [PAI] total compare() calls; drives malloc_trim cadence
        self._session       = None  # [PAI] persistent HTTP session — reuses TCP connections to PHP server

    def __enter__(self):
        self._pw      = sync_playwright().start()
        self._browser = self._pw.firefox.launch()  # [PAI] changed from chromium — user reference is Firefox DOMParser
        self._page    = self._browser.new_page()
        self._session = requests.Session()  # [PAI] open once, reuse for all HTTP calls
        return self

    def __exit__(self, *_):
        if self._session:
            self._session.close()  # [PAI] release HTTP connections
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # [PAI] BEGIN — _fetch_tree moved to method to use self._session
    def _fetch_tree(self, html: str, version: str) -> dict:
        """POST html to the PHP server, return parsed JSON tree."""
        resp = self._session.post(
            _PHP_SERVER,
            json={"html": html, "lexborVersion": version},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    # [PAI] END

    def _browser_elements(self, html: str) -> list:
        raw = self._page.evaluate(_DOM_SERIALIZE_JS, html)
        return [tuple(x) for x in json.loads(raw)]

    # [PAI] BEGIN — page recycling + periodic malloc_trim
    def _maybe_restart_page(self):
        if self._page_uses >= _PAGE_RESTART_EVERY:
            self._page.close()
            self._page = self._browser.new_page()
            self._page_uses = 0
            gc.collect(2)  # full collection including oldest generation
        if self._compare_calls % _MALLOC_TRIM_EVERY == 0 and self._compare_calls > 0:
            _malloc_trim()
    # [PAI] END

    def compare(self, html: str) -> bool:
        """
        Compare DOMParser, PHP DOM, and Lexbor 2.7.0.
        Divergences matching known classes (NAMESPACE_STRIP, SERIALIZATION_AFE,
        SERIALIZATION_IMG) are silently skipped.
        Returns True only when at least one divergence is unclassified (new finding saved).
        Returns False when all parsers agree or all divergences are known.
        """
        # [PAI] BEGIN — increment global counter; drives malloc_trim and page restart
        self._compare_calls += 1
        # [PAI] END

        try:
            tree_php    = self._fetch_tree(html, "php-8.4.18-dom")
            tree_lexbor = self._fetch_tree(html, "2.7.0")
        except Exception as e:
            print(f"\n[ERROR] PHP server unreachable: {e}")
            return False

        body_php    = _find_body(tree_php)
        body_lexbor = _find_body(tree_lexbor)

        if body_php is None or body_lexbor is None:
            print("\n[WARN] Could not locate <body> in PHP/Lexbor response — skipping")
            return False

        elems_php    = _flatten(body_php)
        elems_lexbor = _flatten(body_lexbor)
        # [PAI] BEGIN — explicit del: release large JSON dicts immediately after flattening
        del body_php, body_lexbor, tree_php, tree_lexbor
        # [PAI] END

        # [PAI] BEGIN — page recycling + malloc_trim before evaluate() call
        self._maybe_restart_page()
        elems_browser = self._browser_elements(html)
        self._page_uses += 1
        # [PAI] END

        # Comparaisons utiles : DOMParser vs chacun des deux Lexbor.
        # PHP DOM vs Lexbor 2.7.0 seul n'est pas pertinent (différences de version, pas mXSS).
        divergences = []
        if [e[:2] for e in elems_browser] != [e[:2] for e in elems_lexbor]:  # [PAI] compare without attrs
            divergences.append(("DOMParser", "Lexbor 2.7.0", elems_browser, elems_lexbor))
        if [e[:2] for e in elems_browser] != [e[:2] for e in elems_php]:  # [PAI] compare without attrs
            divergences.append(("DOMParser", "PHP DOM", elems_browser, elems_php))

        if not divergences:
            return False

        # [PAI] BEGIN — classify divergences; skip finding if all are known classes
        classified = []
        for a, b, list_a, list_b in divergences:
            first = _first_diff(list_a, list_b)
            cls   = _classify_divergence(html, list_a, list_b, first)
            classified.append((a, b, list_a, list_b, first, cls))

        # All divergences are known → skip silently
        if all(cls is not None for *_, cls in classified):
            return False
        # [PAI] END

        self._counter += 1
        fname = self.findings_dir / f"finding-{self._counter:05d}.html"
        fname.write_text(html, encoding="utf-8")
        for a, b, list_a, list_b, first, cls in classified:
            # [PAI] BEGIN — show class label in output
            cls_label = f"  [known: {cls}]" if cls else "  [NEW]"
            print(f"\n[DIVERGENCE #{self._counter}] {a} ≠ {b}  →  {fname.name}{cls_label}")
            # [PAI] END
            if first:
                idx, ea, eb = first
                attrs_a = f"  [{ea[2]}]" if len(ea) > 2 and ea[2] else ""
                attrs_b = f"  [{eb[2]}]" if len(eb) > 2 and eb[2] else ""
                print(f"  élément [{idx}]  {a}: <{ea[0]}> ns={ea[1]}{attrs_a}")
                print(f"  élément [{idx}]  {b}: <{eb[0]}> ns={eb[1]}{attrs_b}")
            else:
                print(f"  longueurs : {a}={len(list_a)}  {b}={len(list_b)}")
                if len(list_a) > len(list_b):
                    ex = list_a[len(list_b)]
                    attrs_ex = f"  [{ex[2]}]" if len(ex) > 2 and ex[2] else ""
                    print(f"  élément supplémentaire dans {a}: <{ex[0]}> ns={ex[1]}{attrs_ex}")
                else:
                    ex = list_b[len(list_a)]
                    attrs_ex = f"  [{ex[2]}]" if len(ex) > 2 and ex[2] else ""
                    print(f"  élément supplémentaire dans {b}: <{ex[0]}> ns={ex[1]}{attrs_ex}")
        return True
# [PAI] END
