const absoluteUrl = (path) => {
  const site = import.meta.env.VITE_PUBLIC_SITE_URL || (typeof window !== 'undefined' ? window.location.origin : '');
  if (!site) return null;
  const canonicalPath = path === '/' ? '/' : path.replace(/\/+$/, '');
  return new URL(canonicalPath, site.endsWith('/') ? site : `${site}/`).toString();
};

function meta(selector, attributes, value) {
  let node = document.head.querySelector(selector);
  if (!node) {
    node = document.createElement('meta');
    Object.entries(attributes).forEach(([name, content]) => node.setAttribute(name, content));
    document.head.append(node);
  }
  node.setAttribute('content', value);
}

export function updatePageMetadata({ title, description, path, noindex = false }) {
  if (typeof document === 'undefined') return;
  document.title = title;
  meta('meta[name="description"]', { name: 'description' }, description);
  meta('meta[property="og:title"]', { property: 'og:title' }, title);
  meta('meta[property="og:description"]', { property: 'og:description' }, description);
  meta('meta[property="og:type"]', { property: 'og:type' }, 'website');
  meta('meta[name="twitter:card"]', { name: 'twitter:card' }, 'summary_large_image');
  meta('meta[name="twitter:title"]', { name: 'twitter:title' }, title);
  meta('meta[name="twitter:description"]', { name: 'twitter:description' }, description);
  meta('meta[name="robots"]', { name: 'robots' }, noindex ? 'noindex,follow' : 'index,follow');
  const canonical = absoluteUrl(path);
  let link = document.head.querySelector('link[rel="canonical"]');
  if (canonical) {
    if (!link) {
      link = document.createElement('link');
      link.rel = 'canonical';
      document.head.append(link);
    }
    link.href = canonical;
    meta('meta[property="og:url"]', { property: 'og:url' }, canonical);
  } else {
    link?.remove();
  }
}

export function usePageMetadata(metadata) {
  useEffect(() => {
    updatePageMetadata(metadata);
  }, [metadata.title, metadata.description, metadata.path, metadata.noindex]);
}
import { useEffect } from 'react';
