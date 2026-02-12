#!/usr/bin/env python3
"""
NHANES Unified Correlation Matrix
──────────────────────────────────
Generates a SINGLE self-contained HTML with:
  • Year-toggle between all available cached cohorts
  • Lower-triangle only (symmetric matrix)
  • Pearson r + p-value per pair  (scipy.stats)
  • Pairs with < MIN_SHARED shared observations masked out
  • Only statistically significant pairs (p < P_THRESHOLD) are clickable
  • Scatter plot with swap-axes button, regression line
  • Variable labels link directly to the NHANES documentation page
"""

import os, sys, glob, json, base64
import numpy as np
import pandas as pd
from scipy import stats

# ─── Configuration ────────────────────────────────────────────────────────────
COHORTS = {                 # cycle label → XPT file suffix
    "2009-2010": "F",
    "2011-2012": "G",
    "2013-2014": "H",
    "2015-2016": "I",
    "2017-2018": "J",
}

MIN_VALID_COL  = 100    # rows with non-null values required to include a column
MIN_SHARED     = 50     # shared non-null rows required to compute a pair's r
P_THRESHOLD    = 0.05   # significance cutoff
MAX_VARS       = 200    # cap columns per cohort (sorted by n_valid desc)
SCATTER_ROWS   = 3000   # rows sampled per cohort for on-the-fly scatter display

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "Correlation_Matrix.html")
CACHE_DIR   = os.path.expanduser("~/.cache/pandas_nhanes")


# ─── Data loading ─────────────────────────────────────────────────────────────

def load_merged(suffix: str):
    pattern = os.path.join(CACHE_DIR, f"*_{suffix}.xpt")
    files   = glob.glob(pattern)
    if not files:
        return None
    print(f"  {len(files)} XPT files found for suffix _{suffix}")

    dfs = {}
    for f in files:
        tbl = os.path.basename(f).replace(f"_{suffix}.xpt", "")
        try:
            df = pd.read_sas(f)
            if "SEQN" not in df.columns:
                continue
            dfs[tbl] = df
        except Exception as e:
            print(f"    ✗ {tbl}: {e}")

    if not dfs:
        return None

    merged = None
    for _, df in sorted(dfs.items(), key=lambda x: -len(x[1])):
        if merged is None:
            merged = df.copy()
        else:
            merged = merged.merge(df, on="SEQN", how="outer", suffixes=("", "_dup"))
            dup = [c for c in merged.columns if c.endswith("_dup")]
            if dup:
                merged.drop(columns=dup, inplace=True)

    print(f"  Merged → {len(merged):,} rows × {len(merged.columns):,} columns")
    return merged


def select_columns(df):
    num = df.select_dtypes(include=[np.number]).columns.tolist()
    num = [c for c in num if c != "SEQN"]
    valid = [(c, int(df[c].notna().sum()))
             for c in num
             if df[c].notna().sum() >= MIN_VALID_COL and df[c].std() > 0]
    valid.sort(key=lambda x: -x[1])
    return [c for c, _ in valid[:MAX_VARS]]


# ─── Metadata (descriptions + NHANES links) ───────────────────────────────────

def get_metadata(cols, cycle):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from pandas_nhanes.api import get_variables
        vdf = get_variables()
        cyc = vdf[vdf["cycle name"] == cycle]
    except Exception as e:
        print(f"  Warning: could not load variable descriptions – {e}")
        cyc = pd.DataFrame()

    meta = {}
    for col in cols:
        row = cyc[cyc["variable name"] == col] if not cyc.empty else pd.DataFrame()
        if not row.empty:
            r = row.iloc[0]
            desc = str(r.get("variable explanation", col))
            doc  = str(r.get("dataset documentation link", ""))
            link = f"{doc}#{col}" if doc else \
                   f"https://wwwn.cdc.gov/nchs/nhanes/search/variablelist.aspx?SearchTerms={col}"
        else:
            desc = col
            link = f"https://wwwn.cdc.gov/nchs/nhanes/search/variablelist.aspx?SearchTerms={col}"
        meta[col] = {"desc": desc, "link": link}
    return meta


# ─── Correlation + significance ───────────────────────────────────────────────

def compute_lower_triangle(df, cols):
    """Return corr[n,n], pval[n,n], nshared[n,n]  – upper tri filled with NaN."""
    n   = len(cols)
    arr = df[cols].to_numpy(dtype=float)
    corr   = np.full((n, n), np.nan)
    pval   = np.full((n, n), np.nan)
    nshare = np.zeros((n, n), dtype=np.int32)

    total = n * (n - 1) // 2
    done  = 0
    step  = max(1, total // 20)

    for i in range(n):
        for j in range(i):          # lower triangle only
            mask = ~(np.isnan(arr[:, i]) | np.isnan(arr[:, j]))
            ns   = int(mask.sum())
            nshare[i, j] = ns
            if ns >= MIN_SHARED:
                x, y = arr[mask, i], arr[mask, j]
                if x.std() > 0 and y.std() > 0:
                    r, p = stats.pearsonr(x, y)
                    corr[i, j] = round(float(r), 4)
                    pval[i, j] = float(p)
            done += 1
            if done % step == 0:
                pct = done * 100 // total
                print(f"    [{pct:3d}%] {done}/{total} pairs computed", end="\r")

    print()
    return corr, pval, nshare


# ─── Scatter data ─────────────────────────────────────────────────────────────

def build_col_data(df, cols):
    """Sample SCATTER_ROWS rows and store each column as a fixed-length list
    (None for NaN).  JS zips two columns on click → instant scatter for any pair."""
    sample = df[cols].sample(n=min(SCATTER_ROWS, len(df)), random_state=42)
    col_data = {}
    for col in cols:
        vals = sample[col].tolist()
        col_data[col] = [
            None if (v is None or (isinstance(v, float) and np.isnan(v)))
            else round(float(v), 3)
            for v in vals
        ]
    print(f"  Column data: {len(cols)} vars × {len(sample):,} sampled rows")
    return col_data


# ─── Per-cohort pipeline ──────────────────────────────────────────────────────

def process_cohort(cycle, suffix):
    print(f"\n{'━'*56}")
    print(f"  Cohort {cycle}  (suffix _{suffix})")
    print(f"{'━'*56}")

    df = load_merged(suffix)
    if df is None:
        print("  No cached data – skipping.")
        return None

    cols = select_columns(df)
    print(f"  Variables selected: {len(cols)}")
    if len(cols) < 2:
        return None

    meta = get_metadata(cols, cycle)

    print(f"  Computing correlations for {len(cols)} vars …")
    corr, pval, nshare = compute_lower_triangle(df, cols)

    n_sig = int(np.nansum(pval < P_THRESHOLD))
    print(f"  Significant pairs: {n_sig:,}")

    col_data = build_col_data(df, cols)

    # Convert NaN → None for JSON serialisation
    def _clean(arr):
        return [[None if (isinstance(v, float) and np.isnan(v)) else v
                 for v in row]
                for row in arr.tolist()]

    return {
        "cycle":    cycle,
        "cols":     cols,
        "meta":     meta,
        "corr":     _clean(corr),
        "pval":     _clean(pval),
        "nshare":   nshare.tolist(),
        "col_data": col_data,
        "n_rows":   int(len(df)),
        "n_sig":    n_sig,
    }


# ─── HTML generation ──────────────────────────────────────────────────────────

def b64json(obj):
    return base64.b64encode(json.dumps(obj, separators=(",", ":")).encode()).decode()


def generate_html(cohort_data, output):
    years_json  = json.dumps(list(cohort_data.keys()))
    payload_b64 = {yr: b64json(d) for yr, d in cohort_data.items()}
    payload_js  = "{\n" + ",\n".join(
        f'  {json.dumps(yr)}: {json.dumps(b64)}' for yr, b64 in payload_b64.items()
    ) + "\n}"

    min_shared_js = MIN_SHARED
    p_thresh_js   = P_THRESHOLD

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NHANES Correlation Matrix</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
          background: #f4f6f9; color: #2d3748; min-height: 100vh; }}

  /* ── top bar ── */
  #topbar {{ background: #1a365d; color: #fff; padding: 14px 24px; display: flex;
             align-items: center; gap: 20px; flex-wrap: wrap; }}
  #topbar h1 {{ font-size: 1.25rem; font-weight: 700; letter-spacing: .5px; }}
  #year-btns {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .yr-btn {{ background: #2c5282; border: none; color: #bee3f8; padding: 6px 14px;
             border-radius: 20px; cursor: pointer; font-size: .85rem; transition: all .15s; }}
  .yr-btn:hover {{ background: #3182ce; color: #fff; }}
  .yr-btn.active {{ background: #63b3ed; color: #1a365d; font-weight: 700; }}
  #stats {{ font-size: .8rem; color: #a0aec0; margin-left: auto; white-space: nowrap; }}

  /* ── main layout ── */
  #main {{ display: flex; flex-direction: column; align-items: center;
           padding: 20px; gap: 20px; }}

  /* ── legend ── */
  #legend {{ display: flex; align-items: center; gap: 10px; font-size: .8rem;
             color: #555; flex-wrap: wrap; justify-content: center; }}
  #grad-bar {{ width: 160px; height: 14px; border-radius: 3px;
               background: linear-gradient(to right, #2166ac, #f7f7f7, #d6604d); }}
  .leg-item {{ display: flex; align-items: center; gap: 5px; }}
  .leg-sw {{ width: 14px; height: 14px; border-radius: 2px; flex-shrink: 0; }}

  /* ── matrix scroll container ── */
  #matrix-scroll {{ overflow: auto; max-width: 98vw; background: #fff;
                    border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.12);
                    padding: 6px; }}

  /* ── tooltip ── */
  #tip {{ position: fixed; pointer-events: none; background: rgba(26,54,93,.93);
          color: #fff; padding: 9px 13px; border-radius: 6px; font-size: .78rem;
          line-height: 1.6; z-index: 9999; display: none; max-width: 300px;
          box-shadow: 0 4px 14px rgba(0,0,0,.3); }}

  /* ── scatter panel ── */
  #scatter-panel {{ width: 100%; max-width: 860px; background: #fff;
                   border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.12);
                   padding: 20px; display: none; }}
  #scatter-panel h3 {{ font-size: 1rem; color: #2d3748; margin-bottom: 6px; }}
  #scatter-meta {{ font-size: .8rem; color: #718096; margin-bottom: 12px;
                   line-height: 1.7; }}
  #scatter-meta a {{ color: #3182ce; text-decoration: none; }}
  #scatter-meta a:hover {{ text-decoration: underline; }}
  #swap-btn {{ background: #ebf8ff; border: 1px solid #90cdf4; color: #2b6cb0;
               padding: 5px 16px; border-radius: 4px; cursor: pointer;
               font-size: .82rem; margin-bottom: 14px; }}
  #swap-btn:hover {{ background: #bee3f8; }}
  #scatter-plot {{ width: 100%; height: 440px; }}

  #instructions {{ font-size: .81rem; color: #718096; text-align: center;
                   max-width: 700px; }}
</style>
</head>
<body>

<div id="topbar">
  <h1>NHANES Correlation Matrix</h1>
  <div id="year-btns"></div>
  <div id="stats"></div>
</div>

<div id="main">
  <div id="legend">
    <span style="font-weight:600">Correlation:</span>
    <span>−1</span>
    <div id="grad-bar"></div>
    <span>+1</span>
    &nbsp;
    <div class="leg-item"><div class="leg-sw" style="background:#d0d0d0"></div>
      <span>Not significant (p ≥ 0.05)</span></div>
    <div class="leg-item"><div class="leg-sw" style="background:#f0f0f0;border:1px solid #ccc"></div>
      <span>Insufficient shared data</span></div>
  </div>

  <p id="instructions">
    Hover any cell for details &nbsp;·&nbsp;
    <strong>Click a coloured cell</strong> to view scatter plot &nbsp;·&nbsp;
    Variable names are <span style="color:#3182ce;text-decoration:underline">links</span>
    to NHANES documentation
  </p>

  <div id="matrix-scroll">
    <svg id="matrix-svg" style="display:block"></svg>
  </div>

  <div id="scatter-panel">
    <h3 id="scatter-title"></h3>
    <div id="scatter-meta"></div>
    <button id="swap-btn" onclick="swapAxes()">⇄ Swap Axes</button>
    <div id="scatter-plot"></div>
  </div>
</div>

<div id="tip"></div>

<script>
// ── Embedded payload ────────────────────────────────────────────────────────
const YEARS   = {years_json};
const PAYLOAD = {payload_js};

// ── Constants ───────────────────────────────────────────────────────────────
const MIN_SHARED  = {min_shared_js};
const P_THRESHOLD = {p_thresh_js};

// ── Color scale (RdBu diverging) ────────────────────────────────────────────
const STOPS = [
  [-1.0, [33,  102, 172]],
  [-0.5, [103, 169, 207]],
  [ 0.0, [247, 247, 247]],
  [ 0.5, [239, 138,  98]],
  [ 1.0, [214,  96,  77]],
];
function corrColor(r) {{
  r = Math.max(-1, Math.min(1, r));
  for (let k = 0; k < STOPS.length - 1; k++) {{
    const [r0, c0] = STOPS[k], [r1, c1] = STOPS[k + 1];
    if (r >= r0 && r <= r1) {{
      const t  = (r - r0) / (r1 - r0);
      const ch = c0.map((v, i) => Math.round(v + t * (c1[i] - v)));
      return `rgb(${{ch[0]}},${{ch[1]}},${{ch[2]}})`;
    }}
  }}
  return '#f7f7f7';
}}

// ── State ───────────────────────────────────────────────────────────────────
let active = null;   // decoded cohort object
let activeYear = null;
let scatterState = null;  // {{ i, j, swapped }}

// ── Year buttons ────────────────────────────────────────────────────────────
const yearBtnsEl = document.getElementById('year-btns');
YEARS.forEach(yr => {{
  const btn = document.createElement('button');
  btn.className   = 'yr-btn';
  btn.textContent = yr;
  btn.onclick     = () => loadYear(yr);
  yearBtnsEl.appendChild(btn);
}});

function loadYear(yr) {{
  if (yr === activeYear) return;
  activeYear = yr;
  document.querySelectorAll('.yr-btn')
    .forEach(b => b.classList.toggle('active', b.textContent === yr));
  active = JSON.parse(atob(PAYLOAD[yr]));
  renderMatrix();
  document.getElementById('scatter-panel').style.display = 'none';
}}

// ── Matrix ──────────────────────────────────────────────────────────────────
const LABEL_PAD   = 220;  // px reserved for y-axis labels (left)
const LABEL_PAD_X = 220;  // px reserved for x-axis labels (bottom, rotated)
const MIN_LABEL_PX = 11;  // minimum cell height (px) before a label is drawn

function renderMatrix() {{
  const {{ cols, meta, corr, pval, nshare, n_rows, n_sig }} = active;
  const n      = cols.length;
  const cellPx = Math.max(4, Math.min(13, Math.floor(880 / n)));
  const matPx  = n * cellPx;
  // stride: skip labels when cells are too small to fit text without overlap
  const stride = Math.ceil(MIN_LABEL_PX / cellPx); // e.g. cellPx=4 → stride=3

  const svgW = matPx + LABEL_PAD;
  const svgH = matPx + LABEL_PAD_X;

  const svg = document.getElementById('matrix-svg');
  svg.setAttribute('width',  svgW);
  svg.setAttribute('height', svgH);
  svg.setAttribute('viewBox', `0 0 ${{svgW}} ${{svgH}}`);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const NS = 'http://www.w3.org/2000/svg';
  const mk = (tag, attrs, parent) => {{
    const el = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    if (parent) parent.appendChild(el);
    return el;
  }};

  // White background
  mk('rect', {{ x: 0, y: 0, width: svgW, height: svgH, fill: '#fff' }}, svg);

  // clipPaths so labels never bleed into the matrix area or beyond their box
  const defs = mk('defs', {{}}, svg);
  const cpY  = mk('clipPath', {{ id: 'cpY' }}, defs);
  mk('rect', {{ x: 0, y: 0, width: LABEL_PAD - 2, height: matPx }}, cpY);
  const cpX  = mk('clipPath', {{ id: 'cpX' }}, defs);
  mk('rect', {{ x: LABEL_PAD, y: matPx, width: matPx, height: LABEL_PAD_X }}, cpX);

  // ── cells ──
  const g = mk('g', {{ transform: `translate(${{LABEL_PAD}},0)` }}, svg);

  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < i; j++) {{   // lower triangle only
      const r  = corr[i][j];
      const p  = pval[i][j];
      const ns = nshare[i][j];

      let fill, clickable;
      if (r === null || ns < MIN_SHARED) {{
        fill = '#f0f0f0';
        clickable = false;
      }} else if (p === null || p >= P_THRESHOLD) {{
        fill = '#d0d0d0';
        clickable = false;
      }} else {{
        fill = corrColor(r);
        clickable = true;
      }}

      const rect = mk('rect', {{
        x: j * cellPx,  y: i * cellPx,
        width:  cellPx, height: cellPx,
        fill,
        stroke: '#fff', 'stroke-width': cellPx > 5 ? '0.4' : '0',
        style: clickable ? 'cursor:pointer' : 'cursor:default',
      }}, g);

      rect.addEventListener('mouseenter', e => showTip(e, i, j));
      rect.addEventListener('mouseleave', hideTip);
      if (clickable) rect.addEventListener('click', () => doScatter(i, j));
    }}
  }}

  const fSize = Math.max(7, Math.min(11, cellPx + 3));

  // ── Y-labels (left) – thinned by stride ──
  const gy = mk('g', {{ 'clip-path': 'url(#cpY)' }}, svg);
  for (let i = 0; i < n; i++) {{
    if (i % stride !== 0) continue;
    const cy  = i * cellPx + cellPx / 2;
    const a   = mk('a', {{ href: meta[cols[i]].link, target: '_blank' }}, gy);
    const txt = mk('text', {{
      x: LABEL_PAD - 7, y: cy,
      'text-anchor': 'end', 'dominant-baseline': 'middle',
      'font-size': fSize, fill: '#3182ce',
      style: 'text-decoration:underline;cursor:pointer',
    }}, a);
    txt.textContent = trunc(meta[cols[i]].desc, 30);
    txt.addEventListener('mouseenter', e => labelTip(e, cols[i], meta[cols[i]].desc));
    txt.addEventListener('mouseleave', hideTip);
  }}

  // ── X-labels (bottom, 45°) – thinned by stride ──
  const gx = mk('g', {{ 'clip-path': 'url(#cpX)', transform: `translate(${{LABEL_PAD}},0)` }}, svg);
  for (let j = 0; j < n; j++) {{
    if (j % stride !== 0) continue;
    const cx  = j * cellPx + cellPx / 2;
    const a   = mk('a', {{ href: meta[cols[j]].link, target: '_blank' }}, gx);
    const txt = mk('text', {{
      x: cx, y: matPx + 6,
      'text-anchor': 'start', 'dominant-baseline': 'auto',
      'font-size': fSize, fill: '#3182ce',
      transform: `rotate(45,${{cx}},${{matPx + 6}})`,
      style: 'text-decoration:underline;cursor:pointer',
    }}, a);
    txt.textContent = trunc(meta[cols[j]].desc, 30);
    txt.addEventListener('mouseenter', e => labelTip(e, cols[j], meta[cols[j]].desc));
    txt.addEventListener('mouseleave', hideTip);
  }}

  document.getElementById('stats').textContent =
    `${{n}} variables · ${{n_rows.toLocaleString()}} respondents · ${{n_sig.toLocaleString()}} significant pairs · all pairs clickable`;
}}

// ── Tooltip ─────────────────────────────────────────────────────────────────
const tipEl = document.getElementById('tip');

function showTip(e, i, j) {{
  const {{ cols, meta, corr, pval, nshare }} = active;
  const r  = corr[i][j];
  const p  = pval[i][j];
  const ns = nshare[i][j];
  const ci = cols[i], cj = cols[j];

  let body = `<b>${{meta[cj].desc}}</b> <span style="color:#90cdf4">(${{cj}})</span><br>` +
             `<b>vs ${{meta[ci].desc}}</b> <span style="color:#90cdf4">(${{ci}})</span><br>`;

  if (r === null || ns < MIN_SHARED) {{
    body += `<em>Insufficient shared data (n=${{ns}})</em>`;
  }} else {{
    const sig = (p !== null && p < P_THRESHOLD)
                ? '<span style="color:#68d391">✔ significant</span>'
                : '<span style="color:#fc8181">✘ not significant</span>';
    body += `r = ${{r != null ? r.toFixed(3) : '–'}}<br>` +
            `p = ${{p != null ? p.toExponential(2) : '–'}}<br>` +
            `n = ${{ns.toLocaleString()}} &nbsp; ${{sig}}`;
  }}
  tipEl.innerHTML = body;
  posTip(e);
  tipEl.style.display = 'block';
}}

function labelTip(e, code, desc) {{
  tipEl.innerHTML = `<b>${{code}}</b><br>${{desc}}<br><em style="color:#90cdf4">Opens NHANES docs ↗</em>`;
  posTip(e);
  tipEl.style.display = 'block';
}}

function hideTip() {{ tipEl.style.display = 'none'; }}

function posTip(e) {{
  const x = e.clientX + 14, y = e.clientY + 14;
  tipEl.style.left = Math.min(x, window.innerWidth  - 320) + 'px';
  tipEl.style.top  = Math.min(y, window.innerHeight - 160) + 'px';
}}

document.addEventListener('mousemove', e => {{
  if (tipEl.style.display === 'block') posTip(e);
}});

// ── Scatter ──────────────────────────────────────────────────────────────────
function doScatter(i, j) {{
  scatterState = {{ i, j, swapped: false }};
  drawScatter();
  const panel = document.getElementById('scatter-panel');
  panel.style.display = 'block';
  setTimeout(() => panel.scrollIntoView({{ behavior: 'smooth', block: 'start' }}), 30);
}}

function swapAxes() {{
  if (!scatterState) return;
  scatterState.swapped = !scatterState.swapped;
  drawScatter();
}}

function drawScatter() {{
  const {{ i, j, swapped }} = scatterState;
  const {{ cols, meta, corr, pval, nshare, col_data }} = active;
  const ci = cols[i], cj = cols[j];
  const di = meta[ci].desc, dj = meta[cj].desc;
  const r  = corr[i][j];
  const p  = pval[i][j];
  const ns = nshare[i][j];

  // Compute intersection row-by-row from sampled column arrays – instant
  const vi = col_data[ci];
  const vj = col_data[cj];
  const xs = [], ys = [];
  for (let k = 0; k < vi.length; k++) {{
    if (vi[k] !== null && vj[k] !== null) {{
      xs.push(swapped ? vi[k] : vj[k]);
      ys.push(swapped ? vj[k] : vi[k]);
    }}
  }}

  // Determine axis labels
  const xDesc = swapped ? di : dj;
  const yDesc = swapped ? dj : di;
  const xCode = swapped ? ci : cj;
  const yCode = swapped ? cj : ci;

  document.getElementById('scatter-title').textContent =
    `${{xDesc}} × ${{yDesc}}`;

  document.getElementById('scatter-meta').innerHTML =
    `<b>X:</b> ${{xDesc}} (<a href="${{meta[xCode].link}}" target="_blank">${{xCode}}</a>) &nbsp;| ` +
    `<b>Y:</b> ${{yDesc}} (<a href="${{meta[yCode].link}}" target="_blank">${{yCode}}</a>)<br>` +
    `Pearson r = <b>${{r != null ? r.toFixed(4) : '–'}}</b> &nbsp;|&nbsp; ` +
    `p = <b>${{p != null ? p.toExponential(3) : '–'}}</b> &nbsp;|&nbsp; ` +
    `n = <b>${{ns != null ? ns.toLocaleString() : '–'}}</b> shared (full data)  |  ` +
    `showing <b>${{xs.length.toLocaleString()}}</b> sampled points`;

  if (xs.length < 2) {{
    document.getElementById('scatter-plot').innerHTML =
      '<p style="padding:50px;text-align:center;color:#718096">Not enough shared sampled points to plot.</p>';
    return;
  }}

  // Regression line
  const nn  = xs.length;
  const mx  = xs.reduce((a, v) => a + v, 0) / nn;
  const my  = ys.reduce((a, v) => a + v, 0) / nn;
  const num = xs.reduce((a, v, k) => a + (v - mx) * (ys[k] - my), 0);
  const den = xs.reduce((a, v) => a + (v - mx) ** 2, 0);
  const m   = den ? num / den : 0;
  const b   = my - m * mx;
  const xmin = Math.min(...xs), xmax = Math.max(...xs);

  Plotly.react('scatter-plot', [
    {{
      x: xs, y: ys,
      mode: 'markers', type: 'scatter',
      name: 'Observations',
      marker: {{ size: 6, opacity: .55, color: '#3182ce' }},
      hovertemplate: `${{xCode}}: %{{x:.3g}}<br>${{yCode}}: %{{y:.3g}}<extra></extra>`,
    }},
    {{
      x: [xmin, xmax], y: [m * xmin + b, m * xmax + b],
      mode: 'lines', type: 'scatter',
      name: 'Regression',
      line: {{ color: '#e53e3e', width: 2 }},
      hoverinfo: 'skip',
    }},
  ], {{
    xaxis: {{ title: {{ text: `${{xDesc}}` }}, automargin: true }},
    yaxis: {{ title: {{ text: `${{yDesc}}` }}, automargin: true }},
    showlegend: false,
    margin: {{ t: 10, r: 20, b: 90, l: 90 }},
    hovermode: 'closest',
  }}, {{ responsive: true }});
}}

// ── Helpers ──────────────────────────────────────────────────────────────────
function trunc(s, n) {{
  return s && s.length > n ? s.slice(0, n - 1) + '…' : (s || '');
}}

// ── Boot ─────────────────────────────────────────────────────────────────────
loadYear(YEARS[YEARS.length - 1]);   // default: most recent available year
</script>
</body>
</html>"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"\n✅  Written → {output}  ({size_mb:.1f} MB)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    all_data = {}
    for cycle, suffix in COHORTS.items():
        result = process_cohort(cycle, suffix)
        if result:
            all_data[cycle] = result

    if not all_data:
        print(
            "\n❌  No cohort data found in cache.\n"
            "    Run pandas_nhanes.get_cycle_variables() first to populate ~/.cache/pandas_nhanes/"
        )
        sys.exit(1)

    print(f"\n📊  Generating unified HTML for {len(all_data)} cohort(s)…")
    generate_html(all_data, OUTPUT_FILE)
    print("🎉  Done!")


if __name__ == "__main__":
    main()
