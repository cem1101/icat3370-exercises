"""Helper functions for the ICAT3370 exercises."""
import os
from datetime import datetime
from math import asin, cos, degrees, pi, radians, sin
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

DATA = Path(__file__).parent / "data"

# Label positions (points) for missions whose markers overlap in the trade-off plot
LABEL_OFFSETS = {"ICEYE": (8, -15), "PlanetScope": (8, 6), "WorldView-3": (-30, 10), "MODIS": (-46, -18), "Sentinel-3 OLCI": (8, 8), "Sentinel-5P": (-40, 12), "Sentinel-1": (8, 6), "Sentinel-2": (8, -12)}


# ---------------------------------------------------------------- mission table
COLUMNS = {"mission": "mission", "operator": "operator", "measures": "what it measures",
           "pixel_m": "pixel size (m)", "revisit_days": "days between visits",
           "swath_km": "strip width (km)", "bands": "bands", "access": "cost"}


def load_missions():
    """The course mission table, with plain column names. Technical notes and sources stay in the file."""
    df = pd.read_csv(DATA / "missions.csv")
    return df[list(COLUMNS)].rename(columns=COLUMNS)


def plot_trade_off(missions, highlight=()):
    """Pixel size against revisit time, one point per mission. Missions named in highlight are drawn larger."""
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    colours = {"free": "#1f6fb4", "paid": "#b8336a"}
    markers = {"reflected": "o", "radar": "s", "trace": "^"}
    for _, m in missions.iterrows():
        kind = m["what it measures"].split()[0]
        hl = m["mission"] in highlight
        ax.scatter(m["pixel size (m)"], m["days between visits"], s=170 if hl else (120 if kind != "reflected" else 60),
                   c=colours[m["cost"]], marker=markers[kind],
                   edgecolors="black" if hl else "white", linewidths=2 if hl else 1,
                   zorder=3 if kind != "reflected" else 4)
        ax.annotate(m["mission"], (m["pixel size (m)"], m["days between visits"]),
                    xytext=LABEL_OFFSETS.get(m["mission"], (7, 5)), textcoords="offset points",
                    fontsize=10, fontweight="bold" if hl else "normal")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.7, 8000); ax.set_ylim(0.6, 14)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}" if v in (2, 5) else ""))
    ax.set_xlabel("Pixel size (m)   ← finer detail")
    ax.set_ylabel("Days between visits   ← more often")
    ax.set_title("Pixel size against revisit, all nine missions")
    ax.grid(True, which="both", alpha=0.3)
    for label, c in colours.items():
        ax.scatter([], [], c=c, label=label)
    legend_names = {"reflected": "reflected sunlight", "radar": "radar backscatter", "trace": "trace gases"}
    for key, mk in markers.items():
        ax.scatter([], [], c="grey", marker=mk, label=legend_names[key])
    ax.legend(loc="upper left", frameon=False)
    plt.show()


# ---------------------------------------------------------------- image swipe
def swipe(images, width=900, start=50):
    """Two images on top of each other with a handle you drag to reveal one over the other.

    images = {label: path}. The first image is the left/under layer. If more than two are given,
    a menu lets you choose which image is compared against the first. Pure HTML, no extension needed.
    """
    import base64, uuid
    from IPython.display import HTML, display
    labels = list(images)
    def data_uri(path):
        p = DATA.parent / path
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    uris = {lab: data_uri(images[lab]) for lab in labels}
    uid = "sw" + uuid.uuid4().hex[:8]
    menu = ""
    if len(labels) > 2:
        opts = "".join(f'<option value="{lab}">{lab}</option>' for lab in labels[1:])
        menu = f'<label style="font:14px sans-serif">Compare <b>{labels[0]}</b> with: <select id="{uid}_sel">{opts}</select></label>'
    html = f"""
<div style="width:{width}px;max-width:100%;font:14px sans-serif">
  {menu}
  <div id="{uid}" style="position:relative;width:100%;user-select:none;margin-top:6px">
    <img id="{uid}_l" src="{uris[labels[0]]}" style="display:block;width:100%">
    <img id="{uid}_r" src="{uris[labels[1]]}" style="position:absolute;top:0;left:0;width:100%;clip-path:inset(0 0 0 {start}%)">
    <div id="{uid}_bar" style="position:absolute;top:0;bottom:0;left:{start}%;width:3px;background:#fff;box-shadow:0 0 4px #000;pointer-events:none"></div>
    <div id="{uid}_ll" style="position:absolute;top:8px;left:8px;background:rgba(0,0,0,.6);color:#fff;padding:2px 8px;border-radius:3px">{labels[0]}</div>
    <div id="{uid}_rl" style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,.6);color:#fff;padding:2px 8px;border-radius:3px">{labels[1]}</div>
    <input id="{uid}_in" type="range" min="0" max="100" value="{start}" style="position:absolute;top:0;left:0;width:100%;height:100%;margin:0;opacity:0;cursor:ew-resize">
  </div>
</div>
<script>
(function(){{
  var inp=document.getElementById("{uid}_in"), r=document.getElementById("{uid}_r"), bar=document.getElementById("{uid}_bar");
  function upd(){{ r.style.clipPath="inset(0 0 0 "+inp.value+"%)"; bar.style.left=inp.value+"%"; }}
  inp.addEventListener("input",upd); upd();
  var sel=document.getElementById("{uid}_sel");
  if(sel){{ var uris={uris!r}; sel.addEventListener("change",function(){{ r.src=uris[sel.value]; document.getElementById("{uid}_rl").textContent=sel.value; }}); }}
}})();
</script>"""
    display(HTML(html))


def image_slider(images, width=900):
    """A slider that switches between whole images."""
    import ipywidgets as widgets
    from IPython.display import Image, display
    labels = list(images); out = widgets.Output()
    slider = widgets.SelectionSlider(options=labels, value=labels[0], description="", continuous_update=True,
                                     layout=widgets.Layout(width=f"{width}px"))
    def show(label):
        out.clear_output(wait=True)
        with out:
            display(Image(filename=str(DATA.parent / images[label]), width=width))
    slider.observe(lambda ch: show(ch["new"]), names="value"); show(labels[0])
    display(widgets.VBox([slider, out]))


# ---------------------------------------------------------------- spatial resolution calculator
_VAASA_RGB = {}


def _vaasa_rgb(product="S2B_MSIL2A_20260621T101019_N0512_R022_T34VER_20260621T140048"):
    """A 10 m true-colour crop of Vaasa centre, 3 km across (cached), cut from rgb_vaasa_6km.jpg."""
    import numpy as np
    from PIL import Image
    if product not in _VAASA_RGB:
        img = np.asarray(Image.open(_scene_dir(product) / "rgb_vaasa_6km.jpg").convert("RGB"), dtype=float) / 255
        _VAASA_RGB[product] = img[83:383, 231:531]        # centre 63.096 N 21.616 E, 300 x 300 pixels of 10 m
    return _VAASA_RGB[product]


def pixel_size_calculator():
    """Three sliders (altitude, focal length, detector size). The drawing and the Vaasa image update as you move them."""
    import numpy as np
    import ipywidgets as w
    from IPython.display import display
    st = {"description_width": "170px"}; lay = w.Layout(width="520px")
    H = w.FloatSlider(value=786, min=300, max=1500, step=1, description="altitude (km)", readout_format=".0f",
                      style=st, layout=lay, continuous_update=True)
    f = w.FloatSlider(value=0.6, min=0.1, max=15, step=0.05, description="focal length (m)", readout_format=".2f",
                      style=st, layout=lay, continuous_update=True)
    p = w.FloatSlider(value=7.5, min=1, max=50, step=0.5, description="detector element, sensor pixel (µm)", readout_format=".1f",
                      style=st, layout=lay, continuous_update=True)
    n_det = 31152
    out = w.Output()
    img = _vaasa_rgb()                                   # 10 m pixels, about 300 x 300
    n10 = img.shape[0]
    coarse = {}                                          # pre-computed block means, so sliding stays smooth
    for k in range(1, 31):
        m = (n10 // k) * k
        coarse[k] = img[:m, :m].reshape(m // k, k, m // k, k, 3).mean(axis=(1, 3))
    def draw(_=None):
        G = p.value * 1e-6 * H.value * 1e3 / f.value     # m
        S = n_det * G / 1e3                              # km
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.1]}, dpi=80)
        # ---- left: the geometry, drawn to scale in angle (not in distance)
        ax1.set_xlim(-1.5, 1.5); ax1.set_ylim(-0.25, 1.35); ax1.axis("off")
        half = 0.45 * min(1.0, G / 30)                   # visual half-width of the ground pixel (capped)
        half = max(half, 0.02)
        ax1.plot([-half, half], [0, 0], color="#1f6fb4", lw=8, solid_capstyle="butt")
        ax1.text(0, -0.12, f"pixel on the ground  G = {G:,.1f} m", ha="center", fontsize=11, color="#1f6fb4")
        ax1.plot([-0.25, 0.25], [0.8, 0.8], color="k", lw=3); ax1.text(0.3, 0.8, "telescope", va="center", fontsize=10)
        dh = half * 0.6 / 0.8 * 0.35 / max(half, 1e-9) * 0.35 if False else 0.12 * min(1.0, p.value / 20) + 0.02
        ax1.plot([-dh, dh], [1.15, 1.15], color="#b8336a", lw=6, solid_capstyle="butt")
        ax1.text(0, 1.22, f"detector element (sensor pixel)  p = {p.value:.1f} µm", ha="center", fontsize=10, color="#b8336a")
        for s in (-1, 1):
            ax1.plot([s * dh, 0, -s * half], [1.15, 0.8, 0], color="grey", lw=1)
        ax1.annotate("", xy=(-1.2, 0.8), xytext=(-1.2, 1.15), arrowprops=dict(arrowstyle="<->"))
        ax1.text(-1.25, 0.975, f"f = {f.value:.2f} m", ha="right", va="center", fontsize=10)
        ax1.annotate("", xy=(-1.2, 0), xytext=(-1.2, 0.8), arrowprops=dict(arrowstyle="<->"))
        ax1.text(-1.25, 0.4, f"H = {H.value:.0f} km", ha="right", va="center", fontsize=10)
        ax1.set_title("G = p × H / f", fontsize=13)
        ax1.text(0, -0.22, f"row of {n_det:,} elements  →  swath S = {S:,.0f} km", ha="center", fontsize=11)
        # ---- right: Vaasa at that pixel size
        if G >= 10:
            k = min(30, max(1, int(round(G / 10))))
            ax2.imshow(coarse[k], interpolation="nearest")
            ax2.set_title(f"Vaasa centre, 3 km across, at {k*10:,} m pixels", fontsize=12)
        else:
            ax2.imshow(img, interpolation="nearest")
            ax2.set_title(f"Vaasa centre at 10 m (the data has no finer detail than this)", fontsize=12)
        ax2.set_xticks([]); ax2.set_yticks([])
        plt.tight_layout()
        out.clear_output(wait=True)
        with out:
            plt.show()
    for s in (H, f, p):
        s.observe(draw, names="value")
    draw()
    display(w.VBox([H, f, p, out]))


# ---------------------------------------------------------------- spectral probe
# Reference spectra of common surfaces, resampled to the Sentinel-2 bands. Same values as the Copernicus Browser
# spectral explorer (Sentinel Hub EO Browser, open source), derived from the USGS spectral library.
REFERENCE_SPECTRA = {
    "Water (open ocean)": ("#1f4ee0", [.0448, .0355, .025, .0206, .0203, .02, .0199, .0198, .0198, .0198, .0186, .0163]),
    "Grass":              ("#1a9c1a", [.0406, .0434, .1097, .0451, .172, .399, .4765, .4937, .5042, .4974, .3067, .1709]),
    "Soil (brown sand)":  ("#964B00", [.0522, .0847, .1496, .2154, .2328, .248, .2612, .2737, .2801, .3015, .402, .4028]),
    "Concrete":           ("#808080", [.2932, .3085, .3371, .3469, .3498, .3528, .3538, .3478, .3419, .3366, .304, .2221]),
    "Snow":               ("#000000", [.9838, .9852, .981, .9579, .9455, .9362, .9119, .8977, .8548, .7977, .0425, .0704]),
}


def spectral_probe(product="S2B_MSIL2A_20260621T101019_N0512_R022_T34VER_20260621T140048", width=560):
    """Click on the image to place numbered points; the reflectance of every band at each point is listed and
    drawn as a spectrum against wavelength, with the band names on the axis. Reference spectra of common surfaces
    can be switched on for comparison. Pure HTML and JavaScript, the band values are embedded (6 km around Vaasa)."""
    import base64, json, uuid
    import numpy as np
    from IPython.display import HTML, display
    d = _scene_dir(product)
    z = np.load(d / "spectral_cube_vaasa_6km.npz")
    cube, wl, names = z["cube"], z["wavelengths"].tolist(), z["names"].tolist()
    nb, ny, nx = cube.shape
    data = base64.b64encode(np.ascontiguousarray(cube).tobytes()).decode()
    img = "data:image/jpeg;base64," + base64.b64encode((d / "rgb_vaasa_6km.jpg").read_bytes()).decode()
    refs = [{"name": k, "color": c, "values": v} for k, (c, v) in REFERENCE_SPECTRA.items()]
    uid = "sp" + uuid.uuid4().hex[:8]
    checks = "".join(f'<label style="margin-right:12px;white-space:nowrap"><input type="checkbox" class="{uid}_ref" value="{i}">'
                     f'<span style="display:inline-block;width:10px;height:10px;background:{r["color"]};margin:0 4px 0 4px"></span>{r["name"]}</label>' for i, r in enumerate(refs))
    html = f"""
<div style="display:flex;gap:16px;flex-wrap:wrap;font:13px sans-serif">
 <div style="position:relative;width:{width}px">
  <img id="{uid}_img" src="{img}" style="width:{width}px;display:block;cursor:crosshair">
  <canvas id="{uid}_ov" width="{width}" height="{width}" style="position:absolute;left:0;top:0;pointer-events:none"></canvas>
  <div style="margin-top:4px">Sentinel-2 L2A, 21 June 2026, 6 km around Vaasa. Click to place a point. <button id="{uid}_clr">clear points</button></div>
 </div>
 <div style="flex:1;min-width:420px">
  <canvas id="{uid}_pl" width="520" height="340" style="border:1px solid #ccc;background:#fff"></canvas>
  <div style="margin:6px 0 2px 0">Compare with a known surface: {checks}</div>
  <div id="{uid}_tab" style="margin-top:6px;overflow-x:auto"></div>
 </div>
</div>
<script>
(function(){{
 const bin=atob("{data}"), n={nb}, ny={ny}, nx={nx};
 const cube=new Uint16Array(bin.length/2); for(let i=0;i<cube.length;i++) cube[i]=bin.charCodeAt(2*i)|(bin.charCodeAt(2*i+1)<<8);
 const wl={json.dumps(wl)}, names={json.dumps(names)}, refs={json.dumps(refs)};
 const img=document.getElementById("{uid}_img"), ov=document.getElementById("{uid}_ov"), pl=document.getElementById("{uid}_pl"), tab=document.getElementById("{uid}_tab");
 const colors=["#e6194b","#f58231","#911eb4","#42d4f4","#f032e6","#9a6324","#bfef45","#469990"];
 let pts=[];
 function spectrum(px,py){{ const col=Math.min(nx-1,Math.floor(px*nx)), row=Math.min(ny-1,Math.floor(py*ny)); const s=[]; for(let b=0;b<n;b++) s.push(cube[b*ny*nx+row*nx+col]/10000); return s; }}
 function activeRefs(){{ return [...document.querySelectorAll("."+"{uid}_ref")].filter(c=>c.checked).map(c=>refs[+c.value]); }}
 function draw(){{
  const W=ov.width=img.clientWidth, H=ov.height=img.clientHeight; const c=ov.getContext("2d"); c.clearRect(0,0,W,H);
  pts.forEach((p,i)=>{{ c.beginPath(); c.arc(p.x*W,p.y*H,7,0,6.28); c.fillStyle=colors[i%8]; c.fill(); c.strokeStyle="#fff"; c.lineWidth=2; c.stroke(); c.fillStyle="#fff"; c.font="bold 11px sans-serif"; c.textAlign="center"; c.fillText(i+1,p.x*W,p.y*H+4); }});
  const rf=activeRefs();
  const g=pl.getContext("2d"), L=50, R=12, T=12, B=40, w=pl.width-L-R, h=pl.height-T-B; g.clearRect(0,0,pl.width,pl.height);
  const all=[...pts.map(p=>Math.max(...p.s)), ...rf.map(r=>Math.max(...r.values))];
  const ymax=Math.max(0.1, ...all)*1.08;
  const X=v=>L+(v-420)/(2250-420)*w, Y=v=>T+h-v/ymax*h;
  g.strokeStyle="#888"; g.strokeRect(L,T,w,h);
  g.strokeStyle="#e4e4e4"; wl.forEach(v=>{{ g.beginPath(); g.moveTo(X(v),T); g.lineTo(X(v),T+h); g.stroke(); }});
  g.fillStyle="#333"; g.font="11px sans-serif"; g.textAlign="center";
  [500,1000,1500,2000].forEach(v=>{{ g.fillText(v,X(v),T+h+14); }}); g.fillText("wavelength (nm)",L+w/2,T+h+32);
  g.textAlign="right"; for(let k=0;k<=4;k++){{ const v=ymax*k/4; g.fillText(v.toFixed(2),L-4,Y(v)+4); }}
  g.save(); g.translate(12,T+h/2); g.rotate(-Math.PI/2); g.textAlign="center"; g.fillText("reflectance",0,0); g.restore();
  function line(vals,color,dash){{ g.strokeStyle=color; g.lineWidth=2; g.setLineDash(dash||[]); g.beginPath(); wl.forEach((v,j)=>{{ j?g.lineTo(X(v),Y(vals[j])):g.moveTo(X(v),Y(vals[j])); }}); g.stroke(); g.setLineDash([]); wl.forEach((v,j)=>{{ g.beginPath(); g.arc(X(v),Y(vals[j]),3,0,6.28); g.fillStyle=color; g.fill(); }}); }}
  rf.forEach(r=>line(r.values,r.color,[6,4]));
  pts.forEach((p,i)=>line(p.s,colors[i%8]));
  let t="<table style='border-collapse:collapse;font-size:12px'><tr><th style='text-align:left'>point</th>"+names.map(nm=>"<th style='padding:1px 5px'>"+nm+"</th>").join("")+"</tr>";
  pts.forEach((p,i)=>{{ t+="<tr><td style='color:"+colors[i%8]+";font-weight:bold'>"+(i+1)+"</td>"+p.s.map(v=>"<td style='padding:1px 5px;text-align:right'>"+v.toFixed(3)+"</td>").join("")+"</tr>"; }});
  rf.forEach(r=>{{ t+="<tr style='color:#666'><td style='color:"+r.color+";font-weight:bold'>"+r.name+"</td>"+r.values.map(v=>"<td style='padding:1px 5px;text-align:right'>"+v.toFixed(3)+"</td>").join("")+"</tr>"; }});
  tab.innerHTML=t+"</table>";
 }}
 img.addEventListener("click",e=>{{ const r=img.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width, y=(e.clientY-r.top)/r.height; pts.push({{x:x,y:y,s:spectrum(x,y)}}); draw(); }});
 document.getElementById("{uid}_clr").addEventListener("click",()=>{{ pts=[]; draw(); }});
 document.querySelectorAll("."+"{uid}_ref").forEach(c=>c.addEventListener("change",draw));
 img.complete?draw():img.addEventListener("load",draw);
}})();
</script>"""
    display(HTML(html))


# ---------------------------------------------------------------- change probe (two dates, shared points)
def change_probe(folder="hitachi_fire_2023", before="20230326", after="20230331", width=440,
                 titles=("26 March 2023, three days before the fire", "31 March 2023, two days after")):
    """Two images of the same place on two dates. Click once, the point appears on both, and the two spectra are
    drawn together. A menu chooses how the images are shown (true colour, false colour, one band, NBR, or the
    difference after minus before). Pure HTML and JavaScript, band values embedded (20 m grid)."""
    import base64, json, uuid
    import numpy as np
    from IPython.display import HTML, display
    d = SCENES / folder
    cubes, wl, names = [], None, None
    for tag in (before, after):
        z = np.load(d / f"spectral_cube_{tag}.npz"); cubes.append(z["cube"]); wl = z["wavelengths"].tolist(); names = z["names"].tolist()
    nb, ny, nx = cubes[0].shape
    data = [base64.b64encode(np.ascontiguousarray(c).tobytes()).decode() for c in cubes]
    uid = "cp" + uuid.uuid4().hex[:8]
    dates = (f"{before[6:]}.{before[4:6]}.{before[:4]}", f"{after[6:]}.{after[4:6]}.{after[:4]}")
    views = [("True colour (B04, B03, B02)", "tc"), ("NBR, normalised burn ratio (B08 − B12) / (B08 + B12)", "nbr"),
             ("Difference, after minus before, red band", "dred")]
    opts = "".join(f'<option value="{v}">{t}</option>' for t, v in views)
    html = f"""
<div style="font:13px sans-serif">
 <div style="margin-bottom:6px">Show: <select id="{uid}_view">{opts}</select> &nbsp; <button id="{uid}_clr">clear points</button></div>
 <div style="display:flex;gap:14px;flex-wrap:wrap">
  <div><div style="position:relative;width:{width}px"><canvas id="{uid}_c0" width="{width}" height="{width}" style="cursor:crosshair;display:block"></canvas><canvas id="{uid}_o0" width="{width}" height="{width}" style="position:absolute;left:0;top:0;pointer-events:none"></canvas></div><div id="{uid}_t0">{titles[0]}</div></div>
  <div><div style="position:relative;width:{width}px"><canvas id="{uid}_c1" width="{width}" height="{width}" style="cursor:crosshair;display:block"></canvas><canvas id="{uid}_o1" width="{width}" height="{width}" style="position:absolute;left:0;top:0;pointer-events:none"></canvas></div><div id="{uid}_t1">{titles[1]}</div></div>
  <div style="flex:1;min-width:380px"><canvas id="{uid}_pl" width="460" height="300" style="border:1px solid #ccc;background:#fff"></canvas><div style="color:#666;margin-top:4px">One colour per point. The solid line is the image on the left, the dashed line the image on the right.</div><div id="{uid}_tab" style="margin-top:6px;overflow-x:auto"></div></div>
 </div>
</div>
<script>
(function(){{
 const n={nb}, ny={ny}, nx={nx}, wl={json.dumps(wl)}, names={json.dumps(names)}, W={width};
 function dec(s){{ const b=atob(s), a=new Uint16Array(b.length/2); for(let i=0;i<a.length;i++) a[i]=b.charCodeAt(2*i)|(b.charCodeAt(2*i+1)<<8); return a; }}
 const cubes=[dec("{data[0]}"),dec("{data[1]}")];
 const bi={{}}; names.forEach((nm,i)=>bi[nm]=i);
 const band=(k,b,r,c)=>cubes[k][b*ny*nx+r*nx+c]/10000;
 const colors=["#e6194b","#f58231","#911eb4","#42d4f4","#f032e6","#9a6324","#bfef45","#469990"];
 const sel=document.getElementById("{uid}_view"), pl=document.getElementById("{uid}_pl"), tab=document.getElementById("{uid}_tab");
 const cv=[document.getElementById("{uid}_c0"),document.getElementById("{uid}_c1")], ov=[document.getElementById("{uid}_o0"),document.getElementById("{uid}_o1")];
 const tt=[document.getElementById("{uid}_t0"),document.getElementById("{uid}_t1")];
 const titles={json.dumps(list(titles))}, dates={json.dumps(list(dates))};
 let pts=[];
 function stretch(v,lo,hi){{ return Math.max(0,Math.min(255,Math.round((v-lo)/(hi-lo)*255))); }}
 function nbr(k,r,c){{ const a=band(k,bi.B08,r,c), b=band(k,bi.B12,r,c); return (a+b)>0?(a-b)/(a+b):0; }}
 function render(){{
  const v=sel.value;
  for(let k=0;k<2;k++){{
   const g=cv[k].getContext("2d"), im=g.createImageData(nx,ny);
   for(let r=0;r<ny;r++) for(let c=0;c<nx;c++){{
    let R,G,B; const i=(r*nx+c)*4;
    if(v==="tc"){{ R=stretch(band(k,bi.B04,r,c),0.02,0.9); G=stretch(band(k,bi.B03,r,c),0.02,0.9); B=stretch(band(k,bi.B02,r,c),0.02,0.9); }}
    else if(v==="fc"){{ R=stretch(band(k,bi.B08,r,c),0.02,0.9); G=stretch(band(k,bi.B04,r,c),0.02,0.9); B=stretch(band(k,bi.B03,r,c),0.02,0.9); }}
    else if(v==="b08"){{ R=G=B=stretch(band(k,bi.B08,r,c),0,0.9); }}
    else if(v==="b12"){{ R=G=B=stretch(band(k,bi.B12,r,c),0,0.5); }}
    else if(v==="nbr"){{ const x=nbr(k,r,c); R=stretch(-x,-1,1); G=stretch(x,-1,1); B=60; }}
    else {{ if(k===0){{ R=G=B=stretch(band(0,bi.B04,r,c),0.02,0.9); }} else {{ const x=band(1,bi.B04,r,c)-band(0,bi.B04,r,c); R=stretch(-x,-0.4,0.4); B=stretch(x,-0.4,0.4); G=stretch(0.4-Math.abs(x),0,0.4); }} }}
    im.data[i]=R; im.data[i+1]=G; im.data[i+2]=B; im.data[i+3]=255;
   }}
   const off=document.createElement("canvas"); off.width=nx; off.height=ny; off.getContext("2d").putImageData(im,0,0);
   g.imageSmoothingEnabled=false; g.clearRect(0,0,W,W); g.drawImage(off,0,0,W,W);
  }}
  tt[0].textContent=titles[0]; tt[1].textContent=(v==="dred")?"Red band, after minus before (red = darker after, blue = brighter after, green = no change)":titles[1];
  drawPoints();
 }}
 function drawPoints(){{
  for(let k=0;k<2;k++){{ const c=ov[k].getContext("2d"); c.clearRect(0,0,W,W); pts.forEach((p,i)=>{{ c.beginPath(); c.arc(p.x*W,p.y*W,7,0,6.28); c.fillStyle=colors[i%8]; c.fill(); c.strokeStyle="#fff"; c.lineWidth=2; c.stroke(); c.fillStyle="#fff"; c.font="bold 11px sans-serif"; c.textAlign="center"; c.fillText(i+1,p.x*W,p.y*W+4); }}); }}
  const g=pl.getContext("2d"), L=50, R=12, T=12, B=40, w=pl.width-L-R, h=pl.height-T-B; g.clearRect(0,0,pl.width,pl.height);
  const ymax=Math.max(0.1, ...pts.flatMap(p=>[...p.s0,...p.s1]))*1.08;
  const X=v=>L+(v-420)/(2250-420)*w, Y=v=>T+h-v/ymax*h;
  g.strokeStyle="#888"; g.strokeRect(L,T,w,h); g.fillStyle="#333"; g.font="11px sans-serif"; g.textAlign="center";
  [500,1000,1500,2000].forEach(v=>g.fillText(v,X(v),T+h+14)); g.fillText("wavelength (nm)",L+w/2,T+h+32);
  g.textAlign="right"; for(let k=0;k<=4;k++){{ const v=ymax*k/4; g.fillText(v.toFixed(2),L-4,Y(v)+4); }}
  g.save(); g.translate(12,T+h/2); g.rotate(-Math.PI/2); g.textAlign="center"; g.fillText("reflectance",0,0); g.restore();
  function line(vals,color,dash){{ g.strokeStyle=color; g.lineWidth=2; g.setLineDash(dash); g.beginPath(); wl.forEach((v,j)=>{{ j?g.lineTo(X(v),Y(vals[j])):g.moveTo(X(v),Y(vals[j])); }}); g.stroke(); g.setLineDash([]); }}
  pts.forEach((p,i)=>{{ line(p.s0,colors[i%8],[]); line(p.s1,colors[i%8],[6,4]); }});
  g.font="12px sans-serif"; g.textAlign="left"; g.fillStyle="#333";
  g.strokeStyle="#333"; g.lineWidth=2; g.setLineDash([]); g.beginPath(); g.moveTo(L+w-190,T+16); g.lineTo(L+w-160,T+16); g.stroke(); g.fillText(dates[0]+" (before)",L+w-152,T+20);
  g.setLineDash([6,4]); g.beginPath(); g.moveTo(L+w-190,T+34); g.lineTo(L+w-160,T+34); g.stroke(); g.setLineDash([]); g.fillText(dates[1]+" (after)",L+w-152,T+38);
  let t="<table style='border-collapse:collapse;font-size:12px'><tr><th style='text-align:left'>point</th>"+names.map(nm=>"<th style='padding:1px 5px'>"+nm+"</th>").join("")+"<th>NBR</th></tr>";
  pts.forEach((p,i)=>{{ const c=colors[i%8]; t+="<tr><td style='color:"+c+";font-weight:bold'>"+(i+1)+" before</td>"+p.s0.map(v=>"<td style='padding:1px 5px;text-align:right'>"+v.toFixed(3)+"</td>").join("")+"<td style='text-align:right'>"+p.n0.toFixed(2)+"</td></tr>"; t+="<tr><td style='color:"+c+";font-weight:bold'>"+(i+1)+" after</td>"+p.s1.map(v=>"<td style='padding:1px 5px;text-align:right'>"+v.toFixed(3)+"</td>").join("")+"<td style='text-align:right'>"+p.n1.toFixed(2)+"</td></tr>"; }});
  tab.innerHTML=t+"</table>";
 }}
 function click(e){{ const r=e.target.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width, y=(e.clientY-r.top)/r.height; const row=Math.min(ny-1,Math.floor(y*ny)), col=Math.min(nx-1,Math.floor(x*nx)); const s0=[],s1=[]; for(let b=0;b<n;b++){{ s0.push(band(0,b,row,col)); s1.push(band(1,b,row,col)); }} pts.push({{x:x,y:y,s0:s0,s1:s1,n0:nbr(0,row,col),n1:nbr(1,row,col)}}); drawPoints(); }}
 cv.forEach(c=>c.addEventListener("click",click));
 sel.addEventListener("change",render); document.getElementById("{uid}_clr").addEventListener("click",()=>{{ pts=[]; drawPoints(); }});
 render();
}})();
</script>"""
    display(HTML(html))


# ---------------------------------------------------------------- Sentinel matching task
SENTINELS = {
    "Sentinel-1":  ("radar backscatter from the surface, through cloud, day and night",
                    "https://dlmultimedia.esa.int/download/public/videos/2022/08/018/2208_018_BR_002.mp4"),
    "Sentinel-2":  ("reflected sunlight from the land surface, in visible and infrared bands, at fine detail",
                    "https://dlmultimedia.esa.int/download/public/videos/2022/08/018/2208_018_BR_004.mp4"),
    "Sentinel-3":  ("reflected sunlight and heat from the sea, over wide areas: ocean colour and temperature",
                    "https://dlmultimedia.esa.int/download/public/videos/2022/08/018/2208_018_BR_006.mp4"),
    "Sentinel-5P": ("trace gases in the atmosphere",
                    "https://dlmultimedia.esa.int/download/public/videos/2022/08/018/2208_018_BR_007.mp4"),
    "Sentinel-6":  ("height of the sea surface",
                    "https://dlmultimedia.esa.int/download/public/videos/2022/08/018/2208_018_BR_008.mp4"),
}


def sentinel_match():
    """Five Sentinels, five things they measure. Choose, press Check, fix the red ones.
    A correct row plays ESA's short animation of that satellite (streamed, nothing is downloaded until you press play)."""
    import ipywidgets as widgets
    from IPython.display import HTML, display
    choices = ["choose ..."] + sorted(v[0] for v in SENTINELS.values())
    rows, drops = [], {}
    for name in SENTINELS:
        drops[name] = widgets.Dropdown(options=choices, value=choices[0], layout=widgets.Layout(width="440px"))
        rows.append(widgets.HBox([widgets.HTML(f"<b style='display:inline-block;width:110px'>{name}</b>"), drops[name]]))
    button = widgets.Button(description="Check", button_style="primary")
    out = widgets.Output()
    def check(_):
        out.clear_output()
        with out:
            right = 0
            for name, (answer, clip) in SENTINELS.items():
                if drops[name].value == answer:
                    right += 1
                    display(HTML(f"<div style='color:#1a7f37;margin:4px 0'><b>{name}</b> ✓ {answer}</div>"
                                 f"<video controls preload='none' width='420' src='{clip}' style='margin:0 0 10px 110px'></video>"
                                 f"<div style='font-size:11px;color:#666;margin-left:110px'>ESA/ATG medialab</div>"))
                elif drops[name].value == choices[0]:
                    display(HTML(f"<div style='color:#666;margin:4px 0'><b>{name}</b> · not answered</div>"))
                else:
                    display(HTML(f"<div style='color:#b8336a;margin:4px 0'><b>{name}</b> ✗ try again</div>"))
            if right == len(SENTINELS):
                display(HTML("<p><b>All five.</b> Two of them record reflected sunlight, which is what a map of water colour needs. Keep that in mind for the next table.</p>"))
    button.on_click(check)
    display(widgets.VBox(rows + [button, out]))


# ---------------------------------------------------------------- product names
def parse_product_name(name):
    """Split a Sentinel-2 product name into its parts."""
    mission, level, sensing, baseline, orbit, tile, processed = name.split("_")[:7]
    fmt = "%Y%m%dT%H%M%S"
    parts = {
        "satellite": f"Sentinel-{mission[1:]}",
        "product level": level[3:],
        "sensing time (UTC)": datetime.strptime(sensing, fmt),
        "processing baseline": f"{baseline[1:3]}.{baseline[3:]}",
        "relative orbit": int(orbit[1:]),
        "tile": tile[1:],
        "processing time (UTC)": datetime.strptime(processed, fmt),
    }
    return pd.Series(parts, name=name).to_frame("value")


# ---------------------------------------------------------------- sun position
def sun_elevation(lat, lon, time_utc):
    """Sun elevation angle in degrees (NOAA approximation, accurate to about 0.1 deg)."""
    t = pd.Timestamp(time_utc)
    hour = t.hour + t.minute / 60 + t.second / 3600
    g = 2 * pi / 365 * (t.dayofyear - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * cos(g) + 0.070257 * sin(g) - 0.006758 * cos(2 * g)
            + 0.000907 * sin(2 * g) - 0.002697 * cos(3 * g) + 0.00148 * sin(3 * g))
    eqtime = 229.18 * (0.000075 + 0.001868 * cos(g) - 0.032077 * sin(g)
                       - 0.014615 * cos(2 * g) - 0.040849 * sin(2 * g))
    solar_minutes = hour * 60 + eqtime + 4 * lon
    hour_angle = radians(solar_minutes / 4 - 180)
    phi = radians(lat)
    return degrees(asin(sin(phi) * sin(decl) + cos(phi) * cos(decl) * cos(hour_angle)))


# ---------------------------------------------------------------- catalogue search
STAC_URL = "https://stac.dataspace.copernicus.eu/v1"      # Copernicus Data Space catalogue, no login needed


def search_scenes(lat, lon, date, max_cloud, level="L1C"):
    """Search the Copernicus STAC catalogue for Sentinel-2 products covering a point.

    date is one day ("2026-06-21") or a range ("2026-06-01/2026-06-30").
    Returns the products with cloud cover <= max_cloud, newest first.
    """
    from pystac_client import Client
    catalogue = Client.open(STAC_URL)
    search = catalogue.search(collections=[f"sentinel-2-{level.lower()}"],
                              intersects={"type": "Point", "coordinates": [lon, lat]},
                              datetime=date)
    rows = []
    for item in search.items():
        name = item.id.removesuffix(".SAFE")
        parts = name.split("_")
        rows.append({"product": name,
                     "satellite": f"Sentinel-{parts[0][1:]}",
                     "sensing time (UTC)": item.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                     "tile": parts[5][1:],
                     "relative orbit": int(parts[4][1:]),
                     "cloud cover %": item.properties.get("eo:cloud_cover")})
    found = pd.DataFrame(rows)
    if found.empty:
        print("No products found.")
        return found
    kept = found[found["cloud cover %"] <= max_cloud]
    print(f"{len(found)} products found, {len(kept)} with cloud cover <= {max_cloud} %.")
    return kept.sort_values("sensing time (UTC)", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- scene files on disk
# The prepared scenes live in data/scenes/<product name>/. The environment variable ICAT3370_SCENES
# can point to another folder.
SCENES = Path(os.environ.get("ICAT3370_SCENES", DATA / "scenes"))


def _scene_dir(product):
    d = SCENES / product
    if not d.is_dir():
        raise FileNotFoundError(f"Scene {product} is not in {SCENES}.")
    return d


def _band_file(product, band):
    """Band file of a product. L1C files are named B04.jp2, L2A files B04_10m.jp2 (finest resolution first)."""
    d = _scene_dir(product)
    for pattern in (f"{band}.jp2", f"{band}_10m.jp2", f"{band}_20m.jp2", f"{band}_60m.jp2"):
        if (d / pattern).exists():
            return d / pattern
    raise FileNotFoundError(f"Band {band} of {product} is not prepared.")


def _xml_values(path, tag):
    """All elements with this tag (namespaces ignored)."""
    from lxml import etree
    return etree.parse(str(path)).xpath(f"//*[local-name()='{tag}']")


# ---------------------------------------------------------------- product structure and metadata lines
def show_safe_structure(product):
    """Print the folder structure of a Sentinel-2 product as ESA distributes it (the .SAFE format).
    Structure from the Sentinel-2 Products Specification Document (ESA); the course folder holds the
    same files with shorter names."""
    level = product.split("_")[1][3:]
    tile = product.split("_")[5]
    sensing = product.split("_")[2]
    res = {"L2A": ["R10m/   T{t}_{s}_B02_10m.jp2  B03_10m  B04_10m  B08_10m  TCI_10m  AOT_10m  WVP_10m",
                   "R20m/   T{t}_{s}_B05_20m.jp2  B06 B07 B8A B11 B12  SCL_20m (scene classification)",
                   "R60m/   T{t}_{s}_B01_60m.jp2  B09_60m"],
           "L1C": ["T{t}_{s}_B01.jp2 … B12.jp2  (13 bands, one file each)  TCI.jpg"]}[level]
    lines = [f"{product}.SAFE/",
             f"├── MTD_MSI{level}.xml          product metadata (level, sensing time, baseline, cloud cover, scale factors)",
             "├── manifest.safe             list of every file in the product",
             "├── INSPIRE.xml               catalogue record",
             "├── GRANULE/",
             f"│   └── {level}_{tile}_A0…_{sensing[:8]}T…/",
             "│       ├── MTD_TL.xml        tile metadata (sun and view angles, map projection)",
             "│       ├── IMG_DATA/"] + [f"│       │   └── {r.format(t=tile[1:], s=sensing)}" for r in res] + [
             "│       └── QI_DATA/          cloud and quality masks",
             "├── DATASTRIP/                metadata of the whole strip the tile was cut from",
             "├── HTML/  rep_info/          human readable summary, XML schemas",
             f"└── {product}-ql.jpg   quick look"]
    print("\n".join(lines))


def print_metadata_lines(product, tags=("PROCESSING_LEVEL", "PRODUCT_START_TIME", "PROCESSING_BASELINE",
                                          "Cloud_Coverage_Assessment", "Mean_Sun_Angle")):
    """Print the lines of the two metadata files that carry the given tags, with their line numbers,
    so the values can be read in the raw XML."""
    d = _scene_dir(product)
    level = product.split("_")[1][3:]
    for name in (f"MTD_MSI{level}.xml", "MTD_TL.xml"):
        text = (d / name).read_text().splitlines()
        hits = [i for i, line in enumerate(text) if any(f"<{t}" in line for t in tags)]
        if not hits:
            continue
        print(f"===== {name}  ({len(text):,} lines) =====")
        for i in hits:
            span = range(i, min(i + 3, len(text))) if "Mean_Sun_Angle" in text[i] else [i]
            for j in span:
                print(f"{j+1:6d}  {text[j].rstrip()}")
        print()


# ---------------------------------------------------------------- metadata and pixels
class Metadata(dict):
    """A dictionary that shows itself as a readable table in the notebook."""

    def _repr_html_(self):
        rows = []
        for key, value in self.items():
            if isinstance(value, dict):   # per-band values: show them compactly
                value = ", ".join(f"{b}: {v:g}" for b, v in value.items())
            rows.append(f"<tr><td style='text-align:left'><b>{key}</b></td>"
                        f"<td style='text-align:left'>{value}</td></tr>")
        return "<table>" + "".join(rows) + "</table>"


def read_metadata(product):
    """Read the most important fields from the product (MTD_MSI*.xml) and tile (MTD_TL.xml) metadata."""
    d = _scene_dir(product)
    level = product.split("_")[1][3:]                    # L1C or L2A
    mtd = d / f"MTD_MSI{level}.xml"
    tl = d / "MTD_TL.xml"
    first = lambda path, tag: _xml_values(path, tag)[0].text

    # band_id in the XML is a number (0 = B01 ... 3 = B04 ... 7 = B08, 8 = B8A); translate to band names
    names = {int(e.get("bandId")): e.get("physicalBand").replace("B", "B0") if len(e.get("physicalBand")) == 2
             else e.get("physicalBand") for e in _xml_values(mtd, "Spectral_Information")}
    per_band = lambda tag: {names[int(e.get("band_id"))]: float(e.text) for e in _xml_values(mtd, tag)}

    view_zenith = [float(a.find("ZENITH_ANGLE").text) for a in _xml_values(tl, "Mean_Viewing_Incidence_Angle")]
    sun = _xml_values(tl, "Mean_Sun_Angle")[0]

    md = Metadata()
    md["product"] = product
    md["processing level"] = first(mtd, "PROCESSING_LEVEL")
    md["sensing time (UTC)"] = first(mtd, "PRODUCT_START_TIME")
    md["processing baseline"] = first(mtd, "PROCESSING_BASELINE")
    md["cloud cover %"] = round(float(first(mtd, "Cloud_Coverage_Assessment")), 2)
    md["MEAN_SUN_ZENITH"] = round(float(sun.find("ZENITH_ANGLE").text), 2)
    md["MEAN_SUN_AZIMUTH"] = round(float(sun.find("AZIMUTH_ANGLE").text), 2)
    md["mean viewing zenith"] = round(sum(view_zenith) / len(view_zenith), 2)
    md["coordinate system"] = first(tl, "HORIZONTAL_CS_CODE")
    if level == "L1C":
        md["QUANTIFICATION_VALUE"] = float(first(mtd, "QUANTIFICATION_VALUE"))
        md["RADIO_ADD_OFFSET"] = per_band("RADIO_ADD_OFFSET")
    else:
        md["BOA_QUANTIFICATION_VALUE"] = float(first(mtd, "BOA_QUANTIFICATION_VALUE"))
        md["BOA_ADD_OFFSET"] = per_band("BOA_ADD_OFFSET")
    return md


def _to_scene_xy(src, lat, lon):
    """Latitude/longitude to the map coordinates (UTM metres) of a band file."""
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", src.crs, always_xy=True).transform(lon, lat)


def pixel_dn(product, band, lat, lon):
    """The stored integer (digital number) of one pixel. 0 means 'no data'."""
    import rasterio
    with rasterio.open(_band_file(product, band)) as src:
        dn = int(next(src.sample([_to_scene_xy(src, lat, lon)]))[0])
    if dn == 0:
        print("Note: DN = 0 means 'no data' (outside the image), not a measurement.")
    return dn


def _scale(product):
    """Offset per band and scale value that turn DN into reflectance for this product."""
    md = read_metadata(product)
    if "RADIO_ADD_OFFSET" in md:
        return md["RADIO_ADD_OFFSET"], md["QUANTIFICATION_VALUE"]
    return md["BOA_ADD_OFFSET"], md["BOA_QUANTIFICATION_VALUE"]


# ---------------------------------------------------------------- images
AREA = (21.0, 63.045, 22.25, 63.45)      # Vaasa and Kvarken inside tile T34VER: west, south, east, north (degrees)


def _read_window(product, band, west, south, east, north, max_pixels=None):
    """Read a lat/lon box of one band. Returns array (bands, rows, cols) and extent in UTM metres."""
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds
    with rasterio.open(_band_file(product, band)) as src:
        corners = [_to_scene_xy(src, la, lo) for la in (south, north) for lo in (west, east)]
        xs, ys = zip(*corners)
        window = from_bounds(min(xs), min(ys), max(xs), max(ys), src.transform)
        window = window.round_offsets().round_lengths()
        try:                                                    # keep only the part inside the tile
            window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
        except rasterio.errors.WindowError:
            raise ValueError(f"The area {south:.2f}-{north:.2f} N, {west:.2f}-{east:.2f} E is outside this image "
                             f"(tile {product.split('_')[5][1:]}).") from None
        shape = (src.count, int(window.height), int(window.width))
        if max_pixels and max(shape[1:]) > max_pixels:          # decimate large areas for speed
            f = max(shape[1:]) / max_pixels
            shape = (src.count, int(shape[1] / f), int(shape[2] / f))
        data = src.read(window=window, out_shape=shape, resampling=Resampling.average, boundless=False)
        b = rasterio.windows.bounds(window, src.transform)
        return np.asarray(data), (b[0], b[2], b[1], b[3]), src.crs


def _graticule(ax, crs, west, south, east, north, step_lat=0.1, step_lon=0.2):
    """Draw latitude and longitude lines on a UTM image."""
    import numpy as np
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    dec = 1 if step_lat >= 0.1 else 2
    for lon in np.arange(np.ceil(west / step_lon) * step_lon, east, step_lon):
        x, y = tr.transform(np.full(50, lon), np.linspace(south - 0.1, north + 0.1, 50))
        ax.plot(x, y, color="white", lw=0.6, ls="--", alpha=0.6)
        xl = tr.transform(lon, south)[0]
        if x0 <= xl <= x1:
            ax.text(xl, y0, f"{lon:.{dec}f}°E", ha="center", va="top", fontsize=9)
    for lat in np.arange(np.ceil(south / step_lat) * step_lat, north, step_lat):
        x, y = tr.transform(np.linspace(west - 0.2, east + 0.2, 50), np.full(50, lat))
        ax.plot(x, y, color="white", lw=0.6, ls="--", alpha=0.6)
        yl = tr.transform(west, lat)[1]
        if y0 <= yl <= y1:
            ax.text(x0, yl, f"{lat:.{dec}f}°N ", ha="right", va="center", fontsize=9)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([])
    ax.set_yticks([])


def _mark_sites(ax, crs, sites, size=80):
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    for name, (lat, lon) in sites.items():
        x, y = tr.transform(lon, lat)
        ax.scatter(x, y, s=size, facecolors="none", edgecolors="yellow", linewidths=2)
        ax.annotate(name, (x, y), xytext=(8, 8), textcoords="offset points", color="yellow",
                    fontsize=11, fontweight="bold")


TCI_GAIN = 2.5      # the standard true-colour file is dark over water; brighten every image by the same factor


def show_true_colour(product, sites=None, area=AREA):
    """True-colour image (the product's TCI file) of the Vaasa area with the reference sites marked."""
    import numpy as np
    img, extent, crs = _read_window(product, "TCI", *area, max_pixels=1600)
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.imshow(np.clip(img.transpose(1, 2, 0) / 255 * TCI_GAIN, 0, 1), extent=extent)
    _graticule(ax, crs, *area)
    if sites:
        _mark_sites(ax, crs, sites)
    when = parse_product_name(product).loc["sensing time (UTC)", "value"]
    ax.set_title(f"True colour, {when:%d.%m.%Y %H:%M} UTC  (brightened x{TCI_GAIN})")
    plt.show()


def _reflectance(product, band, west, south, east, north):
    """Reflectance of a lat/lon box of one band (DN 0 = no data becomes NaN)."""
    import numpy as np
    offsets, scale = _scale(product)
    dn, extent, crs = _read_window(product, band, west, south, east, north)
    rho = (dn[0].astype(float) + offsets[band]) / scale
    rho[dn[0] == 0] = np.nan
    return rho, extent, crs


def _box(lat, lon, size_km):
    """Lat/lon box of about size_km x size_km around a point."""
    from math import cos, radians
    dlat = size_km / 2 / 111.2
    dlon = size_km / 2 / (111.2 * cos(radians(lat)))
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


ZOOM_STRETCH = 0.12     # reflectance shown as full brightness in the zooms (water is dark, so not 1.0)


def show_zooms(product, sites, size_km=2):
    """Close-up of each site at full 10 m resolution, all with the SAME brightness scale so they can be compared."""
    import numpy as np
    fig, axes = plt.subplots(1, len(sites), figsize=(4 * len(sites), 4.4))
    for ax, (name, (lat, lon)) in zip(np.atleast_1d(axes), sites.items()):
        box = _box(lat, lon, size_km)
        rgb = [_reflectance(product, b, *box) for b in ("B04", "B03", "B02")]
        extent, crs = rgb[0][1], rgb[0][2]
        img = np.clip(np.dstack([r[0] for r in rgb]) / ZOOM_STRETCH, 0, 1)
        ax.imshow(np.nan_to_num(img), extent=extent)
        _mark_sites(ax, crs, {"": (lat, lon)}, size=200)
        ax.set_title(f"{name}  ({size_km} km)")
        ax.set_xticks([])
        ax.set_yticks([])
    plt.tight_layout()
    fig.suptitle(f"Same brightness scale in every panel: white = reflectance {ZOOM_STRETCH} or more", fontsize=10, y=1.03)
    plt.show()


def _pixel_km(product, band):
    import rasterio
    with rasterio.open(_band_file(product, band)) as src:
        return src.res[0] / 1000


WAVELENGTH_NM = {"B01": 443, "B02": 490, "B03": 560, "B04": 665, "B05": 705, "B06": 740, "B07": 783,
                 "B08": 842, "B8A": 865, "B09": 945, "B11": 1610, "B12": 2190}


def site_reflectance(product, sites, bands, window=3):
    """Mean reflectance in a window x window pixel box at each site, as a table and a spectral plot.

    The mean of a few pixels is used instead of one pixel, so a single noisy pixel does not decide the result.
    """
    import numpy as np
    table = pd.DataFrame(index=list(sites), columns=bands, dtype=float)
    for name, (lat, lon) in sites.items():
        for band in bands:
            rho, _, _ = _reflectance(product, band, *_box(lat, lon, window * _pixel_km(product, band)))
            table.loc[name, band] = np.nanmean(rho)
    table = table.round(4)

    fig, ax = plt.subplots(figsize=(7, 4))
    x = [WAVELENGTH_NM[b] for b in bands]
    for name, row in table.iterrows():
        ax.plot(x, row.values, marker="o", label=name)
    ax.set_xticks(x, [f"{b}\n{w} nm" for b, w in zip(bands, x)])
    ax.set_ylabel("Reflectance")
    ax.set_title("Spectral signature of each site")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    plt.show()
    return table
