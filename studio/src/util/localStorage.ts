export function loadFromLocalStorage<T>(
  localStorageKey: string,
  defaultValue: T,
  validator: (t: unknown) => t is T,
) {
  const stringValue = localStorage.getItem(localStorageKey);
  if (stringValue == null) { return defaultValue; }

  try {
    const value = JSON.parse(stringValue);
    if (validator(value)) {
      return value;
    } else {
      return defaultValue;
    }
  } catch(_error) {
    return defaultValue;
  }
}

export function saveToLocalStorage<T>(
  localStorageKey: string,
  value: T,
) {
  localStorage.setItem(localStorageKey, JSON.stringify(value));
}
