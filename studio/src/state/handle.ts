type FileSystemWritableFileStream = {
  write: (s: string) => Promise<void>;
  close: () => Promise<void>;
};

export type FileHandle = {
  getFile: () => Promise<File>;
  createWritable: () => Promise<FileSystemWritableFileStream>;
};

export type t = {
  entries: () => any;
  getFileHandle: (s: string, opts?: any) => Promise<FileHandle>;
  getDirectoryHandle: (s: string, opts?: any) => Promise<t>;
};
