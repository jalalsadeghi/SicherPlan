export function buildLoginLocation(
  loginPath: string,
  defaultHomePath: string,
  currentPath?: string,
  includeRedirect: boolean = true,
) {
  return {
    path: loginPath,
    query:
      includeRedirect && currentPath && currentPath !== defaultHomePath
        ? { redirect: encodeURIComponent(currentPath) }
        : {},
  };
}
