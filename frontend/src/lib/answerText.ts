export interface ParsedContent {
  prose: string;
  metrics: { label: string; value: string }[];
  note?: string;
}

const isSeparatorRow = (line: string) => /^\|?[\s:|-]+\|?$/.test(line) && line.includes('-');
const isTableRow = (line: string) => line.startsWith('|') && line.endsWith('|');

/** Splits backend answer text into prose, a label/value list (markdown table rows) and an optional note. */
export function parseAnswerText(rawText: string): ParsedContent {
  const lines = rawText.split('\n').map((l) => l.trim());
  const proseLines: string[] = [];
  const metrics: { label: string; value: string }[] = [];
  let note: string | undefined;

  lines.forEach((trimmed, i) => {
    if (!trimmed || isSeparatorRow(trimmed)) return;

    if (isTableRow(trimmed)) {
      // A row followed by a separator row is the table header ("| Aspect | Detail |"), not data
      if (isSeparatorRow(lines[i + 1] ?? '')) return;
      const parts = trimmed.split('|').map((p) => p.trim()).filter(Boolean);
      if (parts.length >= 2) {
        const label = parts[0].replace(/\*\*/g, '').trim();
        const value = parts[1].replace(/\*\*/g, '').trim();
        const l = label.toLowerCase();
        // Fund house, data source and AMFI code are in the citation footer or add nothing to the answer
        if (label && value && !l.includes('metric') && !l.includes('data source') && !l.includes('fund house') && !l.includes('amfi code')) {
          metrics.push({ label, value });
        }
      }
    } else if (trimmed.toLowerCase().startsWith('note:')) {
      note = trimmed.replace(/^note:\s*/i, '');
    } else if (!trimmed.toLowerCase().startsWith('source:')) {
      proseLines.push(trimmed);
    }
  });

  return { prose: proseLines.join('\n\n'), metrics, note };
}
