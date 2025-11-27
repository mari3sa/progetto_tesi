import { useState, useMemo } from "react";
import MeasureItem from "./components/MeasureItem";
import styles from "./styles/styles";

import exportConstraintsToFile from "./utils/exportConstraints";
import importConstraintsFromFile from "./utils/importConstraints";
import getUnknownSymbols from "./utils/getUnknownSymbols";

import useInstances from "./hooks/useInstances";
import useSchema from "./hooks/useSchema";
import useConstraints from "./hooks/useConstraints";
import useMeasures from "./hooks/useMeasures";

const API_BASE = "http://127.0.0.1:8000";

/**
 * Selezione dinamica delle misure RPC
 *
 * L'interfaccia permette all'utente di scegliere quali misure di inconsistenza calcolare.
 * Le misure disponibili sono definite in `measureOptions.
 *
 * Lo stato `selectedMeasures` contiene l'elenco delle misure richieste.
 * Quando l’utente clicca "Calcola misure", il frontend invia al backend:
 *
 *   {
 *     constraints: [...],
 *     requested_measures: selectedMeasures
 *   }
 *
 * Il backend calcola solo le misure incluse in `requested_measures`.
 *
 * La sezione dei risultati mostra dinamicamente solo le misure selezionate.
 *
 * Vantaggi:
 * - Migliori prestazioni su grafi grandi
 * - UI più pulita e coerente con le scelte dell'utente
 * - Facile estendere o aggiungere nuove misure
 */

export default function App() {
  // Lista istanze
  const instances = useInstances();

  // Istanza selezionata
  const [selectedInstance, setSelectedInstance] = useState("");

  // Schema del grafo
  const {
    schema,
    loadSchema,
    loadingSchema,
    errorSchema
  } = useSchema(selectedInstance);

  // Vincoli RPC
  const {
    constraintsText,
    setConstraintsText,
    constraintsArray
  } = useConstraints();

  // Misure dal backend
  const {
    summary,
    loadingMeasures,
    errorMeasures,
    computeMeasures
  } = useMeasures(selectedInstance);

  const error = errorSchema || errorMeasures;

  // Selezione istanza + caricamento schema
  function handleSelectInstance(id) {
    setSelectedInstance(id);

    if (!id) return;

    fetch(`${API_BASE}/api/instances/select/${id}`, {
      method: "POST",
    })
      .then((r) => r.json())
      .then(() => loadSchema(id))
      .catch(() => alert("Errore nel selezionare l'istanza."));
  }

  // Warning su simboli non presenti
  const unknownSymbols = useMemo(
    () => getUnknownSymbols(constraintsArray, schema.rel_types),
    [constraintsArray, schema.rel_types]
  );

  const measureOptions = [
  { id: "mu_drastic", label: "I_B(G): misura drastica" },
  { id: "mu_violated_constraints", label: "I_C(G): vincoli violati" },
  { id: "problematic_pairs", label: "I_P(G): coppie problematiche" },
  { id: "minimal_problematic_graphs", label: "I_M(G): MIMS" },
  { id: "minimal_problematic_paths", label: "I_S(G): percorsi minimali" },
  { id: "problematic_edges", label: "I_E(G): archi problematici" },
  { id: "problematic_labels", label: "I_L(G): etichette problematiche" },
  { id: "problematic_vertices", label: "I_V(G): vertici problematici" },
  { id: "I_E_minus", label: "I(E⁻)(G): rimozione archi" },
  { id: "I_E_plus", label: "I(E⁺)(G): aggiunta archi" },
  { id: "I_V_minus", label: "I(V⁻)(G): rimozione vertici" },
];

// Stato misure richieste
const [selectedMeasures, setSelectedMeasures] = useState(
  measureOptions.map((m) => m.id) // di default: tutte selezionate
);

function getMeasureDescription(id) {
  switch (id) {
    case "mu_drastic":
      return "Misura drastica (0 = consistente, 1 = inconsistente)";
    case "mu_violated_constraints":
      return "Numero di vincoli RPC violati";
    case "problematic_pairs":
      return "Numero di coppie problematiche";
    case "minimal_problematic_graphs":
      return "Numero di sottografi minimalmente inconsistenti (MIMS)";
    case "minimal_problematic_paths":
      return "Numero di percorsi problematici minimali";
    case "problematic_edges":
      return "Numero di archi problematici";
    case "problematic_labels":
      return "Numero di etichette problematiche";
    case "problematic_vertices":
      return "Numero di vertici problematici";
    case "I_E_minus":
      return "Archi da rimuovere per ristabilire la coerenza (I(E⁻))";
    case "I_E_plus":
      return "Archi da aggiungere per ristabilire la coerenza (I(E⁺))";
    case "I_V_minus":
      return "Vertici da rimuovere per ristabilire la coerenza (I(V⁻))";
    default:
      return "";
  }
}


  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------
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

        {/* SEZIONE 1: ISTANZA */}
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

          {selectedInstance && (
            <div style={styles.graphPreview}>
              <h3 style={styles.graphTitle}>Grafo selezionato</h3>
              <p style={styles.helperText}>
                L'immagine viene resa dal backend per il grafo corrente.
              </p>

              <div style={styles.graphImageWrapper}>
                <img
                  alt="Anteprima grafo"
                  style={styles.graphImage}
                  src={`${API_BASE}/api/graph/image?instance=${encodeURIComponent(
                    selectedInstance
                  )}`}
                  onError={(e) => (e.currentTarget.style.display = "none")}
                />

                <span style={styles.graphFallback}>
                  Se non vedi l'immagine, verifica l'endpoint
                  <code style={styles.code}> /api/graph/image </code> nel backend.
                </span>
              </div>
            </div>
          )}
        </section>

        {/* SEZIONE 2: SCHEMA */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>2. Schema del grafo</h2>

          <div style={styles.schemaRow}>
            {/* Etichette nodi */}
            <div style={styles.schemaCol}>
              <h3 style={styles.schemaTitle}>Etichette dei nodi</h3>

              {schema.labels.length === 0 ? (
                <p style={styles.helperText}>
                  Nessuna etichetta caricata (seleziona un'istanza e aspetta il caricamento).
                </p>
              ) : (
                <ul style={styles.tagList}>
                  {schema.labels.map((l) => (
                    <li key={l} style={styles.tag}>{l}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* Tipi di relazione */}
            <div style={styles.schemaCol}>
              <h3 style={styles.schemaTitle}>Tipi di relazione</h3>

              {schema.rel_types.length === 0 ? (
                <p style={styles.helperText}>
                  Nessuna relazione caricata (seleziona un'istanza e aspetta il caricamento).
                </p>
              ) : (
                <ul style={styles.tagList}>
                  {schema.rel_types.map((t) => (
                    <li key={t} style={styles.tag}>{t}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* Nodi name */}
            <div style={styles.schemaCol}>
              <h3 style={styles.schemaTitle}>Nodi (name)</h3>

              {schema.nodes.length === 0 ? (
                <p style={styles.helperText}>Nessun nodo caricato (seleziona un'istanza).</p>
              ) : (
                <ul style={styles.tagList}>
                  {schema.nodes.map((n, idx) => (
                    <li key={`${n}-${idx}`} style={styles.tag}>{n}</li>
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
            <code style={styles.code}>C1=child_of⊆son_of∣daughter_of</code><br />
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

          {/* Symbol warning */}
          {unknownSymbols.length > 0 && (
            <div style={styles.warningBox}>
              <strong>Attenzione:</strong> le seguenti etichette non risultano
              presenti tra i tipi di relazione del grafo corrente (warning NON bloccante):
              <div style={styles.tagListInline}>
                {unknownSymbols.map((sym) => (
                  <span key={sym} style={styles.tagWarning}>{sym}</span>
                ))}
              </div>
            </div>
          )}

                    <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
            {measureOptions.map((m) => (
              <label key={m.id} style={{ display: "flex", gap: "6px", fontSize: "13px" }}>
                <input
                  type="checkbox"
                  checked={selectedMeasures.includes(m.id)}
                  onChange={() => {
                    setSelectedMeasures((prev) =>
                      prev.includes(m.id)
                        ? prev.filter((x) => x !== m.id)
                        : [...prev, m.id]
                    );
                  }}
                />
                {m.label}
              </label>
            ))}
          </div>


          <div style={styles.buttonRow}>
            {/* Calcolo misure */}
            <button
              style={styles.primaryButton}
              onClick={() => computeMeasures(constraintsArray, selectedMeasures)}
              disabled={loadingMeasures}
            >
              {loadingMeasures ? "Calcolo in corso..." : "Calcola misure"}
            </button>

            {/* Import/export */}
            <div style={styles.fileControls}>
              <button
                style={styles.secondaryButton}
                onClick={() => exportConstraintsToFile(constraintsArray)}
              >
                Salva vincoli su file
              </button>

              <label style={styles.fileLabel}>
                Carica vincoli da file
                <input
                  type="file"
                  accept=".json"
                  style={{ display: "none" }}
                  onChange={(e) => importConstraintsFromFile(e, setConstraintsText)}
                />
              </label>
            </div>
          </div>
        </section>

       {/* SEZIONE 4: RISULTATI */}
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
      {measureOptions
        .filter((m) => selectedMeasures.includes(m.id))   // 👈 mostra solo misure selezionate
        .map((m) => (
          <MeasureItem
            key={m.id}
            label={m.label}
            description={getMeasureDescription(m.id)}
            value={summary[m.id] ?? "—"}  // 👈 prende il valore dinamicamente dal backend
          />
        ))}
    </div>
  )}
</section>
      </div>
    </div>
  );
}
