/* Dependency-free SVG charts for the ELT dashboard.
   Each element with data-chart="<name>" is rendered from window.TELEMETRY.
   Colours come from CSS variables, so themes need no JS changes. */
(() => {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const T = window.TELEMETRY || {};

  const STATUS_COLOR = {
    SUCCESS: "var(--ok)", FAILED: "var(--bad)", RUNNING: "var(--run)",
    INCOMPLETE: "var(--idle)", UNKNOWN: "var(--idle)", WARNING: "var(--warn)",
  };
  const STAGE_COLORS = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)"];

  const pl = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
  const esc = (v) => String(v).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function svg(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] != null) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function html(tag, cls, parent, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  }
  function fmtDur(s) {
    if (s == null) return "N/A";
    if (s === 0) return "0";
    if (s < 1) return Math.round(s * 1000) + " ms";
    if (s < 60) return (s < 10 ? s.toFixed(1) : Math.round(s)) + " s";
    const m = Math.floor(s / 60), r = Math.round(s % 60);
    if (m < 60) return m + "m " + String(r).padStart(2, "0") + "s";
    return Math.floor(m / 60) + "h " + String(m % 60).padStart(2, "0") + "m";
  }
  /* "Nice" axis ticks for 0..max. */
  function niceScale(max, count, integer) {
    if (!(max > 0)) return { max: 1, ticks: [0, 1] };
    const raw = max / count, pow = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = (integer ? [1, 2, 5, 10] : [1, 2, 2.5, 5, 10]).map((m) => m * pow).find((s) => s >= raw);
    const top = Math.ceil(max / step) * step, ticks = [];
    for (let v = 0; v <= top + 1e-9; v += step) ticks.push(+v.toFixed(6));
    return { max: top, ticks };
  }
  function makeSvg(box, W, H, label) {
    return svg("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": label }, box);
  }
  function empty(box, text) { html("div", "empty", box, text); }
  function legend(box, items) {
    const l = html("div", "legend", box);
    items.forEach((it) => {
      const s = html("span", "", l);
      html("i", "", s).style.background = it.color;
      s.appendChild(document.createTextNode(it.name));
    });
  }

  /* ---------- tooltip ---------- */
  const tip = html("div", "tooltip", document.body);
  tip.setAttribute("role", "tooltip");
  document.addEventListener("mouseover", (e) => {
    const t = e.target.closest && e.target.closest("[data-tip]");
    if (!t) return;
    tip.innerHTML = t.getAttribute("data-tip");
    tip.classList.add("on");
  });
  document.addEventListener("mousemove", (e) => {
    if (!tip.classList.contains("on")) return;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = e.clientX + 14, y = e.clientY + 14;
    if (x + w > innerWidth - 8) x = e.clientX - w - 14;
    if (y + h > innerHeight - 8) y = e.clientY - h - 14;
    tip.style.left = x + "px"; tip.style.top = y + "px";
  });
  document.addEventListener("mouseout", (e) => {
    if (e.target.closest && e.target.closest("[data-tip]")) tip.classList.remove("on");
  });

  /* ---------- column chart (runs, stage trend, event volume) ---------- */
  function columnChart(box, o) {
    const n = o.columns.length;
    if (!n) return empty(box, o.empty || "No data yet.");
    const W = Math.max(box.clientWidth, 260), H = o.height || 210;
    const m = { l: 46, r: 8, t: 10, b: 34 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const maxVal = Math.max(...o.columns.map((c) => c.segments.reduce((a, s) => a + (s.value || 0), 0)), o.refValue || 0);
    const sc = niceScale(maxVal, 4, o.integer);
    const root = makeSvg(box, W, H, o.aria);
    const y = (v) => m.t + ih - (v / sc.max) * ih;
    sc.ticks.forEach((v) => {
      svg("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: v === 0 ? "axis" : "grid-line" }, root);
      svg("text", { x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }, root).textContent = o.yFmt(v);
    });
    const slot = iw / n, bw = Math.min(Math.max(slot * 0.62, 3), 44);
    const every = Math.ceil(n / Math.max(1, Math.floor(iw / (o.labelWidth || 64))));
    o.columns.forEach((c, i) => {
      const cx = m.l + slot * i + slot / 2;
      let acc = 0;
      const g = svg("g", { "data-tip": c.tip }, root);
      svg("rect", { x: cx - slot / 2, y: m.t, width: slot, height: ih, fill: "transparent" }, g);
      c.segments.forEach((s) => {
        if (!s.value) return;
        const y0 = y(acc + s.value), h = Math.max(y(acc) - y0, 1);
        svg("rect", { x: cx - bw / 2, y: y0, width: bw, height: h, rx: 2, style: `fill:${s.color}` }, g);
        acc += s.value;
      });
      if (c.marker) svg("text", { x: cx, y: y(0) - 5, "text-anchor": "middle", class: "lbl" }, g).textContent = c.marker;
      if (i % every === 0 || i === n - 1) {
        const parts = c.label.split("|");
        parts.forEach((p, k) =>
          (svg("text", { x: cx, y: H - m.b + 15 + k * 12, "text-anchor": "middle", class: k ? "" : "lbl" }, root).textContent = p));
      }
    });
    if (o.refValue != null) {
      svg("line", { x1: m.l, x2: W - m.r, y1: y(o.refValue), y2: y(o.refValue), class: "ref" }, root);
      svg("text", { x: W - m.r, y: y(o.refValue) - 4, "text-anchor": "end" }, root).textContent = o.refLabel;
    }
    if (o.legend) legend(box, o.legend);
  }

  /* ---------- horizontal bars ---------- */
  function hBars(box, o) {
    if (!o.rows.length) return empty(box, o.empty || "No data yet.");
    const W = Math.max(box.clientWidth, 260), rowH = 28, labelW = Math.min(o.labelW || 150, W * 0.42), endW = 64;
    const H = o.rows.length * rowH + 4;
    const root = makeSvg(box, W, H, o.aria);
    const max = Math.max(...o.rows.map((r) => r.segments.reduce((a, s) => a + s.value, 0)), 1e-9);
    const iw = W - labelW - endW;
    o.rows.forEach((r, i) => {
      const yy = i * rowH + 2, g = svg("g", { "data-tip": r.tip }, root);
      svg("rect", { x: 0, y: yy, width: W, height: rowH, fill: "transparent" }, g);
      const t = svg("text", { x: 0, y: yy + rowH / 2 + 4, class: "lbl" }, g);
      const cap = Math.floor(labelW / 6.4);
      t.textContent = r.label.length > cap ? r.label.slice(0, cap - 1) + "…" : r.label;
      svg("rect", { x: labelW, y: yy + 7, width: iw, height: 14, rx: 3, style: "fill:var(--surface-2)" }, g);
      let acc = 0;
      r.segments.forEach((s) => {
        if (!s.value) return;
        const w = Math.max((s.value / max) * iw, 2);
        svg("rect", { x: labelW + (acc / max) * iw, y: yy + 7, width: w, height: 14, rx: 3, style: `fill:${s.color}` }, g);
        acc += s.value;
      });
      svg("text", { x: W, y: yy + rowH / 2 + 4, "text-anchor": "end", class: "strong" }, g).textContent = r.end;
    });
    if (o.legend) legend(box, o.legend);
  }

  /* ---------- donut ---------- */
  function donut(box, o) {
    const total = o.items.reduce((a, i) => a + i.value, 0);
    if (!total) return empty(box, o.empty || "No data yet.");
    const wrap = html("div", "", box);
    wrap.style.cssText = "display:flex;align-items:center;gap:22px;flex-wrap:wrap";
    const S = 150, r = 60, sw = 16, C = 2 * Math.PI * r;
    const root = makeSvg(wrap, S, S, o.aria);
    root.style.cssText = "width:" + S + "px;flex:none";
    svg("circle", { cx: S / 2, cy: S / 2, r, fill: "none", style: "stroke:var(--surface-2)", "stroke-width": sw }, root);
    const live = o.items.filter((i) => i.value > 0);
    const gap = live.length > 1 ? 2 : 0;
    let acc = 0;
    live.forEach((it) => {
      const len = (it.value / total) * C;
      svg("circle", {
        cx: S / 2, cy: S / 2, r, fill: "none", "stroke-width": sw, style: `stroke:${it.color}`,
        "stroke-dasharray": `${Math.max(len - gap, 0.5)} ${C}`, "stroke-dashoffset": -acc,
        transform: `rotate(-90 ${S / 2} ${S / 2})`, "data-tip": it.tip,
      }, root);
      acc += len;
    });
    svg("text", { x: S / 2, y: S / 2 + 3, "text-anchor": "middle", class: "strong", style: "font-size:22px" }, root).textContent = o.center;
    svg("text", { x: S / 2, y: S / 2 + 21, "text-anchor": "middle" }, root).textContent = o.centerSub;
    const l = html("div", "legend", wrap);
    l.style.cssText = "flex-direction:column;gap:7px;margin:0";
    o.items.forEach((it) => {
      const s = html("span", "", l);
      html("i", "", s).style.background = it.color;
      s.appendChild(document.createTextNode(`${it.label}  `));
      html("b", "", s, String(it.value)).style.cssText = "color:var(--ink);font-weight:600";
    });
  }

  /* ---------- gantt for the latest run ---------- */
  function gantt(box) {
    const g = T.gantt;
    if (!g) return empty(box, "No pipeline run has been recorded yet. Start the pipeline to see stage timing here.");
    const W = Math.max(box.clientWidth, 340), rowH = 36, top = 4, axisH = 26;
    const labelW = Math.min(180, W * 0.3), endPad = 78;
    const H = top + g.stages.length * rowH + axisH;
    const iw = W - labelW - endPad;
    const root = makeSvg(box, W, H, "Latest run timeline, one bar per stage");
    const x = (s) => labelW + (Math.min(s, g.total_s) / g.total_s) * iw;
    const ticks = iw < 330 ? 3 : 5;
    for (let i = 0; i <= ticks; i++) {
      const s = (g.total_s * i) / ticks, xx = x(s);
      svg("line", { x1: xx, x2: xx, y1: top, y2: H - axisH, class: "grid-line" }, root);
      svg("text", { x: xx, y: H - 8, "text-anchor": i === 0 ? "start" : i === ticks ? "end" : "middle" }, root).textContent = i === 0 ? "0" : fmtDur(s);
    }
    g.stages.forEach((s, i) => {
      const yy = top + i * rowH, mid = yy + rowH / 2;
      svg("text", { x: 0, y: mid + 4, class: "lbl" }, root).textContent = s.label;
      if (s.offset_s == null) {
        svg("text", { x: labelW + 4, y: mid + 4 }, root).textContent = "No log events for this stage in the run";
        return;
      }
      const dur = s.duration_s || 0, bx = x(s.offset_s), bw = Math.max(x(s.offset_s + dur) - bx, 4);
      const grp = svg("g", {
        "data-tip": `<b>${esc(s.label)}</b><br>${esc(s.status.toLowerCase())}<br>Started +${esc(fmtDur(s.offset_s))}` +
          `<br>Duration ${esc(s.duration_label)}${s.exact ? "" : " (from timestamps)"}` +
          `<br>${pl(s.events, "event")}, ${pl(s.warnings, "warning")}, ${pl(s.errors, "error")}`,
      }, root);
      svg("rect", { x: labelW, y: yy + 4, width: iw, height: rowH - 8, fill: "transparent" }, grp);
      svg("rect", { x: bx, y: mid - 8, width: bw, height: 16, rx: 3, style: `fill:${STATUS_COLOR[s.status] || STATUS_COLOR.UNKNOWN}` }, grp);
      const inside = bw > 54;
      svg("text", {
        x: inside ? bx + bw - 6 : bx + bw + 6, y: mid + 4,
        "text-anchor": inside ? "end" : "start", class: inside ? "" : "lbl",
        style: inside ? "fill:var(--surface);font-weight:600" : null,
      }, grp).textContent = s.duration_label;
    });
  }


  /* ---------- line chart (one line per series) ---------- */
  function lineChart(box, o) {
    const n = o.labels.length;
    if (n < 2) return empty(box, o.empty || "Needs at least two runs to draw a trend.");
    const W = Math.max(box.clientWidth, 260), H = 210, m = { l: 46, r: 12, t: 10, b: 34 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const sc = niceScale(Math.max(...o.series.flatMap((s) => s.values.filter((v) => v != null)), 0), 4);
    const root = makeSvg(box, W, H, o.aria);
    const x = (i) => m.l + (i / (n - 1)) * iw, y = (v) => m.t + ih - (v / sc.max) * ih;
    sc.ticks.forEach((v) => {
      svg("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: v === 0 ? "axis" : "grid-line" }, root);
      svg("text", { x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }, root).textContent = o.yFmt(v);
    });
    const every = Math.ceil(n / Math.max(1, Math.floor(iw / 64)));
    o.labels.forEach((l, i) => {
      if (i % every && i !== n - 1) return;
      l.split("|").forEach((p, k) => (svg("text", { x: x(i), y: H - m.b + 15 + k * 12, "text-anchor": "middle", class: k ? "" : "lbl" }, root).textContent = p));
    });
    o.series.forEach((s) => {
      const pts = s.values.map((v, i) => (v == null ? null : [x(i), y(v)]));
      let d = "", pen = false;
      pts.forEach((pt) => {
        if (!pt) { pen = false; return; }
        d += (pen ? "L" : "M") + pt[0].toFixed(1) + " " + pt[1].toFixed(1);
        pen = true;
      });
      svg("path", { d, fill: "none", "stroke-width": 1.75, "stroke-linejoin": "round", style: `stroke:${s.color}` }, root);
    });
    o.labels.forEach((l, i) => {
      const g = svg("g", { "data-tip": o.tip(i) }, root);
      svg("rect", { x: x(i) - iw / n / 2, y: m.t, width: iw / n, height: ih, fill: "transparent" }, g);
      o.series.forEach((s) => s.values[i] != null && svg("circle", { cx: x(i), cy: y(s.values[i]), r: 2.5, style: `fill:${s.color}` }, g));
    });
    legend(box, o.series.map((s) => ({ name: s.name, color: s.color })));
  }

  /* ---------- min / median / max range per stage ---------- */
  function stageRange(box) {
    const st = (T.stage_stats || []).filter((s) => s.n > 0);
    if (!st.length) return empty(box, "No successful stage runs yet.");
    const W = Math.max(box.clientWidth, 280), rowH = 34, labelW = Math.min(170, W * 0.36), endW = 60;
    const root = makeSvg(box, W, st.length * rowH + 26, "Stage duration range across successful runs");
    const sc = niceScale(Math.max(...st.map((s) => Math.max(s.max, s.latest || 0))), 4), iw = W - labelW - endW;
    const x = (v) => labelW + (v / sc.max) * iw;
    sc.ticks.forEach((v) => {
      svg("line", { x1: x(v), x2: x(v), y1: 0, y2: st.length * rowH, class: "grid-line" }, root);
      svg("text", { x: x(v), y: st.length * rowH + 16, "text-anchor": "middle" }, root).textContent = fmtDur(v);
    });
    st.forEach((s, i) => {
      const mid = i * rowH + rowH / 2;
      const g = svg("g", { "data-tip": `<b>${esc(s.label)}</b><br>Fastest ${esc(fmtDur(s.min))}<br>Median ${esc(fmtDur(s.median))}<br>Slowest ${esc(fmtDur(s.max))}<br>Latest ${esc(fmtDur(s.latest))}<br>${pl(s.n, "run")}` }, root);
      svg("rect", { x: 0, y: i * rowH, width: W, height: rowH, fill: "transparent" }, g);
      svg("text", { x: 0, y: mid + 4, class: "lbl" }, g).textContent = s.label;
      svg("rect", { x: x(s.min), y: mid - 4, width: Math.max(x(s.max) - x(s.min), 3), height: 8, rx: 4, style: "fill:var(--c5);opacity:.55" }, g);
      svg("rect", { x: x(s.median) - 1.5, y: mid - 8, width: 3, height: 16, rx: 1, style: "fill:var(--c1)" }, g);
      if (s.latest != null) svg("circle", { cx: x(s.latest), cy: mid, r: 4.5, style: "fill:var(--surface);stroke:var(--accent);stroke-width:2" }, g);
    });
    legend(box, [{ name: "Fastest to slowest", color: "var(--c5)" }, { name: "Median", color: "var(--c1)" }, { name: "Latest run (circle)", color: "var(--accent)" }]);
  }

  /* ---------- job status grid ---------- */
  function jobMatrix(box) {
    const stages = T.stages || [];
    if (!stages.length) return empty(box, "No stages configured.");
    const colors = { SUCCESS: "var(--ok)", FAILED: "var(--bad)", RUNNING: "var(--run)" };
    stages.forEach((st) => {
      const row = html("div", "", box);
      row.style.cssText = "display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid var(--line)";
      const lab = html("span", "", row, st.label); lab.style.cssText = "width:170px;flex:none;color:var(--ink-2);font-size:13px";
      const cells = html("div", "", row); cells.style.cssText = "display:flex;gap:4px;flex-wrap:wrap";
      st.jobs.forEach((j) => {
        const c = html("span", "", cells);
        c.style.cssText = `width:18px;height:18px;border-radius:3px;background:${colors[j.status] || "var(--idle-soft)"};` + (colors[j.status] ? "" : "border:1px solid var(--line-strong)");
        c.setAttribute("data-tip", `<b>${esc(j.label)}</b><br>${esc(j.status.toLowerCase())}`);
      });
    });
    legend(box, [{ name: "Completed", color: "var(--ok)" }, { name: "Failed", color: "var(--bad)" }, { name: "Running", color: "var(--run)" }, { name: "No evidence", color: "var(--idle-soft)" }]);
  }

  /* ---------- sparkline ---------- */
  function spark(box) {
    const vals = (box.dataset.values || "").split(",").map(Number).filter((v) => !isNaN(v));
    if (vals.length < 2) return;
    const W = Math.max(box.clientWidth, 80), H = 22, max = Math.max(...vals), min = Math.min(...vals);
    const root = makeSvg(box, W, H, "Trend of recent runs");
    const px = (i) => 2 + (i / (vals.length - 1)) * (W - 4);
    const py = (v) => H - 3 - ((v - min) / (max - min || 1)) * (H - 8);
    svg("polyline", {
      points: vals.map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(" "),
      fill: "none", "stroke-width": 1.5, "stroke-linejoin": "round", style: "stroke:var(--accent)",
    }, root);
    svg("circle", { cx: px(vals.length - 1), cy: py(vals[vals.length - 1]), r: 2.5, style: "fill:var(--accent)" }, root);
  }

  /* ---------- chart definitions ---------- */
  const runLabel = (r) => {
    const p = (r.full || "").split(" ");
    if (p.length < 2) return r.label;
    const d = new Date(r.full.replace(" ", "T"));
    const day = isNaN(d) ? p[0].slice(5) : d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
    return `${day}|${p[1].slice(0, 5)}`;
  };

  const CHARTS = {
    gantt,
    spark,
    runs(box) {
      const cols = (T.runs || []).map((r) => ({
        label: runLabel(r),
        segments: [{ value: r.duration || 0, color: STATUS_COLOR[r.status] || STATUS_COLOR.UNKNOWN }],
        marker: r.duration == null ? "–" : null,
        tip: `<b>${esc(r.full || "Run")}</b><br>${esc(r.status.toLowerCase())}<br>Duration ${esc(r.duration_label)}` +
          `<br>${pl(r.events, "event")}, ${pl(r.warnings, "warning")}, ${pl(r.errors, "error")}`,
      }));
      const med = T.duration_stats && T.duration_stats.median;
      columnChart(box, {
        columns: cols, yFmt: fmtDur, aria: "Duration of recent pipeline runs",
        refValue: med, refLabel: med ? "median " + fmtDur(med) : null,
        legend: [{ name: "Succeeded", color: "var(--ok)" }, { name: "Failed", color: "var(--bad)" }, { name: "Incomplete", color: "var(--idle)" }],
        empty: "No runs recorded yet.",
      });
    },
    stagetrend(box) {
      const meta = T.stage_meta || [];
      const cols = (T.stage_trend || []).map((r, i) => {
        const run = (T.runs || [])[i] || {};
        const segs = meta.map((s, k) => ({ value: (r.stages[s.key] || 0), color: STAGE_COLORS[k % 5] }));
        return {
          label: runLabel(run), segments: segs,
          tip: `<b>${esc(run.full || "Run")}</b><br>` +
            meta.map((s, k) => `${esc(s.label)}: ${esc(fmtDur(r.stages[s.key]))}`).join("<br>"),
        };
      });
      columnChart(box, {
        columns: cols, yFmt: fmtDur, aria: "Stage duration per run, stacked",
        legend: meta.map((s, k) => ({ name: s.label, color: STAGE_COLORS[k % 5] })),
        empty: "No runs recorded yet.",
      });
    },
    stagelines(box) {
      const meta = T.stage_meta || [];
      lineChart(box, {
        labels: (T.runs || []).map(runLabel), yFmt: fmtDur, aria: "Stage duration per run, one line per stage",
        series: meta.map((s, k) => ({ name: s.label, color: STAGE_COLORS[k % 5], values: (T.stage_trend || []).map((r) => r.stages[s.key] || null) })),
        tip: (i) => `<b>${esc(((T.runs || [])[i] || {}).full || "Run")}</b><br>` + meta.map((s) => `${esc(s.label)}: ${esc(fmtDur(T.stage_trend[i].stages[s.key]))}`).join("<br>"),
      });
    },
    timeshare(box) {
      const g = T.gantt;
      const items = g ? g.stages.filter((s) => s.duration_s).map((s, k) => ({
        label: s.label, value: Math.round(s.duration_s * 100) / 100, color: STAGE_COLORS[T.gantt.stages.indexOf(s) % 5],
        tip: `<b>${esc(s.label)}</b><br>${esc(s.duration_label)} (${Math.round((100 * s.duration_s) / g.stages.reduce((a, x) => a + (x.duration_s || 0), 0))}%)`,
      })) : [];
      donut(box, { aria: "Share of latest run time per stage", empty: "No stage timing yet.", items,
        center: g ? g.total_label : "", centerSub: "latest run" });
      box.querySelectorAll(".legend b").forEach((b) => (b.textContent = fmtDur(+b.textContent)));
    },
    stagerange: stageRange,
    jobmatrix: jobMatrix,
    runissues(box) {
      const runs = T.runs || [];
      if (!runs.some((r) => r.warnings || r.errors)) return empty(box, "No warnings or errors in the recent runs.");
      columnChart(box, {
        columns: runs.map((r) => ({ label: runLabel(r), segments: [{ value: r.warnings, color: "var(--warn)" }, { value: r.errors, color: "var(--bad)" }],
          tip: `<b>${esc(r.full || "Run")}</b><br>${pl(r.warnings, "warning")}<br>${pl(r.errors, "error")}` })),
        yFmt: (v) => String(v), integer: true, aria: "Warnings and errors per run",
        legend: [{ name: "Warnings", color: "var(--warn)" }, { name: "Errors", color: "var(--bad)" }],
      });
    },
    cadence(box) {
      const runs = (T.runs || []).filter((r) => r.gap_h != null);
      columnChart(box, {
        columns: runs.map((r) => ({ label: runLabel(r), segments: [{ value: r.gap_h, color: "var(--c1)" }],
          tip: `<b>${esc(r.full)}</b><br>${r.gap_h.toFixed(1)} h after the previous start` })),
        yFmt: (v) => v + " h", aria: "Hours between consecutive run starts", empty: "Needs at least two runs.",
      });
    },
    outcomes(box) {
      const o = T.outcomes || { success: 0, failed: 0, incomplete: 0 };
      const done = o.success + o.failed;
      donut(box, {
        aria: "Pipeline run outcomes", empty: "No runs recorded yet.",
        center: T.kpi.success_rate != null ? T.kpi.success_rate + "%" : "N/A",
        centerSub: done ? `${done} finished` : "no finished runs",
        items: [
          { label: "Succeeded", value: o.success, color: "var(--ok)", tip: `<b>Succeeded</b><br>${pl(o.success, "run")}` },
          { label: "Failed", value: o.failed, color: "var(--bad)", tip: `<b>Failed</b><br>${pl(o.failed, "run")}` },
          { label: "Incomplete", value: o.incomplete, color: "var(--idle)", tip: `<b>Incomplete</b><br>${pl(o.incomplete, "run")}` },
        ],
      });
    },
    events(box) {
      const b = (T.event_buckets || {}).buckets || [];
      const unit = (T.event_buckets || {}).unit;
      columnChart(box, {
        columns: b.map((x) => ({
          label: x.label,
          segments: [{ value: x.info, color: "var(--c5)" }, { value: x.warning, color: "var(--warn)" }, { value: x.error, color: "var(--bad)" }],
          tip: `<b>${esc(x.full)}</b><br>${x.info} info<br>${pl(x.warning, "warning")}<br>${pl(x.error, "error")}`,
        })),
        yFmt: (v) => String(v), integer: true, aria: "Log events per " + unit, labelWidth: 48,
        legend: [{ name: "Info", color: "var(--c5)" }, { name: "Warnings", color: "var(--warn)" }, { name: "Errors", color: "var(--bad)" }],
        empty: "No log events recorded yet.",
      });
    },
    bylogger(box) {
      hBars(box, {
        aria: "Log events by stage", empty: "No log events recorded yet.", labelW: 160,
        rows: (T.by_logger || []).map((r) => ({
          label: r.label, end: String(r.info + r.warning + r.error),
          segments: [{ value: r.info, color: "var(--c5)" }, { value: r.warning, color: "var(--warn)" }, { value: r.error, color: "var(--bad)" }],
          tip: `<b>${esc(r.label)}</b><br>${r.info} info, ${r.warning} warnings, ${r.error} errors`,
        })),
        legend: [{ name: "Info", color: "var(--c5)" }, { name: "Warnings", color: "var(--warn)" }, { name: "Errors", color: "var(--bad)" }],
      });
    },
    dbttests(box) {
      const d = T.dbt;
      if (!d) return empty(box, "No dbt run_results.json found. Run the Gold build to produce test results.");
      const t = d.tests;
      donut(box, {
        aria: "dbt test results", empty: "The saved dbt report has no tests.",
        center: t.total ? Math.round((100 * t.pass) / t.total) + "%" : "N/A", centerSub: `${t.pass} of ${t.total} passed`,
        items: [
          { label: "Passed", value: t.pass, color: "var(--ok)", tip: `<b>Passed</b><br>${t.pass} tests` },
          { label: "Warnings", value: t.warn, color: "var(--warn)", tip: `<b>Warnings</b><br>${t.warn} tests` },
          { label: "Failed", value: t.fail, color: "var(--bad)", tip: `<b>Failed</b><br>${t.fail} tests` },
          { label: "Errored", value: t.error, color: "var(--bad)", tip: `<b>Errored</b><br>${t.error} tests` },
          { label: "Skipped", value: t.skip, color: "var(--idle)", tip: `<b>Skipped</b><br>${t.skip} tests` },
        ].filter((i) => i.value > 0 || i.label === "Passed"),
      });
    },
    dbtmodels(box) {
      const d = T.dbt;
      if (!d) return empty(box, "No dbt model timings available.");
      hBars(box, {
        aria: "dbt model runtimes", labelW: 130,
        rows: d.models.map((m) => ({
          label: m.name, end: m.seconds != null ? m.seconds.toFixed(2) + " s" : "N/A",
          segments: [{ value: m.seconds || 0, color: m.status === "success" ? "var(--c1)" : "var(--bad)" }],
          tip: `<b>${esc(m.name)}</b><br>${esc(m.status)}<br>${m.seconds != null ? m.seconds.toFixed(2) + " s" : "no timing"}`,
        })),
      });
    },
    storage(box) {
      hBars(box, {
        aria: "Storage size per layer", labelW: 90,
        rows: (T.storage || []).map((s) => ({
          label: s.label, end: s.present ? s.mb.toFixed(1) + " MB" : "empty",
          segments: [{ value: s.mb, color: "var(--c1)" }],
          tip: `<b>${esc(s.label)}</b><br>${s.present ? s.mb.toFixed(2) + " MB" : "No output"}` +
            (s.files != null ? `<br>${s.files} files` : "") + (s.modified ? `<br>Updated ${esc(s.modified)}` : ""),
        })),
      });
    },
  };

  function renderAll() {
    document.querySelectorAll("[data-chart]").forEach((box) => {
      const fn = CHARTS[box.dataset.chart];
      if (!fn) return;
      box.replaceChildren();
      try { fn(box); } catch (err) { console.error("chart failed:", box.dataset.chart, err); empty(box, "This chart could not be drawn."); }
      box.dataset.w = box.clientWidth;
    });
  }

  let timer;
  new ResizeObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const stale = [...document.querySelectorAll("[data-chart]")].some((b) => Math.abs(b.clientWidth - (+b.dataset.w || 0)) > 8);
      if (stale) renderAll();
    }, 120);
  }).observe(document.body);

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", renderAll);
  else renderAll();
})();
