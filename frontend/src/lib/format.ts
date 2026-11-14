const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** '2026-11-13' -> '13 Nov 2026'. Empty when there is no date: never show a made-up one. */
export function formatDate(isoStr?: string): string {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  if (isNaN(d.getTime())) return isoStr;
  // UTC getters so a date-only string shows the same day in every timezone
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

/** '₹100687.07 Cr' -> '₹1,00,687.07 Cr' (lakh/crore grouping, as Groww prints it). Grouped numbers are left alone. */
export function groupIndian(text: string): string {
  return text.replace(/\d[\d,]*(\.\d+)?/g, (token) => {
    if (token.includes(',')) return token;
    const [int, frac] = token.split('.');
    if (int.length < 4) return token;
    const head = int.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',');
    return `${head},${int.slice(-3)}${frac ? `.${frac}` : ''}`;
  });
}

/** Groww words exit loads 'Exit load of 1% if ...'; under an "Exit load" label that reads twice. */
export function plainExitLoad(value: string): string {
  return value.replace(/^\s*exit\s+load\s+(of\s+)?/i, '');
}
