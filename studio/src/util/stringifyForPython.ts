// We by convention use triple-single-quotes in Python script JS string literals.

function writeStringComponent(s: string): string {
  return String.raw`r'''${s}'''`;
}

export function writeString(s: string): string {
  const components = s.split("'");
  return '(' + components.map(writeStringComponent).join('+"\'"+') + ')';
}

export function stringify(o: object): string {
  return writeString(JSON.stringify(o));
}
