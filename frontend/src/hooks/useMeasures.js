import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

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
