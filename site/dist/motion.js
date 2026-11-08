/* IRODA live case file. Every frame is a pure function of the timeline time t,
   so the animation can be scrubbed and always looks the same at a given second.
   Add ?debug=1 to the page address for a scrubber. */
(() => {
  const root = document.documentElement;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const clamp = (v) => Math.min(1, Math.max(0, v));
  const smooth = (p) => p * p * (3 - 2 * p);

  // Piecewise value from [time, value, time, value, ...], held at both ends.
  const sample = (keys, t) => {
    if (t <= keys[0]) return keys[1];
    for (let i = 2; i < keys.length; i += 2) {
      if (t <= keys[i]) {
        const p = (t - keys[i - 2]) / (keys[i] - keys[i - 2]);
        return keys[i - 1] + (keys[i + 1] - keys[i - 1]) * smooth(clamp(p));
      }
    }
    return keys[keys.length - 1];
  };

  const panel = document.querySelector("[data-run]");
  const ledger = panel && panel.closest(".ledger");

  if (panel && ledger) {
    const END = 14.6;
    const RESET = 8.4;
    const tracks = [];
    const track = (el, apply, keys) => tracks.push({ el, apply, keys });

    const opacity = (el, v) => { el.style.opacity = v; };
    const scaleX = (el, v) => { el.style.transform = `scaleX(${v})`; };
    const stroke = (el, v) => { el.style.strokeDashoffset = 1 - v; };
    const bad = (el, v) => { el.classList.toggle("is-bad", v > 0.5); };
    const typed = (el, v) => {
      const chars = el.textContent.length;
      el.style.clipPath = `inset(0 ${100 - (100 * Math.floor(v * chars)) / chars}% 0 0)`;
    };

    // Stage captions change one at a time.
    const STAGES = [0, 1.5, 4.3, RESET, 9.4, 11.9, 14.2];
    panel.querySelectorAll(".run-stage span").forEach((el, i) => {
      const from = STAGES[i];
      const to = STAGES[i + 1];
      const keys = i === 0 ? [0, 1] : [from, 0, from + 0.15, 1];
      if (to !== undefined) keys.push(to - 0.15, 1, to, 0);
      track(el, opacity, keys);
    });

    // Tool calls: run 1 makes three, run 2 adds the unrequested fourth.
    const CALLS = [[1.6, 9.5], [2.4, 10], [3.2, 10.5], [null, 11]];
    panel.querySelectorAll(".run-row").forEach((row, i) => {
      const rule = row.querySelector(".run-rule");
      track(rule, scaleX, [0.2 + i * 0.12, 0, 0.7 + i * 0.12, 1, RESET, 1, RESET + 0.25, 0, 8.7 + i * 0.1, 0, 9.15 + i * 0.1, 1]);
      const [first, second] = CALLS[i];
      const tool = row.querySelector(".run-tool");
      const val = row.querySelector(".run-val");
      const toolKeys = [];
      const valKeys = [];
      if (first !== null) {
        toolKeys.push(first, 0, first + 0.5, 1, RESET, 1, RESET + 0.25, 0);
        valKeys.push(first + 0.5, 0, first + 0.65, 1, RESET, 1, RESET + 0.25, 0);
      }
      toolKeys.push(second, 0, second + 0.4, 1);
      valKeys.push(second + 0.4, 0, second + 0.55, 1);
      track(tool, typed, toolKeys);
      track(val, opacity, valKeys);
    });

    // The grader checks each row. In run 2 the last check stalls, then fails.
    const FIRST = [4.4, 5, 5.6];
    const SECOND = [11.9, 12.3, 12.7];
    const STALL_END = SECOND[2] + 0.85;
    ledger.querySelectorAll(".checks li").forEach((li, i) => {
      const a = FIRST[i];
      const b = SECOND[i];
      const last = i === 2;
      const rule = li.querySelector(".check-rule");
      const after = last
        ? [b, 0, b + 0.4, 0.55, STALL_END, 0.55, STALL_END + 0.15, 1]
        : [b, 0, b + 0.35, 1];
      track(rule, scaleX, [a, 0, a + 0.45, 1, RESET, 1, RESET + 0.25, 0, ...after]);
      const endOfCheck = last ? STALL_END : b + 0.25;
      track(li.querySelector(".step-n"), opacity, [a + 0.35, 1, a + 0.45, 0, RESET, 0, RESET + 0.25, 1, endOfCheck, 1, endOfCheck + 0.1, 0]);
      const ok = li.querySelector(".tick-ok");
      ok.style.visibility = "visible";
      track(ok.querySelector("path"), stroke, last
        ? [a + 0.35, 0, a + 0.6, 1, RESET, 1, RESET + 0.25, 0]
        : [a + 0.35, 0, a + 0.6, 1, RESET, 1, RESET + 0.25, 0, b + 0.25, 0, b + 0.5, 1]);
      if (last) {
        track(li.querySelector(".tick-bad path"), stroke, [STALL_END, 0, STALL_END + 0.25, 1]);
        track(rule, bad, [STALL_END, 0, STALL_END + 0.01, 1]);
        track(panel.querySelector(".is-flagged .run-rule"), bad, [STALL_END, 0, STALL_END + 0.01, 1]);
      }
    });

    // Outcomes stay on screen, so the end state tells the whole story.
    const [correct, incorrect] = ledger.querySelectorAll(".run-results .badge");
    track(correct, opacity, [6.3, 0, 6.6, 1]);
    track(incorrect, (el, v) => {
      el.style.opacity = v;
      el.style.transform = `scale(${1.08 - 0.08 * v})`;
    }, [14, 0, 14.25, 1]);

    const render = (t) => {
      for (const { el, apply, keys } of tracks) apply(el, sample(keys, t));
    };

    const button = panel.querySelector(".run-control");
    let t = 0;
    let frame = 0;
    let last = 0;
    let state = "idle"; // idle, playing, paused, ended

    const label = () => {
      const name = { playing: "pause", paused: "resume", ended: "replay" }[state] || "play";
      button.textContent = button.dataset[reduced && state === "ended" ? "play" : name];
    };

    const stopClock = () => {
      cancelAnimationFrame(frame);
      frame = 0;
    };

    const tick = (now) => {
      t += Math.min(now - last, 50) / 1000;
      last = now;
      if (t >= END) {
        t = END;
        state = "ended";
        frame = 0;
        label();
      } else {
        frame = requestAnimationFrame(tick);
      }
      render(t);
    };

    const startClock = () => {
      if (frame) return;
      last = performance.now();
      frame = requestAnimationFrame(tick);
    };

    const play = () => {
      state = "playing";
      label();
      startClock();
    };

    button.addEventListener("click", () => {
      if (state === "playing") {
        state = "paused";
        stopClock();
        label();
        return;
      }
      if (state === "ended") t = 0;
      play();
    });

    if (reduced) {
      t = END;
      state = "ended";
      render(END);
    } else {
      render(0);
      // Start only when the tool calls can be seen. Once running, keep going
      // while any of the panel is on screen, so reading the checks doesn't stall it.
      new IntersectionObserver(([entry]) => {
        if (state === "idle" && entry.isIntersecting) play();
      }, { threshold: 0.75 }).observe(panel.querySelector(".run-trace"));
      new IntersectionObserver(([entry]) => {
        if (state !== "playing") return;
        if (entry.isIntersecting) startClock();
        else stopClock();
      }).observe(ledger);
    }
    button.hidden = false;
    label();

    if (new URLSearchParams(location.search).has("debug")) {
      const scrub = document.createElement("input");
      Object.assign(scrub, { type: "range", min: 0, max: END, step: 0.05, value: t });
      scrub.setAttribute("aria-label", "Timeline");
      scrub.className = "run-scrub";
      scrub.style.width = "100%";
      scrub.addEventListener("input", () => {
        stopClock();
        state = "paused";
        t = Number(scrub.value);
        render(t);
        label();
      });
      panel.append(scrub);
    }
  }

  if (!reduced) {
    root.classList.add("motion");

    const once = (selector, onEnter) => {
      const seen = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            seen.unobserve(entry.target);
            onEnter(entry.target);
          }
        }
      }, { threshold: 0.1 });
      document.querySelectorAll(selector).forEach((el) => seen.observe(el));
    };

    once(".section", (el) => el.classList.add("drawn"));

    // Fact numbers count up once. The original text is restored at the end.
    once("[data-count]", (el) => {
      const original = el.textContent;
      const target = Number(el.dataset.count);
      const separator = (original.match(/\d(\D)\d/) || [])[1] || "";
      const suffix = original.match(/\D*$/)[0];
      const write = (n) => {
        const text = n >= 1000
          ? `${Math.floor(n / 1000)}${separator}${String(n % 1000).padStart(3, "0")}`
          : String(n);
        el.textContent = `${text}${suffix}`;
      };
      const DURATION = 0.9;
      let elapsed = 0;
      let previous = performance.now();
      write(0);
      const step = (now) => {
        elapsed += Math.min(now - previous, 50) / 1000;
        previous = now;
        const p = clamp(elapsed / DURATION);
        if (p < 1) {
          write(Math.floor(smooth(p) * target));
          requestAnimationFrame(step);
        } else {
          el.textContent = original;
        }
      };
      requestAnimationFrame(step);
    });
  }

  root.classList.add("ready");
})();
