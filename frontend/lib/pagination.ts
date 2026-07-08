export async function fetchAllPages<T>(
  fetchPage: (args: { limit: number; offset: number }) => Promise<T[]>,
  pageSize = 100,
): Promise<T[]> {
  const items: T[] = [];
  let offset = 0;

  for (;;) {
    const page = await fetchPage({ limit: pageSize, offset });
    items.push(...page);
    if (page.length < pageSize) {
      break;
    }
    offset += pageSize;
  }

  return items;
}

