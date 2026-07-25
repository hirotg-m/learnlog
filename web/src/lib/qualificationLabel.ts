import type { Qualification } from "../types/api";

export function formatQualificationName(
  item: Pick<Qualification, "name" | "abbreviation">
): string {
  return item.abbreviation ? `(${item.abbreviation})${item.name}` : item.name;
}
