import { getCollection, getEntry, type CollectionEntry } from 'astro:content';
import links from '../../content/links.json';

export type Project = CollectionEntry<'projects'>;
export type Post = CollectionEntry<'posts'>;

/** Projects: featured first, then by order, then newest year. */
export async function getProjects(): Promise<Project[]> {
  const all = await getCollection('projects');
  return all.sort(
    (a, b) =>
      Number(b.data.featured) - Number(a.data.featured) ||
      a.data.order - b.data.order ||
      b.data.year - a.data.year,
  );
}

/** Posts: newest first. */
export async function getPosts(): Promise<Post[]> {
  const all = await getCollection('posts');
  return all.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export async function getAbout() {
  return getEntry('pages', 'about');
}

export type Links = typeof links;
export function getLinks(): Links {
  return links;
}

/** Social links as [label, href] pairs, empty ones dropped. */
export function getLinkList(): { label: string; href: string }[] {
  const l = getLinks();
  const out: { label: string; href: string }[] = [];
  if (l.email) out.push({ label: 'Email', href: `mailto:${l.email}` });
  if (l.github) out.push({ label: 'GitHub', href: l.github });
  if (l.linkedin) out.push({ label: 'LinkedIn', href: l.linkedin });
  if (l.x) out.push({ label: 'X', href: l.x });
  if (l.resume) out.push({ label: 'Resume', href: l.resume });
  return out;
}

export function formatDate(d: Date): string {
  return d.toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

import site from '../../content/site.json';
export type Site = typeof site;
export function getSite(): Site {
  return site;
}
