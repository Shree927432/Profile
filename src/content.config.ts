import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// All collections read from ../content/ (the only source of truth).
// Field shapes mirror content/README.md.

const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/projects' }),
  schema: z.object({
    title: z.string(),
    year: z.number(),
    summary: z.string().max(140),
    tags: z.array(z.string()).default([]),
    links: z
      .object({
        live: z.string().default(''),
        source: z.string().default(''),
      })
      .default({ live: '', source: '' }),
    cover: z.string().default(''),
    featured: z.boolean().default(false),
    order: z.number().default(99),
  }),
});

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/posts' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    summary: z.string(),
    tags: z.array(z.string()).default([]),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: 'about.md', base: './content' }),
  schema: z.object({}).passthrough(),
});

export const collections = { projects, posts, pages };
