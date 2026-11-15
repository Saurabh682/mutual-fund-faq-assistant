import type { SchemeInfo } from '../types/chat';

/** Schemes grouped by fund house, in the order /meta lists them. Schemes without a fund house share one group. */
export function groupByFundHouse(schemes: SchemeInfo[]): { house: string; schemes: SchemeInfo[] }[] {
  const groups = new Map<string, SchemeInfo[]>();
  for (const s of schemes) {
    const house = s.amc_name || '';
    groups.set(house, [...(groups.get(house) || []), s]);
  }
  return [...groups].map(([house, list]) => ({ house, schemes: list }));
}

/** "HDFC and Mahindra Manulife": the fund houses the catalogue covers, without "Mutual Fund". */
export function fundHouseNames(schemes: SchemeInfo[]): string {
  const names = groupByFundHouse(schemes)
    .map((g) => g.house.replace(/ Mutual Fund$/, ''))
    .filter(Boolean);
  if (names.length <= 2) return names.join(' and ');
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
}

export const shortSchemeName = (name: string) =>
  name.replace(' (Direct - Growth)', '').replace(' (Direct Growth)', '');
