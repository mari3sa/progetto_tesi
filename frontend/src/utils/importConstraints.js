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
