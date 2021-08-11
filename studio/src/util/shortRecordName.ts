export default function shortRecordName(fullRecordName: string): string {
  return lastPathComponent(fullRecordName);
}

function lastPathComponent(path: string): string {
  const comps = path.split('/');
  return comps[comps.length - 1];
}
