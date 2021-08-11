export function humanReadableFileSize(bytes: number): string {
  bytes = Math.floor(bytes);

  if (bytes < 0) {
    throw `Invalid file size: ${bytes}`;
  }

  if (bytes < 1_000) {
    return `${bytes} B`;
  } else if (bytes < 1_000_000) {
    return `${Math.floor(bytes / 1_000)} KB`;
  } else if (bytes < 1_000_000_000) {
    return `${Math.floor(bytes / 1_000_000)} MB`;
  } else if (bytes < 1_000_000_000_000) {
    return `${Math.floor(bytes / 1_000_000_000)} GB`;
  } else {
    return `${Math.floor(bytes / 1_000_000_000_000)} TB`;
  }
}
