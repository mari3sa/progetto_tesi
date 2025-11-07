import { useEffect, useState } from "react";

export default function App() {
  const [schema, setSchema] = useState({labels:[], rel_types:[]});
  const [constraints, setConstraints] = useState([]);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/schema")
      .then(r => r.json())
      .then(setSchema);
  }, []);

  function addNodeConstraint() {
    setConstraints(cs => [...cs, {type:"node_label_included", label:""}]);
  }
  function addEdgeConstraint() {
    setConstraints(cs => [...cs, {type:"edge_type_between", from_label:"", rel_type:"", to_label:""}]);
  }
  function updateConstraint(i, patch) {
    setConstraints(cs => cs.map((c,idx) => idx===i ? {...c, ...patch} : c));
  }

  function validate() {
    fetch("http://127.0.0.1:8000/api/constraints/validate", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({constraints})
    })
    .then(r=>r.json())
    .then(setResult);
  }

  function save() {
    fetch("http://127.0.0.1:8000/api/constraints/save", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({constraints})
    })
    .then(r=>r.json())
    .then(setResult);
  }

  return (
    <div style={{color:"white", padding:24}}>
      <h1>Vincoli</h1>
      <button onClick={addNodeConstraint}>+ label</button>
      <button onClick={addEdgeConstraint} style={{marginLeft:8}}>+ relazione</button>

      <div style={{marginTop:16}}>
        {constraints.map((c,i)=>(
          <div key={i} style={{border:"1px solid #555", padding:12, marginBottom:8}}>
            <strong>{c.type}</strong>
            {c.type==="node_label_included" && (
              <div>
                <select value={c.label} onChange={e=>updateConstraint(i,{label:e.target.value})}>
                  <option value="">-- scegli label --</option>
                  {schema.labels.map(l=><option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            )}
            {c.type==="edge_type_between" && (
              <div style={{display:"flex", gap:8}}>
                <select value={c.from_label} onChange={e=>updateConstraint(i,{from_label:e.target.value})}>
                  <option value="">from label</option>
                  {schema.labels.map(l=><option key={l} value={l}>{l}</option>)}
                </select>
                <select value={c.rel_type} onChange={e=>updateConstraint(i,{rel_type:e.target.value})}>
                  <option value="">rel type</option>
                  {schema.rel_types.map(t=><option key={t} value={t}>{t}</option>)}
                </select>
                <select value={c.to_label} onChange={e=>updateConstraint(i,{to_label:e.target.value})}>
                  <option value="">to label</option>
                  {schema.labels.map(l=><option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{marginTop:12}}>
        <button onClick={validate}>Validate</button>
        <button onClick={save} style={{marginLeft:8}}>Save</button>
      </div>

      <pre style={{marginTop:16}}>{result && JSON.stringify(result, null, 2)}</pre>
    </div>
  );
}
