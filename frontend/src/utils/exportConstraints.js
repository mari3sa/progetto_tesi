/**
 * exportConstraintsToFile
 *
 * Esporta un array di vincoli RPC in un file JSON scaricabile.
 * Il file generato si chiama **vincoli_rpc.json** e contiene:
 *
 * {
 *   "constraints": [ ... ]
 * }
 *
 * Funzionamento:
 * 1. Converte i vincoli in una stringa JSON formattata.
 * 2. Crea un Blob con MIME type "application/json".
 * 3. Genera un URL temporaneo tramite URL.createObjectURL().
 * 4. Crea dinamicamente un tag <a> invisibile.
 * 5. Forza il download del file tramite `a.click()`.
 * 6. Rilascia l’URL temporaneo per evitare memory leak.
 *
 * @param {string[]} constraintsArray - Lista dei vincoli RPC da esportare.
 */
export default function exportConstraintsToFile(constraintsArray) {
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
