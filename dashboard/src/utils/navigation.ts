/**
 * Navigate to a path while preserving current query parameters
 * Returns an object with pathname and search for React Router
 * Preserves the raw query string without re-encoding
 */
export function navigateWithQuery(path: string) {
  return {
    pathname: path,
    search: window.location.search
  };
}
