import PACKAGE_JSON from 'studio/../package.json';

export const STUDIO_VERSION = PACKAGE_JSON.version;

type Version = {
  major: number;
  minor: number;
  patch: number;
};

export function parse(version: string): Version | undefined {
  try {
    const match =
      /^(?<major>\d+).(?<minor>\d+).(?<patch>\d+)$/
        .exec(version);
    if (!match) {
      return undefined;
    }

    const [major, minor, patch] = match.slice(1, 4).map(s => Number(s));
    if (!Number.isInteger(major) ||
        !Number.isInteger(minor) ||
        !Number.isInteger(patch))
    {
      return undefined;
    }

    return {major, minor, patch};
  } catch {
    // Pass.
  }
}
