/**
 * importConstraintsFromFile
 *
 * Importa un file JSON contenente vincoli RPC e aggiorna il testo
 * multilinea tramite `setConstraintsText`. Supporta **diversi formati**
 * perché i file possono provenire da backend differenti o da versioni precedenti
 * dell’applicazione.
 *
 * Formati supportati (in ordine di priorità):
 *
 * 1️ `{ "constraints": [...] }`
 * 2️ `{ "payload": { "constraints": [...] } }`
 * 3️ `{ "model_dump": { "constraints": [...] } }`
 *
 * Se nessuna di queste strutture è valida, viene mostrato un messaggio di errore.
 *
 * Funzionamento:
 * - Usa `FileReader` per leggere il file selezionato dall’utente.
 * - Effettua il parsing JSON.
 * - Identifica automaticamente il campo che contiene i vincoli.
 * - Li converte in testo multilinea, separando ogni vincolo con `\n`.
 *
 * @param {Event} e - L'evento `onChange` dell’input type="file".
 * @param {Function} setConstraintsText - Setter React che aggiorna il testo multilinea dei vincoli.
 */
export default function importConstraintsFromFile(e, setConstraintsText) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();

  reader.onload = (evt) => {
    try {
      const text = evt.target.result;
      const json = JSON.parse(text);

      if (json.constraints && Array.isArray(json.constraints)) {
        setConstraintsText(json.constraints.join("\n"));
        return;
      }

      if (
        json.payload &&
        json.payload.constraints &&
        Array.isArray(json.payload.constraints)
      ) {
        setConstraintsText(json.payload.constraints.join("\n"));
        return;
      }

      if (json.model_dump && json.model_dump.constraints) {
        setConstraintsText(json.model_dump.constraints.join("\n"));
        return;
      }

      alert("File non valido: deve contenere { constraints: [...] } o payload.constraints.");
    } catch {
      alert("Errore nel leggere il file di vincoli (JSON non valido?).");
    }
  };

  reader.readAsText(file, "utf-8");
}
