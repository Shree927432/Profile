// Screen: the desk monitor. Lists posts (newest first) on a dark navy terminal-style display.
// Keys/click/scroll select a post; Enter or clicking a row calls open(post.url).
//
// Uses only mount's arguments: no imports, globals or DOM. Times are in milliseconds.

const BG = "#13253b";
const FG = "#9fd0ff";
const FG_DIM = "#6a97c4";
const FG_BRIGHT = "#e6f3ff";
const HILITE = "#1f4068";
const FONT = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace';

const PAD = 24;
const HEADER_Y = 40;
const LIST_TOP = 64;
const ROW_H = 56;
const HINT_Y_FROM_BOTTOM = 18;
const BLINK_MS = 530;
const SCROLL_STEP = 40; // scroll units per row

export default {
  id: "monitor-posts",
  mount({ canvas, ctx, width, height, content, open, reduce, say }) {
    const posts = (content && content.posts) || [];
    const text = (content && content.site && content.site.screens && content.site.screens.posts) || {};
    const listBottom = height - 44;
    const rows = Math.max(1, Math.floor((listBottom - LIST_TOP) / ROW_H));

    let sel = 0;
    let top = 0;
    let scrollAcc = 0;
    let cursorOn = true;
    let dirty = true;
    let stopped = false;

    const fit = (s, maxW) => {
      s = String(s == null ? "" : s);
      if (ctx.measureText(s).width <= maxW) return s;
      let lo = 0, hi = s.length;
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (ctx.measureText(s.slice(0, mid) + "…").width <= maxW) lo = mid; else hi = mid - 1;
      }
      return s.slice(0, lo).trimEnd() + "…";
    };

    const announce = () => {
      const p = posts[sel];
      if (p && say) say(p.title + (p.date ? ", " + p.date : ""));
    };

    const clamp = () => {
      sel = Math.max(0, Math.min(posts.length - 1, sel));
      if (sel < top) top = sel;
      if (sel >= top + rows) top = sel - rows + 1;
      top = Math.max(0, Math.min(Math.max(0, posts.length - rows), top));
    };

    const draw = () => {
      ctx.save();
      ctx.fillStyle = BG;
      ctx.fillRect(0, 0, width, height);
      ctx.textBaseline = "alphabetic";

      ctx.font = `bold 20px ${FONT}`;
      ctx.fillStyle = FG_BRIGHT;
      const title = text.title || "";
      ctx.fillText(fit(title, width - PAD * 2 - 20), PAD, HEADER_Y);
      if (cursorOn) {
        const w = ctx.measureText(title + " ").width;
        ctx.fillStyle = FG;
        ctx.fillRect(PAD + w, HEADER_Y - 16, 11, 19);
      }
      ctx.fillStyle = FG_DIM;
      ctx.fillRect(PAD, HEADER_Y + 10, width - PAD * 2, 1);

      if (posts.length === 0) {
        ctx.font = `16px ${FONT}`;
        ctx.fillStyle = FG_DIM;
        ctx.fillText(fit(text.empty || "", width - PAD * 2), PAD, LIST_TOP + 28);
      }

      const textW = width - PAD * 2 - 16;
      for (let i = 0; i < rows && top + i < posts.length; i++) {
        const p = posts[top + i];
        const y = LIST_TOP + i * ROW_H;
        const on = top + i === sel;
        if (on) {
          ctx.fillStyle = HILITE;
          ctx.fillRect(PAD - 10, y, width - PAD * 2 + 20 - 8, ROW_H - 6);
        }
        ctx.font = `bold 17px ${FONT}`;
        ctx.fillStyle = on ? FG_BRIGHT : FG;
        ctx.fillText(fit((on ? "> " : "  ") + (p.title || ""), textW), PAD, y + 22);
        ctx.font = `13px ${FONT}`;
        ctx.fillStyle = on ? FG : FG_DIM;
        const meta = [p.date, p.summary].filter(Boolean).join("  ");
        ctx.fillText(fit("  " + meta, textW), PAD, y + 42);
      }

      // scroll bar, only when the list is longer than the screen
      if (posts.length > rows) {
        const trackH = rows * ROW_H - 6;
        const thumbH = Math.max(16, (trackH * rows) / posts.length);
        const thumbY = LIST_TOP + ((trackH - thumbH) * top) / (posts.length - rows);
        ctx.fillStyle = HILITE;
        ctx.fillRect(width - 14, LIST_TOP, 4, trackH);
        ctx.fillStyle = FG;
        ctx.fillRect(width - 14, thumbY, 4, thumbH);
      }

      ctx.font = `13px ${FONT}`;
      ctx.fillStyle = FG_DIM;
      ctx.fillText(fit(text.hint || "", width - PAD * 2), PAD, height - HINT_Y_FROM_BOTTOM);
      ctx.restore();
    };

    const openSel = () => {
      const p = posts[sel];
      if (p && p.url) open(p.url);
    };

    const move = (to) => {
      if (posts.length === 0) return true;
      const before = sel;
      sel = to;
      clamp();
      if (sel !== before) { announce(); dirty = true; }
      return true;
    };

    return {
      frame(t) {
        if (stopped) return false;
        if (!reduce) {
          const on = Math.floor(t / BLINK_MS) % 2 === 0;
          if (on !== cursorOn) { cursorOn = on; dirty = true; }
        }
        if (!dirty) return false;
        dirty = false;
        draw();
        return true;
      },

      input(ev) {
        if (stopped || !ev) return false;
        if (ev.type === "open") { openSel(); return posts.length > 0; }
        if (ev.type === "key") {
          switch (ev.key) {
            case "ArrowDown": case "j": return move(sel + 1);
            case "ArrowUp": case "k": return move(sel - 1);
            case "PageDown": return move(sel + rows);
            case "PageUp": return move(sel - rows);
            case "Home": return move(0);
            case "End": return move(posts.length - 1);
            case "Enter": openSel(); return posts.length > 0;
          }
          return false;
        }
        if (ev.type === "click") {
          const i = Math.floor((ev.y - LIST_TOP) / ROW_H);
          if (ev.y < LIST_TOP || i < 0 || i >= rows || top + i >= posts.length) return false;
          sel = top + i;
          dirty = true;
          openSel();
          return true;
        }
        if (ev.type === "scroll") {
          if (posts.length <= rows) return false;
          const maxTop = posts.length - rows;
          const atEdge = (ev.dy < 0 && top === 0) || (ev.dy > 0 && top === maxTop);
          if (atEdge) { scrollAcc = 0; return false; } // let the page scroll on
          scrollAcc += ev.dy;
          const steps = Math.trunc(scrollAcc / SCROLL_STEP);
          if (steps !== 0) {
            scrollAcc -= steps * SCROLL_STEP;
            top = Math.max(0, Math.min(maxTop, top + steps));
            if (sel < top) sel = top;
            if (sel >= top + rows) sel = top + rows - 1;
            dirty = true;
          }
          return true;
        }
        return false;
      },

      stop() { stopped = true; },
    };
  },
};
