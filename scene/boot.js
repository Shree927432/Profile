// The room's entry point. See docs/02-architecture.md, "The hook between layers 2 and 3".
//
// Phase 1: does nothing on purpose. The static page is the whole site.
//
// Phase 3 will fill in, in this order:
//   1. prefers-reduced-motion?            stay static, offer a link to try anyway
//   2. no WebGL2 or a weak device?         stay static, show "try interactive"
//   3. otherwise hide #static (keep it in the DOM), show #room, import desktop.js
export {};
