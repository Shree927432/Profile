// Emits /content.json at build time (dist/content.json) with everything the
// room needs in one request. Served in dev at the same path.
import type { APIRoute } from 'astro';
import { getProjects, getPosts, getAbout, getLinks, getSite, isoDate } from '../lib/content';

export const GET: APIRoute = async () => {
  const [projects, posts, about] = await Promise.all([getProjects(), getPosts(), getAbout()]);
  const body = {
    generatedAt: new Date().toISOString(),
    site: getSite(),
    links: getLinks(),
    about: about?.body ?? '',
    projects: projects.map((p) => ({
      slug: p.id,
      url: `/projects/${p.id}`,
      ...p.data,
      body: p.body ?? '',
    })),
    posts: posts.map((p) => ({
      slug: p.id,
      url: `/posts/${p.id}`,
      ...p.data,
      date: isoDate(p.data.date),
      body: p.body ?? '',
    })),
  };
  return new Response(JSON.stringify(body, null, 2), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
};
