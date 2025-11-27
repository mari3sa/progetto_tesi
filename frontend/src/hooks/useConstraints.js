

import { useMemo, useState } from "react";
/**
 * useConstraints
 *
 * Custom hook che gestisce una lista di "vincoli" (constraints) inseriti come testo multilinea.
 * Fornisce sia il testo grezzo che una versione processata in array.
 *
 * Funzionamento:
 * - L'utente inserisce del testo con più righe.
 * - Ogni riga viene trim-mata e ignorata se vuota.
 * - Il risultato è un array di stringhe pulite, calcolato in modo ottimizzato con useMemo.
 *
 * @returns {Object} Oggetto contenente:
 * @returns {string} return.constraintsText - Testo completo dei vincoli in formato multilinea.
 * @returns {Function} return.setConstraintsText - Setter per aggiornare il testo dei vincoli.
 * @returns {string[]} return.constraintsArray - Lista dei vincoli, uno per riga.
 *
 */
export default function useConstraints() {
  const [constraintsText, setConstraintsText] = useState("");

  const constraintsArray = useMemo(
    () =>
      constraintsText
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
    [constraintsText]
  );

  return {
    constraintsText,
    setConstraintsText,
    constraintsArray,
  };
}
