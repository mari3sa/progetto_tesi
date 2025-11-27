import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

/**
 * useSchema
 *
 * Custom hook che carica lo schema del grafo + i nodi appartenenti
 * all'istanza selezionata. Esegue due richieste in parallelo:
 *
 * 1. `/api/schema` — restituisce labels e rel_types
 * 2. `/api/graph/nodes?instance=X` — restituisce i nodi dell'istanza selezionata
 *
 * Se non viene fornito `instanceId`, il hook usa `selectedInstance`.
 *
 * Struttura dello schema restituito:
 * {
 *   labels: string[],
 *   rel_types: string[],
 *   nodes: object[]
 * }
 *
 * Gestione stati:
 * - `schema` → lo schema completo
 * - `loadingSchema` → true durante il caricamento
 * - `errorSchema` → messaggi di errore
 *
 * Gestione errori:
 * - In caso di problemi con una delle fetch, viene impostato
 *   uno schema vuoto e valorizzato `errorSchema`.
 *
 * @param {*} selectedInstance - Identificativo dell'istanza selezionata (opzionale).
 *
 * @returns {Object} Oggetto contenente:
 * @returns {Object} return.schema - Schema del grafo: { labels, rel_types, nodes }
 * @returns {Function} return.loadSchema - Funzione per avviare il caricamento (`loadSchema(instanceId?)`).
 * @returns {boolean} return.loadingSchema - True mentre lo schema è in caricamento.
 * @returns {string} return.errorSchema - Eventuale messaggio di errore.
 */

export default function useSchema(selectedInstance) {
  const [schema, setSchema] = useState({
    labels: [],
    rel_types: [],
    nodes: [],
  });
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [errorSchema, setErrorSchema] = useState("");

  function loadSchema(instanceId) {
    const inst = instanceId || selectedInstance;
    setLoadingSchema(true);
    setErrorSchema("");

    const schemaPromise = fetch(`${API_BASE}/api/schema`).then((r) => r.json());

    const nodesPromise = inst
      ? fetch(
          `${API_BASE}/api/graph/nodes?instance=${encodeURIComponent(inst)}`
        ).then((r) => r.json())
      : Promise.resolve({ nodes: [] });

    Promise.all([schemaPromise, nodesPromise])
      .then(([schemaData, nodesData]) => {
        setSchema({
          labels: schemaData.labels || [],
          rel_types: schemaData.rel_types || [],
          nodes: nodesData.nodes || [],
        });
      })
      .catch(() => {
        setSchema({ labels: [], rel_types: [], nodes: [] });
        setErrorSchema("Errore nel caricare lo schema dal backend.");
      })
      .finally(() => setLoadingSchema(false));
  }

  return { schema, loadSchema, loadingSchema, errorSchema };
}
