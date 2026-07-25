const qualificationColorMap: Record<string, string> = {
  red: "#ef6060",
  orange: "#f5a445",
  yellow: "#f0d64c",
  green: "#67c46c",
  teal: "#2fbbad",
  blue: "#4f86f7",
  indigo: "#7476ef",
  pink: "#f07ecf",
  brown: "#a37a4f",
  gray: "#a5adb8",
};

export function getQualificationColor(color: string): string {
  return qualificationColorMap[color] ?? "#a5adb8";
}
