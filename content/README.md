# Content

The only place words live. Both the static site and the room read from here.

## projects/<slug>.md

    ---
    title: Project name
    year: 2025
    summary: One sentence, under 140 characters.
    tags: [web, 3d]
    links:
      live: https://
      source: https://
    cover: /images/projects/<slug>.jpg
    featured: true
    order: 1
    ---
    Body in markdown. What it is, what you did, what you learned. Short.

## posts/<slug>.md

    ---
    title: Post title
    date: 2026-10-16
    summary: One sentence.
    tags: [notes]
    ---
    Body.

## about.md

Plain markdown. Who you are, what you do, what you are into. First person.

## links.json

    {
      "email": "",
      "github": "",
      "linkedin": "",
      "x": "",
      "resume": ""
    }

## site.json

    {
      "name": "Your name, used as the site title",
      "tagline": "One line under your name on the home page",
      "intro": "Two or three sentences for the home page",
      "description": "One sentence for search engines and link previews",
      "notFound": { "title": "", "text": "", "link": "" }
    }

`notFound` is the text of the 404 page.
