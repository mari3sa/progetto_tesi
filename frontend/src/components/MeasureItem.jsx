import styles from "../styles/styles";

export default function MeasureItem({ label, description, value }) {
  return (
    <div style={styles.measureCard}>
      <div style={styles.measureLabel}>{label}</div>
      <div style={styles.measureValue}>{value ?? "—"}</div>
      <div style={styles.measureDesc}>{description}</div>
    </div>
  );
}
