# Synthetic fixture expectations

- `duplicate.svg`: three ID occurrences receive unique replacement IDs. Both original paint IDs map separately; the fill reference resolves to the first original paint occurrence. The use reference follows the renamed box.
- `references.svg`: quoted local url fragment and href fragment follow their rewritten targets.
- `adversarial.svg`: comment content, visible text and the data-note attribute remain unchanged. Only the actual ID and fill reference change. Parsing identifies element attributes; no global text substitution occurs.
- `clean.svg`: no IDs or references; the CSV contains only its header. XML serialization may alter whitespace or empty-element syntax.
- `unknown.svg`: the missing relink-1 target stays missing; allocation skips that spelling, and the shape receives relink-2.
