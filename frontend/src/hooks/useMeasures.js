import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

/**
 * useMeasures
 *
 * Custom hook che effettua il calcolo delle misure RPC inviando al backend
 * una lista di vincoli (`constraintsArray`) tramite POST.
 *
 * Richiede che l'utente abbia selezionato una "instance" (grafo Neo4j) prima di procedere.
 *
 * Flusso di lavoro:
 * 1. Verifica che `selectedInstance` sia presente.
 * 2. Verifica che esista almeno un vincolo.
 * 3. Invia la richiesta POST a `/api/measures/compute` con il payload:
 *    `{ constraints: string[] }`
 * 4. Aggiorna gli stati:
 *    - `summary`: risultato del backend
 *    - `loadingMeasures`: indica se è in corso il calcolo
 *    - `errorMeasures`: messaggio di errore eventuale
 *
 * Gestione errori:
 * - Se la risposta HTTP non è OK, viene estratto `data.detail` come messaggio.
 * - In caso di errori generici, viene impostato un messaggio di fallback.
 *
 * @param {*} selectedInstance - L'istanza selezionata (necessaria per avviare il calcolo).
 *
 * @returns {Object} Oggetto contenente:
 * @returns {?Object} return.summary - Risultato del calcolo delle misure (summary), oppure null.
 * @returns {boolean} return.loadingMeasures - Stato di caricamento.
 * @returns {string} return.errorMeasures - Eventuale messaggio di errore.
 * @returns {Function} return.computeMeasures - Funzione per avviare il calcolo (`computeMeasures(constraintsArray)`).
 */

export default function useMeasures(selectedInstance) {
  const [summary, setSummary] = useState(null);
  const [loadingMeasures, setLoadingMeasures] = useState(false);
  const [errorMeasures, setErrorMeasures] = useState("");

  function computeMeasures(constraintsArray) {
    if (!selectedInstance) {
      alert("Seleziona prima un grafo / istanza Neo4j.");
      return;
    }
    if (constraintsArray.length === 0) {
      alert("Inserisci almeno un vincolo RPC.");
      return;
    }

    setLoadingMeasures(true);
    setErrorMeasures("");
    setSummary(null);

    fetch(`${API_BASE}/api/measures/compute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ constraints: constraintsArray }),
    })
      .then(async (r) => {
        if (!r.ok) {
          const data = await r.json().catch(() => ({}));
          throw new Error(data.detail || "Errore HTTP");
        }
        return r.json();
      })
      .then((data) => {
        setSummary(data.summary || null);
      })
      .catch((e) => {
        setErrorMeasures(e.message || "Errore nel calcolo delle misure.");
      })
      .finally(() => setLoadingMeasures(false));
  }

  return {
    summary,
    loadingMeasures,
    errorMeasures,
    computeMeasures,
  };
}
