export default function getUnknownSymbols(constraintsArray, relTypes) {
  if (!constraintsArray.length) return [];

  const known = new Set(relTypes || []);
  const tokenRegex = /[A-Za-z_][A-Za-z0-9_]*/g;
  const found = new Set();

  for (const line of constraintsArray) {
    const tokens = line.match(tokenRegex) || [];
    for (const t of tokens) {
      if (/^C\d+$/i.test(t)) continue;
      if (["AND", "OR", "NOT"].includes(t.toUpperCase())) continue;
      if (!known.has(t)) {
        found.add(t);
      }
    }
  }

  return Array.from(found);
}
