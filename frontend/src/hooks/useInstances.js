import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

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
