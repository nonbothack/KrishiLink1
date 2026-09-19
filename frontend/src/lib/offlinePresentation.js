export function savedSnapshotLabel(t, cachedAt, language = 'en') {
  const date = cachedAt && Number.isFinite(Date.parse(cachedAt))
    ? new Intl.DateTimeFormat(language, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(cachedAt))
    : null;
  return date ? `${t('savedPrices')} · ${t('lastSaved')}: ${date}` : t('savedPrices');
}
