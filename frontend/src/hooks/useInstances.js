
import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";
/**
 * useInstances
 *
 * Custom hook che recupera la lista delle "instances" da un endpoint API al mount del componente.
 * Esegue una richiesta GET a `${API_BASE}/api/instances`, estrae il campo `instances`
 * dalla risposta e lo inserisce nello stato locale.
 *
 * Comportamento:
 * - La fetch viene eseguita una sola volta grazie alla dependency list vuota di useEffect.
 * - In caso di errore nella chiamata API, lo stato viene impostato a un array vuoto.
 * - La forma attesa della risposta è: `{ instances: [...] }`
 *
 * @returns {Array} Lista delle instances recuperate dall'API.
 */

export default function useInstances() {
  const [instances, setInstances] = useState([]);

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

  return instances;
}
