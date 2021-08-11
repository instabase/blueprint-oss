import * as Transform from 'studio/util/zoomAndPanTransform';
import useLocalStorageState from 'studio/hooks/useLocalStorageState';

export default function(localStorageSuffix: string) {
  return useLocalStorageState<Transform.t>(
    `Studio.ZoomAndPan-v1-${localStorageSuffix}`,
    Default,
    Transform.isZoomAndPanTransform,
  );
}

const Default = {x: 0, y: 0, scale: 1};
