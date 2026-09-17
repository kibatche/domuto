#!/usr/bin/env python3
"""
analyze_findings.py — Rejoue les findings enregistrés dans findings/.
Compare DOMParser (Playwright/Firefox) vs Lexbor PHP vs Lexbor 2.7.0 standalone.
Output : pour chaque finding, divergences détaillées avec contexte DOM.
"""

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("[ERROR] requests manquant — .venv/bin/pip install requests")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("[ERROR] playwright manquant — .venv/bin/pip install playwright")

_PHP_SERVER = "http://127.0.0.1:5000/lexborParser.php"
_ELEM_NODE  = 1

# Même JS que diff_compare.py — sérialise body en (localName, namespaceURI, attrs)
_DOM_SERIALIZE_JS = """(html) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const result = [];
    function walk(node) {
        if (node.nodeType !== 1) return;
        if (node.localName === 'template' && node.namespaceURI === 'http://www.w3.org/1999/xhtml') return;
        const attrs = Array.from(node.attributes).map(a => a.name + '="' + a.value + '"').join(' ');
        result.push([node.localName.toLowerCase(), node.namespaceURI, attrs]);
        for (const child of node.childNodes) walk(child);
    }
    walk(doc.body);
    return JSON.stringify(result);
}"""


def fetch_tree(html: str, version: str) -> dict:
    resp = requests.post(_PHP_SERVER, json={"html": html, "lexborVersion": version}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def find_body(tree: dict) -> dict | None:
    for child in tree.get("childNodes", []):
        if child.get("nodeType") == _ELEM_NODE and child.get("localName", "").lower() == "html":
            for c in child.get("childNodes", []):
                if c.get("nodeType") == _ELEM_NODE and c.get("localName", "").lower() == "body":
                    return c
    return None


def flatten(node: dict) -> list:
    if node.get("nodeType") != _ELEM_NODE:
        return []
    ns    = node.get("namespaceURI") or ""
    local = (node.get("localName") or "").lower()
    if node.get("isTemplate") or (local == "template" and ns == "http://www.w3.org/1999/xhtml"):
        return []
    attrs_list = node.get("attributes") or []
    attrs_str  = " ".join(f'{a["name"]}="{a.get("value","")}"' for a in attrs_list if isinstance(a, dict))
    result = [(local, ns, attrs_str)]
    for child in node.get("childNodes", []):
        result.extend(flatten(child))
    return result


def first_diff(a: list, b: list):
    for i, (x, y) in enumerate(zip(a, b)):
        if x[:2] != y[:2]:
            return (i, x, y)
    return None


def ns_short(ns: str) -> str:
    return {
        "http://www.w3.org/1999/xhtml": "xhtml",
        "http://www.w3.org/2000/svg":   "svg",
        "http://www.w3.org/1998/Math/MathML": "mathml",
    }.get(ns, ns or "?")


def elem_str(e: tuple) -> str:
    name, ns, attrs = e
    s = f"<{name}> {ns_short(ns)}"
    if attrs:
        s += f"  [{attrs}]"
    return s


def analyze(findings_dir: Path):
    files = sorted(findings_dir.glob("finding-*.html"))
    print(f"[INFO] {len(files)} findings à analyser\n")

    with sync_playwright() as pw:
        browser = pw.firefox.launch()  # Firefox est le DOMParser de référence de la comparaison
        page    = browser.new_page()

        for fpath in files:
            html = fpath.read_text(encoding="utf-8")
            fname = fpath.name

            # DOMParser via Playwright
            raw_browser = page.evaluate(_DOM_SERIALIZE_JS, html)
            elems_browser = [tuple(x) for x in json.loads(raw_browser)]

            # Lexbor PHP
            tree_php  = fetch_tree(html, "php-8.4.18-dom")
            body_php  = find_body(tree_php)
            elems_php = flatten(body_php) if body_php else []

            # Lexbor 2.7.0 standalone
            tree_lx  = fetch_tree(html, "2.7.0")
            body_lx  = find_body(tree_lx)
            elems_lx = flatten(body_lx) if body_lx else []

            print(f"{'='*70}")
            print(f"  {fname}")
            print(f"{'='*70}")

            pairs = [
                ("DOMParser", "Lexbor-PHP",        elems_browser, elems_php),
                ("DOMParser", "Lexbor-2.7.0",      elems_browser, elems_lx),
                ("Lexbor-PHP", "Lexbor-2.7.0",     elems_php,     elems_lx),
            ]

            any_div = False
            for label_a, label_b, la, lb in pairs:
                if [e[:2] for e in la] == [e[:2] for e in lb]:
                    continue
                any_div = True
                diff = first_diff(la, lb)
                if diff:
                    idx, ea, eb = diff
                    print(f"  DIVERGENCE {label_a} ≠ {label_b}")
                    print(f"    [{idx}] {label_a}: {elem_str(ea)}")
                    print(f"    [{idx}] {label_b}: {elem_str(eb)}")

                    # Contexte : 3 éléments avant et après le point de divergence
                    ctx_start = max(0, idx - 3)
                    ctx_end   = min(idx + 4, min(len(la), len(lb)))
                    print(f"  Contexte [{ctx_start}..{ctx_end-1}]:")
                    for i in range(ctx_start, ctx_end):
                        ea_c = la[i] if i < len(la) else None
                        eb_c = lb[i] if i < len(lb) else None
                        marker = ">>>" if i == idx else "   "
                        print(f"    {marker} [{i}]  {label_a}: {elem_str(ea_c) if ea_c else '(absent)'}")
                        print(f"    {marker} [{i}]  {label_b}: {elem_str(eb_c) if eb_c else '(absent)'}")
                else:
                    # Même préfixe, longueurs différentes
                    print(f"  DIVERGENCE {label_a} ≠ {label_b}  (longueurs: {len(la)} vs {len(lb)})")
                    if len(la) > len(lb):
                        ex = la[len(lb)]
                        print(f"    Élément supplémentaire dans {label_a}: {elem_str(ex)}")
                    else:
                        ex = lb[len(la)]
                        print(f"    Élément supplémentaire dans {label_b}: {elem_str(ex)}")
                print()

            if not any_div:
                print("  [OK] Aucune divergence détectée sur ce finding.\n")

        browser.close()


if __name__ == "__main__":
    findings_dir = Path(__file__).parent / "findings"
    analyze(findings_dir)
