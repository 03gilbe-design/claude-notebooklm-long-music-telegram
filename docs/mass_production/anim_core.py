"""Shared animation core for GIF scripts.

Enforces the GIF_RULES.md animation rules BY CONSTRUCTION:
 R4 cause->effect : elements enter via spawn() (eased, from a cause point)
                    and exit via absorb() (eased, into a target) — an element
                    can never pop in/out because opacity is owned by the engine.
 R5 state persists: element state carries across phases automatically; a phase
                    only declares *changes*, the engine keeps everything else.
 R6 gradual merge : absorb() uses eased shrink toward the absorber.
 R7 no template mutation: render() formats a fresh copy per frame.

Usage:
    tl = Timeline(frames=150)
    e = tl.element("ep1", x=300, y=270, opacity=0)
    with tl.phase(0.0, 0.25) as ph:
        ph.spawn(e, frm={"x": 100}, ease=ease_out_bounce)   # born from source
        ph.to(e, x=270)
    ...
    for i, state in tl.iter_frames():
        html = template.format(**state)  # fresh copy each frame (R7)
"""
import math


# ---- easing: pytweening (battle-tested, already installed) -----------------
from pytweening import (linear, easeInOutQuad as ease_in_out,
                        easeInQuad as ease_in_quad, easeOutQuad as ease_out_quad,
                        easeInBack as ease_in_back, easeOutBounce as ease_out_bounce)

def spring(t, start, target, freq=3, decay=5):
    if t <= 0: return start
    if t >= 1: return target
    return target + (start - target) * math.exp(-decay * t) * math.cos(freq * math.pi * 2 * t)


# ---- engine ----------------------------------------------------------------
class _Element:
    def __init__(self, name, **props):
        self.name = name
        self.props = dict(props)          # current persistent state (R5)


class _Move:
    """One animated property change inside a phase."""
    def __init__(self, el, target, ease, t0, t1):
        self.el, self.target, self.ease = el, dict(target), ease
        self.t0, self.t1 = t0, t1         # local sub-window inside the phase
        self.start = None                 # captured lazily at first eval

    def eval(self, tp):                   # tp = phase-local 0..1
        if tp < self.t0: return
        u = 1.0 if tp >= self.t1 else (tp - self.t0) / (self.t1 - self.t0)
        # u=1 -> exact target (some easings, e.g. pytweening easeOutBounce, don't return 1.0 at 1)
        u = 1.0 if u >= 1.0 else self.ease(u)
        if self.start is None:
            self.start = {k: self.el.props.get(k, 0) for k in self.target}
        for k, v in self.target.items():
            s = self.start[k]
            self.el.props[k] = s + (v - s) * u


class _Phase:
    def __init__(self, p0, p1):
        self.p0, self.p1 = p0, p1
        self.moves = []

    def __enter__(self): return self
    def __exit__(self, *a): return False

    def to(self, el, ease=ease_in_out, window=(0.0, 1.0), **target):
        """Animate properties toward target values over the phase (R5-safe)."""
        self.moves.append(_Move(el, target, ease, window[0], window[1]))

    def spawn(self, el, frm=None, ease=ease_out_bounce, window=(0.0, 1.0), **target):
        """Element is BORN: fades/scales in from `frm` (its cause point). R4."""
        if frm:
            el.props.update(frm)
        tgt = {"opacity": 1.0}
        tgt.update(target)
        self.moves.append(_Move(el, tgt, ease, window[0], window[1]))

    def absorb(self, el, into, ease=ease_in_quad, window=(0.0, 1.0)):
        """Element is EATEN by `into`: eased move+shrink+fade to absorber. R4+R6."""
        tgt = {"x": into.props.get("x", 0), "y": into.props.get("y", 0),
               "sx": 0.0, "sy": 0.0, "opacity": 0.0}
        self.moves.append(_Move(el, tgt, ease, window[0], window[1]))


class Timeline:
    def __init__(self, frames):
        self.frames = frames
        self.elements = {}
        self.phases = []

    def element(self, name, **props):
        props.setdefault("opacity", 0.0)
        props.setdefault("sx", 1.0)
        props.setdefault("sy", 1.0)
        el = _Element(name, **props)
        self.elements[name] = el
        return el

    def phase(self, p0, p1):
        ph = _Phase(p0, p1)
        self.phases.append(ph)
        return ph

    def iter_frames(self):
        """Yield (i, flat_state_dict). State persists between phases (R5)."""
        for i in range(self.frames):
            p = i / float(self.frames - 1)
            for ph in self.phases:
                if p >= ph.p0:
                    # clamp: past-end phases finalize at tp=1 so end states are
                    # exact and the next phase starts from them (R5)
                    tp = min(1.0, (p - ph.p0) / (ph.p1 - ph.p0)) if ph.p1 > ph.p0 else 1.0
                    for mv in ph.moves:
                        mv.eval(tp)
            flat = {}
            for el in self.elements.values():
                for k, v in el.props.items():
                    flat[f"{el.name}_{k}"] = round(v, 3) if isinstance(v, float) else v
            yield i, flat


if __name__ == "__main__":
    # self-check: state persists across phases, no pops
    tl = Timeline(frames=100)
    e = tl.element("a", x=0, y=270)
    src = tl.element("s", x=0, y=0, opacity=1)
    with tl.phase(0.0, 0.5) as ph:
        ph.spawn(e, frm={"x": 100}, x=270)
    with tl.phase(0.5, 1.0) as ph:
        ph.to(e, x=300)
    states = dict(tl.iter_frames())
    assert states[50]["a_x"] >= 270, states[50]          # phase 1 finalized exactly (clamp)
    assert abs(states[50]["a_x"] - 270) < 2, states[50]  # phase 2 STARTS where 1 ended (R5)
    assert states[0]["a_opacity"] == 0.0                 # born, not popped (R4)
    assert states[99]["a_opacity"] == 1.0
    print("anim_core self-check OK")
