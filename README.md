# SVG ID relink

Open-source illustrators composing diagrams can replace duplicate identifiers with unique IDs and receive an auditable before/after map. This free offline utility reads a static SVG, assigns deterministic identifiers in document order, and writes a new SVG plus CSV mapping. All ID occurrences are renamed, including originally unique ones. It never mutates its input. Both output paths are explicit and must be new, distinct paths; existing files, symlinks and input aliases are refused.

## Pinned scope

The frozen implementation uses only the Python 3 standard library. It accepts well-formed UTF-8-compatible XML with an SVG root, namespace-qualified or unqualified elements, and ASCII identifiers beginning with a letter or underscore. Supported references are local `href` fragments, local `url(#...)` expressions in presentation attributes and simple inline styles, and whitespace-separated accessibility label or description IDs. Quotes around local URL fragments are accepted. Unresolved references remain unresolved; new identifier allocation avoids capturing their names.

Duplicate IDs make the original target ambiguous. The explicit policy is that references to an old spelling resolve to its first occurrence in document order. The map records each occurrence separately, so an illustrator can review and adjust that choice. Later duplicates still receive their own unique IDs. This utility cannot infer intended visual grouping.

Comments, visible text and arbitrary data attributes are preserved as content: they are never searched for references. The adversarial fixture demonstrates this distinction. XML serialization can change attribute quoting, namespace prefixes and empty-element formatting. This is a structural rewrite, not byte preservation. Stylesheet elements, scripts, animations, DTDs and entities are rejected; CSS selectors, animation timing references, external resource relinking and rendering comparison are non-goals.

## Usage and verification

```text
python3 svg_id_relink.py fixtures/duplicate.svg --output repaired.svg --map id-map.csv
```

The SVG contains IDs such as `relink-1`. The CSV columns are `occurrence,before,after`, with one row per original ID occurrence. Successful processing returns exit code 0, including duplicate findings. Invalid or unreadable input, unsupported scope, invalid output arguments and unwritable destinations produce a nonzero exit and a standard-error diagnostic. Run `python3 -m unittest` offline; `fixtures/EXPECTED.md` explains the synthetic corpus.

Frozen release. No updates, no support, no roadmap are promised. Distribution is prepared for the held GitHub repository/profile and repository search; publication is separate.

## Support

Voluntary one-time support only via the held Stripe support rail, retaining this utility's attribution.

Support link: https://buy.stripe.com/bJe28qgTC3es7VmepLa7C01

Counting path: voluntary support payment -> Stripe payment link -> Mercury, Plaid-verified; a support payment is counted once, and the shared rail across utilities is never double-counted.
