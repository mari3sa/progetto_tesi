import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

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
