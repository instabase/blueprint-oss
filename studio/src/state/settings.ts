export type BlueprintSettings = {
  config_numSamples: number;
  config_timeout: number;
};

export type t = BlueprintSettings & {
  numSimultaneousModelRuns: number;

  numExtraModelRunsToKeep: number;

  annotationMode: boolean;

  flaFields: string;
  requiredDocTags: string;
};

export function build(): t {
  return {
    numSimultaneousModelRuns: 8,
    numExtraModelRunsToKeep: 5,

    /* XXX: Used only for BP projects. */
    annotationMode: false,

    flaFields: '',
    requiredDocTags: '',

    config_numSamples: 10,
    config_timeout: 45,
  };
}

export function fill(original: t): t {
  return {
    ...build(),
    ...original,
  };
}

type Config = {
  num_samples: number;
  timeout: number;
};

export function makeConfig(blueprintSettings: BlueprintSettings): Config {
  return {
    num_samples: blueprintSettings.config_numSamples,
    timeout: blueprintSettings.config_timeout,
  };
}
