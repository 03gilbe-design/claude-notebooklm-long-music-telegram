# GIF generation rules (for AI agents)

Read this BEFORE creating or editing any GIF script in `mass_production/`.

## Hard rules (enforced by `docs/audit_assets.py` — run it after every edit)

1. **Assets**: every `<img>` must use `file:///C:/podcastlab/docs/assets/<name>` — never inline base64, never remote http(s) URLs (they fail silently in html2image; 404 pages get baked in as icons).
2. **One icon per concept**, same file everywhere:
   - NotebookLM → `notebooklm_iconmark.svg` (icon only, NO text/wordmark)
   - Claude → `claude_icon.svg` (official, fill #D97757)
   - Telegram → `telegram_icon.svg`
   - Podcast episode/audio track → `waveform_icon.png`
   - Music/jingle → `music_icon.png`
   - Podcast mic (alternative) → `podcast_icon.png`
3. Never invent/draw approximate logos. Official asset or a deliberate clean glyph added to `assets/`.

## Animation rules

4. **Cause → effect**: nothing appears or disappears from nowhere. Anticipation → impact → reaction. An element is born because something hits/creates it, and dies only when absorbed/arrived.
5. **State persists across phases**: when phase N ends with an element at position P, phase N+1 must start it at P. Set phase-start positions explicitly from the previous phase's end values — never rely on loop defaults.
6. **Gradual fusion**: merges use eased shrink (e.g. quadratic), not linear snap.
7. Never mutate `html_template` inside the frame loop (`.replace` on the template corrupts all later frames). Format/replace on the per-frame `html` copy.

## Output rules

8. Optimize with `gifsicle -O3` ONLY. Never `--colors N` or `--lossy` (visible quality loss, user-rejected).
9. **Verify visually before declaring done**: extract frames at phase boundaries with PIL, look at them. Silence of the script is not success.

## Reuse, don't reinvent

- Easing: `pytweening` (installed) — never hand-roll easing math.
- Phase/state timeline: `mass_production/anim_core.py` (Timeline/spawn/absorb — rules 4-7 enforced by construction; run `python anim_core.py` for its self-check).
- Pro upgrade path (future): author animation as an anime.js/GSAP timeline in the HTML, drive it frame-by-frame with Playwright `page.screenshot()` + timeline `seek()` — industry-grade motion for free.

## Checklist for a new GIF

- [ ] All `<img>` point to `docs/assets/` local files
- [ ] `python docs/audit_assets.py` → OK
- [ ] Every appear/disappear has a visible cause
- [ ] Phase boundary positions continuous
- [ ] `gifsicle -O3 -i in.gif -o out.gif` (no color reduction)
- [ ] Frames extracted and visually checked at each phase boundary
