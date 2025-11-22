import { useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  // Istanza / grafo selezionato
  const [instances, setInstances] = useState([]);
  const [selectedInstance, setSelectedInstance] = useState("");

  // Schema corrente (etichette nodi + tipi di relazione + nodi)
  const [schema, setSchema] = useState({
    labels: [],
    rel_types: [],
    nodes: [],      // 🔹 NODI (name)
  });

  // Testo dei vincoli RPC (multi-linea)
  const [constraintsText, setConstraintsText] = useState("");

  // Risultato delle misure
  const [summary, setSummary] = useState(null);

  // Stato UI / errori
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [loadingMeasures, setLoadingMeasures] = useState(false);
  const [error, setError] = useState("");

  // =========================================================
  // 1️⃣ Carica lista istanze Neo4j
  // =========================================================
  useEffect(() => {
    fetch(`${API_BASE}/api/instances`)
      .then((r) => r.json())
      .then((data) => {
        setInstances(data.instances || []);
      })
      .catch(() => {
        setInstances([]);
      });
  }, []);

  // =========================================================
  // 2️⃣ Quando scelgo un'istanza → POST /select + carico schema
  // =========================================================
  function handleSelectInstance(id) {
    setSelectedInstance(id);
    setSummary(null);
    setError("");
    if (!id) return;

    fetch(`${API_BASE}/api/instances/select/${id}`, {
      method: "POST",
    })
      .then((r) => r.json())
      .then(() => {
        // 🔹 passiamo l'id per essere sicuri di usarlo in loadSchema
        loadSchema(id);
      })
      .catch((e) => {
        console.error(e);
        setError("Errore nel selezionare l'istanza.");
      });
  }

  // =========================================================
  // 3️⃣ Carica schema (etichette nodi + relazioni + nodi) per il grafo
  // =========================================================
  function loadSchema(instanceId) {
    const inst = instanceId || selectedInstance;
    setLoadingSchema(true);
    setError("");

    // 🔹 schema + nodi in parallelo
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
      .catch((e) => {
        console.error(e);
        setSchema({ labels: [], rel_types: [], nodes: [] });
        setError("Errore nel caricare lo schema dal backend.");
      })
      .finally(() => setLoadingSchema(false));
  }

  // =========================================================
  // 4️⃣ Parsing vincoli RPC in array di stringhe
  // =========================================================
  const constraintsArray = useMemo(
    () =>
      constraintsText
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
    [constraintsText]
  );

  // =========================================================
  // 5️⃣ Warning su etichette non presenti nel grafo
  //     (NON bloccante)
  // =========================================================
  const unknownSymbols = useMemo(() => {
    if (!constraintsArray.length) return [];

    // Prendiamo le rel_types dal backend e le usiamo come "alfabeto noto"
    const known = new Set(schema.rel_types || []);

    // Regex semplicissima per catturare parole tipo child_of, son_of, ...
    const tokenRegex = /[A-Za-z_][A-Za-z0-9_]*/g;

    const found = new Set();

    for (const line of constraintsArray) {
      const tokens = line.match(tokenRegex) || [];
      for (const t of tokens) {
        // Filtro simboli ovvi che NON sono etichette (C1, C2, ecc., e simboli comuni)
        if (/^C\d+$/i.test(t)) continue;
        if (["AND", "OR", "NOT"].includes(t.toUpperCase())) continue;
        if (!known.has(t)) {
          found.add(t);
        }
      }
    }

    return Array.from(found);
  }, [constraintsArray, schema.rel_types]);

  // =========================================================
  // 6️⃣ Calcolo delle misure di inconsistenza
  // =========================================================
  function computeMeasures() {
    if (!selectedInstance) {
      alert("Seleziona prima un grafo / istanza Neo4j.");
      return;
    }
    if (constraintsArray.length === 0) {
      alert("Inserisci almeno un vincolo RPC.");
      return;
    }

    setLoadingMeasures(true);
    setError("");
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
        console.error(e);
        setError(e.message || "Errore nel calcolo delle misure.");
      })
      .finally(() => setLoadingMeasures(false));
  }

  // =========================================================
  // 7️⃣ Salva / carica vincoli da file (lato client)
  // =========================================================
  function exportConstraintsToFile() {
    const blob = new Blob(
      [JSON.stringify({ constraints: constraintsArray }, null, 2)],
      { type: "application/json" }
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vincoli_rpc.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function importConstraintsFromFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const text = evt.target.result;
        const json = JSON.parse(text);
        if (Array.isArray(json.constraints)) {
          setConstraintsText(json.constraints.join("\n"));
        } else {
          alert("File non valido: manca la chiave 'constraints'.");
        }
      } catch (err) {
        console.error(err);
        alert("Errore nel leggere il file di vincoli.");
      }
    };
    reader.readAsText(file, "utf-8");
  }

  // =========================================================
  // 8️⃣ UI
  // =========================================================
  return (
    <div style={styles.page}>
      <div style={styles.container}>
        {/* HEADER */}
        <header style={styles.header}>
          <h1 style={styles.title}>Misure di inconsistenza per grafi Neo4j</h1>
          <p style={styles.subtitle}>
            Seleziona il grafo, inserisci i vincoli RPC e calcola le misure.
          </p>
        </header>

        {/* SEZIONE 1: SCELTA GRAFO */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>1. Seleziona il grafo</h2>
          <div style={styles.row}>
            <div style={{ flex: 1 }}>
              <label style={styles.label}>Istanza / progetto Neo4j:</label>
              <select
                style={styles.select}
                value={selectedInstance}
                onChange={(e) => handleSelectInstance(e.target.value)}
              >
                <option value="">— seleziona —</option>
                {instances.map((inst) => (
                  <option key={inst.id} value={inst.id}>
                    {inst.id} ({inst.bolt})
                  </option>
                ))}
              </select>
              {loadingSchema && (
                <p style={styles.helperText}>Caricamento schema in corso...</p>
              )}
            </div>
          </div>

          {/* Immagine del grafo */}
          {selectedInstance && (
            <div style={styles.graphPreview}>
              <h3 style={styles.graphTitle}>Grafo selezionato</h3>
              <p style={styles.helperText}>
                L&apos;immagine viene resa dal backend per il grafo corrente.
              </p>
              <div style={styles.graphImageWrapper}>
                <img
                  alt="Anteprima grafo"
                  style={styles.graphImage}
                  src={`${API_BASE}/api/graph/image?instance=${encodeURIComponent(
                    selectedInstance
                  )}`}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
                <span style={styles.graphFallback}>
                  Se non vedi l&apos;immagine, verifica l&apos;endpoint
                  <code style={styles.code}> /api/graph/image </code> nel
                  backend.
                </span>
              </div>
            </div>
          )}
        </section>

        {/* SEZIONE 2: SCHEMA (NODI + RELAZIONI + NODI NAME) */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>2. Schema del grafo</h2>
          <div style={styles.schemaRow}>
            <div style={styles.schemaCol}>
              <h3 style={styles.schemaTitle}>Etichette dei nodi</h3>
              {schema.labels.length === 0 ? (
                <p style={styles.helperText}>
                  Nessuna etichetta caricata (seleziona un&apos;istanza e
                  aspetta il caricamento).
                </p>
              ) : (
                <ul style={styles.tagList}>
                  {schema.labels.map((l) => (
                    <li key={l} style={styles.tag}>
                      {l}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div style={styles.schemaCol}>
              <h3 style={styles.schemaTitle}>Tipi di relazione</h3>
              {schema.rel_types.length === 0 ? (
                <p style={styles.helperText}>
                  Nessuna relazione caricata (seleziona un&apos;istanza e
                  aspetta il caricamento).
                </p>
              ) : (
                <ul style={styles.tagList}>
                  {schema.rel_types.map((t) => (
                    <li key={t} style={styles.tag}>
                      {t}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* 🔹 NODI (name) */}
            <div style={styles.schemaCol}>
              <h3 style={styles.schemaTitle}>Nodi (name)</h3>
              {(!schema.nodes || schema.nodes.length === 0) ? (
                <p style={styles.helperText}>
                  Nessun nodo caricato (seleziona un&apos;istanza).
                </p>
              ) : (
                <ul style={styles.tagList}>
                  {schema.nodes.map((n, idx) => (
                    <li key={`${n}-${idx}`} style={styles.tag}>
                      {n}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>

        {/* SEZIONE 3: VINCOLI RPC */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>3. Vincoli RPC</h2>
          <p style={styles.helperText}>
            Inserisci uno o più vincoli, uno per riga. Esempi:
            <br />
            <code style={styles.code}>
              C1=child_of⊆son_of∣daughter_of
            </code>
            <br />
            <code style={styles.code}>
              C2=child_of.(brother_of∣sister_of)⊆nephew_of∣niece_of
            </code>
          </p>

          <textarea
            style={styles.textarea}
            rows={6}
            placeholder={`C1=child_of⊆son_of∣daughter_of
C2=child_of.(brother_of∣sister_of)⊆nephew_of∣niece_of
C3=child_of.child_of⊆grandson_of∣granddaughter_of
C4=son_of.child_of⊆grandson_of`}
            value={constraintsText}
            onChange={(e) => setConstraintsText(e.target.value)}
          />

          {/* Warning etichette non presenti ma NON bloccante */}
          {unknownSymbols.length > 0 && (
            <div style={styles.warningBox}>
              <strong>Attenzione:</strong> le seguenti etichette non risultano
              presenti tra i tipi di relazione del grafo corrente (warning
              NON bloccante):
              <div style={styles.tagListInline}>
                {unknownSymbols.map((sym) => (
                  <span key={sym} style={styles.tagWarning}>
                    {sym}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Bottoni calcolo + import/export */}
          <div style={styles.buttonRow}>
            <button
              style={styles.primaryButton}
              onClick={computeMeasures}
              disabled={loadingMeasures}
            >
              {loadingMeasures ? "Calcolo in corso..." : "Calcola misure"}
            </button>

            <div style={styles.fileControls}>
              <button
                style={styles.secondaryButton}
                onClick={exportConstraintsToFile}
              >
                Salva vincoli su file
              </button>
              <label style={styles.fileLabel}>
                Carica vincoli da file
                <input
                  type="file"
                  accept=".json"
                  style={{ display: "none" }}
                  onChange={importConstraintsFromFile}
                />
              </label>
            </div>
          </div>
        </section>

        {/* SEZIONE 4: RISULTATI DELLE MISURE */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>4. Misure di inconsistenza</h2>

          {error && <div style={styles.errorBox}>{error}</div>}

          {!summary && !error && (
            <p style={styles.helperText}>
              Nessun risultato ancora. Inserisci i vincoli e premi{" "}
              <strong>Calcola misure</strong>.
            </p>
          )}

          {summary && (
            <div style={styles.measuresGrid}>
              <MeasureItem
                label="I_B(G) = μ_d"
                description="Coerenza drastica (0 = coerente, 1 = incoerente)"
                value={summary.mu_drastic}
              />
              <MeasureItem
                label="I_C(G)"
                description="Numero di vincoli RPC violati"
                value={summary.mu_violated_constraints}
              />
              <MeasureItem
                label="I_P(G)"
                description="Numero di coppie problematiche"
                value={summary.problematic_pairs}
              />
              <MeasureItem
                label="I_M(G)"
                description="Numero di sottografi minimalmente inconsistenti"
                value={summary.I_M}
              />
              <MeasureItem
                label="I_S(G)"
                description="Numero di percorsi problematici minimali"
                value={summary.I_S}
              />
              <MeasureItem
                label="I_E(G)"
                description="Numero di archi problematici"
                value={summary.problematic_edges}
              />
              <MeasureItem
                label="I_L(G)"
                description="Numero di etichette problematiche"
                value={summary.problematic_labels}
              />
              <MeasureItem
                label="I_V(G)"
                description="Numero di vertici problematici"
                value={summary.problematic_vertices}
              />
              <MeasureItem
                label="I_(E⁻)(G)"
                description="Archi da rimuovere per ristabilire la coerenza"
                value={summary.I_E_minus}
              />
              <MeasureItem
                label="I_(E⁺)(G)"
                description="Archi da aggiungere per ristabilire la coerenza"
                value={summary.I_E_plus}
              />
              <MeasureItem
                label="I_(V⁻)(G)"
                description="Vertici da rimuovere per ristabilire la coerenza"
                value={summary.I_V_minus}
              />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

// =========================================================
// COMPONENTE PER UNA SINGOLA MISURA
// =========================================================
function MeasureItem({ label, description, value }) {
  return (
    <div style={styles.measureCard}>
      <div style={styles.measureLabel}>{label}</div>
      <div style={styles.measureValue}>{value ?? "—"}</div>
      <div style={styles.measureDesc}>{description}</div>
    </div>
  );
}

// =========================================================
// STILI (inline) — tema chiaro e pulito
// =========================================================
const styles = {
  page: {
    minHeight: "100vh",
    background: "#f5f7fb",
    padding: "24px",
    fontFamily:
      "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    color: "#1f2933",
  },
  container: {
    maxWidth: "1100px",
    margin: "0 auto",
  },
  header: {
    marginBottom: "24px",
  },
  title: {
    margin: 0,
    fontSize: "26px",
    fontWeight: 700,
    color: "#111827",
  },
  subtitle: {
    marginTop: "8px",
    color: "#4b5563",
    fontSize: "14px",
  },
  card: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "18px 20px",
    marginBottom: "18px",
    boxShadow: "0 8px 18px rgba(15, 23, 42, 0.06)",
    border: "1px solid #e5e7eb",
  },
  sectionTitle: {
    margin: 0,
    marginBottom: "12px",
    fontSize: "18px",
    fontWeight: 600,
    color: "#111827",
  },
  row: {
    display: "flex",
    gap: "16px",
    alignItems: "center",
  },
  label: {
    display: "block",
    fontSize: "13px",
    fontWeight: 500,
    color: "#374151",
    marginBottom: "4px",
  },
  select: {
    width: "100%",
    padding: "8px 10px",
    borderRadius: "8px",
    border: "1px solid #d1d5db",
    fontSize: "14px",
    outline: "none",
  },
  helperText: {
    marginTop: "6px",
    fontSize: "12px",
    color: "#6b7280",
  },
  graphPreview: {
    marginTop: "16px",
  },
  graphTitle: {
    margin: 0,
    marginBottom: "6px",
    fontSize: "15px",
    fontWeight: 600,
  },
  graphImageWrapper: {
    marginTop: "8px",
    borderRadius: "10px",
    border: "1px dashed #d1d5db",
    padding: "10px",
    textAlign: "center",
    background: "#f9fafb",
  },
  graphImage: {
    maxWidth: "100%",
    maxHeight: "280px",
    borderRadius: "8px",
    display: "block",
    margin: "0 auto",
  },
  graphFallback: {
    fontSize: "12px",
    color: "#9ca3af",
  },
  code: {
    fontFamily: "monospace",
    background: "#f3f4f6",
    padding: "2px 5px",
    borderRadius: "4px",
    fontSize: "12px",
  },
  schemaRow: {
    display: "flex",
    gap: "24px",
    flexWrap: "wrap",
  },
  schemaCol: {
    flex: 1,
    minWidth: "220px",
  },
  schemaTitle: {
    margin: 0,
    marginBottom: "8px",
    fontSize: "15px",
    fontWeight: 600,
  },
  tagList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  tag: {
    padding: "4px 8px",
    borderRadius: "999px",
    background: "#eef2ff",
    color: "#3730a3",
    fontSize: "12px",
  },
  tagListInline: {
    marginTop: "6px",
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  tagWarning: {
    padding: "3px 7px",
    borderRadius: "999px",
    background: "#fef3c7",
    color: "#92400e",
    fontSize: "12px",
  },
  textarea: {
    width: "100%",
    marginTop: "8px",
    padding: "8px 10px",
    borderRadius: "8px",
    border: "1px solid #d1d5db",
    fontSize: "13px",
    resize: "vertical",
  },
  warningBox: {
    marginTop: "10px",
    padding: "8px 10px",
    borderRadius: "8px",
    background: "#fffbeb",
    border: "1px solid #fcd34d",
    fontSize: "12px",
    color: "#78350f",
  },
  buttonRow: {
    marginTop: "14px",
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
    alignItems: "center",
    justifyContent: "space-between",
  },
  primaryButton: {
    padding: "8px 16px",
    borderRadius: "999px",
    border: "none",
    background: "#2563eb",
    color: "#ffffff",
    fontSize: "14px",
    fontWeight: 500,
    cursor: "pointer",
  },
  secondaryButton: {
    padding: "7px 14px",
    borderRadius: "999px",
    border: "1px solid #d1d5db",
    background: "#ffffff",
    color: "#111827",
    fontSize: "13px",
    cursor: "pointer",
  },
  fileControls: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  fileLabel: {
    padding: "7px 14px",
    borderRadius: "999px",
    border: "1px dashed #d1d5db",
    background: "#ffffff",
    color: "#111827",
    fontSize: "13px",
    cursor: "pointer",
  },
  errorBox: {
    padding: "10px 12px",
    borderRadius: "8px",
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#b91c1c",
    fontSize: "13px",
    marginBottom: "10px",
  },
  measuresGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "12px",
    marginTop: "10px",
  },
  measureCard: {
    borderRadius: "10px",
    border: "1px solid #e5e7eb",
    padding: "10px 12px",
    background: "#f9fafb",
  },
  measureLabel: {
    fontSize: "13px",
    fontWeight: 600,
    color: "#111827",
  },
  measureValue: {
    marginTop: "4px",
    fontSize: "18px",
    fontWeight: 700,
    color: "#2563eb",
  },
  measureDesc: {
    marginTop: "4px",
    fontSize: "11px",
    color: "#6b7280",
  },
};
