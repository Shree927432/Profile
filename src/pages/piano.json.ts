// Emits /piano.json at build time: the pieces the room's piano plays (content/piano.json, scene/objects/piano.js).
// Its own file, fetched on the first play, so the room's first load does not carry the notes.
import type { APIRoute } from 'astro';
import piano from '../../content/piano.json';

export const GET: APIRoute = () =>
  new Response(JSON.stringify(piano), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
