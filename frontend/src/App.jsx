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

          <div style={styles.buttonRow}>
            {/* Calcolo misure */}
            <button
              style={styles.primaryButton}
              onClick={() => computeMeasures(constraintsArray)}
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
              <MeasureItem
                label="I_B(G)"
                description="Misura drastica (0 = consistente, 1 = inconsistente)"
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
                label="I_M (G)"
                description="Numero di sottografi minimalmente inconsistenti"
                value={summary.minimal_problematic_graphs}
              />
              <MeasureItem
                label="I_S (G)"
                description="Numero di percorsi problematici minimali"
                value={summary.minimal_problematic_paths}
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
