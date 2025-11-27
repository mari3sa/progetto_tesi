
import styles from "../styles/styles";
/**
 * MeasureItem
 *
 * Un componente UI che visualizza una metrica composta da:
 * - label: nome della misura
 * - value: valore della misura (se assente mostra "—")
 * - description: testo descrittivo sotto al valore
 *
 * @component
 * @param {Object} props - Proprietà del componente.
 * @param {string} props.label - Nome o titolo della metrica.
 * @param {string} props.description - Descrizione breve della metrica.
 * @param {*} [props.value] - Valore della metrica. Se null/undefined viene mostrato "—".
 *
 * @returns {JSX.Element} Il componente renderizzato.
 */

export default function MeasureItem({ label, description, value }) {
  return (
    <div style={styles.measureCard}>
      <div style={styles.measureLabel}>{label}</div>
      <div style={styles.measureValue}>{value ?? "—"}</div>
      <div style={styles.measureDesc}>{description}</div>
    </div>
  );
}
