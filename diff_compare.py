# diff_compare.py — Differential parser comparator
# Compare DOM trees from DOMParser (browser), PHP DOM, and Lexbor 2.7.0.
# Comparison: element name + namespaceURI only, DFS from <body>, <template> skipped.

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ERROR] 'requests' not installed. Run: .venv/bin/pip install -r requirements.txt")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[ERROR] 'playwright' not installed. Run: .venv/bin/pip install playwright && .venv/bin/playwright install firefox")
    sys.exit(1)

_PHP_SERVER = "http://127.0.0.1:5000/lexborParser.php"
_ELEM_NODE  = 1  # DOM nodeType for Element

_PAGE_RESTART_EVERY = 500  # recyclage de la page pour libérer la mémoire du moteur JS

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
        const attrs = Array.from(node.attributes).map(a => a.name + '="' + a.value + '"').join(' '); // canary: include attrs for divergence display
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
    local = local.lower()  # normalize: Lexbor 2.7.0 lowercases SVG names (e.g. foreignobject vs foreignObject)
    if node.get("isTemplate") or (local == "template" and ns == "http://www.w3.org/1999/xhtml"):
        return []
    # include attrs string as canary (3rd element, not used in comparison)
    attrs_list = node.get("attributes") or []
    attrs_str  = " ".join(f'{a["name"]}="{a.get("value", "")}"' for a in attrs_list if isinstance(a, dict))  # .get(): boolean attrs have no "value" key in Lexbor JSON
    result = [(local, ns, attrs_str)]
    for child in node.get("childNodes", []):
        result.extend(_flatten(child))
    return result


def _first_diff(list_a: list, list_b: list):
    """Return (index, elem_a, elem_b) for the first differing element, or None if same prefix."""
    for i, (a, b) in enumerate(zip(list_a, list_b)):
        if a[:2] != b[:2]:  # compare only (localName, namespaceURI), ignore attrs canary
            return (i, a, b)
    return None

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
        self._counter   = 0
        self._page_uses = 0  # tracks evaluate() calls; page is recycled every _PAGE_RESTART_EVERY
        self._session   = None  # persistent HTTP session — reuses TCP connections to PHP server

    def __enter__(self):
        self._pw      = sync_playwright().start()
        self._browser = self._pw.firefox.launch()  # Firefox est le DOMParser de référence de la comparaison
        self._page    = self._browser.new_page()
        self._session = requests.Session()  # open once, reuse for all HTTP calls
        return self

    def __exit__(self, *_):
        if self._session:
            self._session.close()  # release HTTP connections
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # Méthode plutôt que fonction libre : la session HTTP est réutilisée d'un appel à l'autre
    def _fetch_tree(self, html: str, version: str) -> dict:
        """POST html to the PHP server, return parsed JSON tree."""
        resp = self._session.post(
            _PHP_SERVER,
            json={"html": html, "lexborVersion": version},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def _browser_elements(self, html: str) -> list:
        raw = self._page.evaluate(_DOM_SERIALIZE_JS, html)
        return [tuple(x) for x in json.loads(raw)]

    def _maybe_restart_page(self):
        if self._page_uses >= _PAGE_RESTART_EVERY:
            self._page.close()
            self._page = self._browser.new_page()
            self._page_uses = 0

    def compare(self, html: str) -> bool:
        """
        Compare DOMParser, PHP DOM, and Lexbor 2.7.0.
        Returns True only when at least one divergence is found.
        Returns False when all parsers agree.
        """
        # print("HTML : " + html)
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

        self._maybe_restart_page()
        elems_browser = self._browser_elements(html)
        self._page_uses += 1

        # Comparaisons utiles : DOMParser vs chacun des deux Lexbor.
        # PHP DOM vs Lexbor 2.7.0 seul n'est pas pertinent (différences de version, pas mXSS).
        divergences = []
        if [e[:2] for e in elems_browser] != [e[:2] for e in elems_lexbor]:  # compare without attrs
            divergences.append(("DOMParser", "Lexbor 2.7.0", elems_browser, elems_lexbor))
        if [e[:2] for e in elems_browser] != [e[:2] for e in elems_php]:  # compare without attrs
            divergences.append(("DOMParser", "PHP DOM", elems_browser, elems_php))

        if not divergences:
            return False

        self._counter += 1
        fname = self.findings_dir / f"finding-{self._counter:05d}.html"
        fname.write_text(html, encoding="utf-8")
        for a, b, list_a, list_b in divergences:
            first = _first_diff(list_a, list_b)
            # show class label in output
            print(f"\n[DIVERGENCE #{self._counter}] {a} ≠ {b}  →  {fname.name}")
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
