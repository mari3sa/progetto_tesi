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
