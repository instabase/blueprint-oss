export default function shortDocName(fullDocName: string): string {
  return lastPathComponent(fullDocName);
}

function lastPathComponent(path: string): string {
  const comps = path.split('/');
  return comps[comps.length - 1];
}
