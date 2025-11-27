
/**
 * getUnknownSymbols
 *
 * Analizza un insieme di vincoli RPC e restituisce tutti i simboli
 * (token alfabetici) che non appartengono alla lista dei `relTypes`
 * fornita. Utile per individuare errori di digitazione, relazioni mancanti
 * nello schema o simboli non supportati.
 *
 * Definizione del riconoscimento token:
 * - Identificatori: `[A-Za-z_][A-Za-z0-9_]*`
 * - Ignorati:
 *   - Pattern `C<number>` → es. C1, C2, C30
 *   - Operatori logici: AND, OR, NOT (case-insensitive)
 *
 * Esempio:
 * constraints: ["A > B", "X AND Y", "R1 OR R2"]
 * relTypes: ["A", "B", "R1"]
 * → unknown: ["X", "Y", "R2"]  (ordine non garantito)
 *
 * @param {string[]} constraintsArray - Lista di vincoli RPC da analizzare.
 * @param {string[]} relTypes - Lista dei simboli riconosciuti (relazioni valide).
 *
 * @returns {string[]} Lista dei simboli sconosciuti trovati nei vincoli.
 */
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
