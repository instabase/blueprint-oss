type FileSystemWritableFileStream = {
  write: (s: string) => Promise<void>;
};

type FileHandle = {
  getFile: () => Promise<File>;
  createWritable: () => Promise<FileSystemWritableFileStream>;
};

export type t = {
  entries: () => any;
  getFileHandle: (s: string) => Promise<FileHandle>;
};
