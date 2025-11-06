import { useState,useEffect } from 'react'
import './App.css'

export default function App() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    fetch("/api/hello")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch((e) => setErr(e.message));
  }, []);

  return (
    <div style={{ color: "white", fontFamily: "sans-serif", padding: 32 }}>
      <h1 style={{ fontSize: 64, margin: 0 }}>Frontend OK ✅</h1>
      <h2>Risposta dal backend:</h2>
      <pre>{data ? JSON.stringify(data, null, 2) : "Caricamento..."}</pre>
      {err && <p style={{ color: "salmon" }}>Errore: {err}</p>}
    </div>
  );
}
