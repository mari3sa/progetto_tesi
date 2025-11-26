import { useMemo, useState } from "react";

export default function useConstraints() {
  const [constraintsText, setConstraintsText] = useState("");

  const constraintsArray = useMemo(
    () =>
      constraintsText
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
    [constraintsText]
  );

  return {
    constraintsText,
    setConstraintsText,
    constraintsArray,
  };
}
