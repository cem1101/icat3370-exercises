"""eo_tools.py, helper functions for ICAT3370 notebooks.

Students, you are welcome to read this file, but you are not expected to.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap
import rasterio
import rasterio.transform
from rasterio.windows import from_bounds
from rasterio.transform import rowcol
from rasterio.warp import reproject, Resampling, calculate_default_transform

# ----------------------------------------------------------------------
# Constants for the course study area
# ----------------------------------------------------------------------
STAC_URL = "https://paituli.csc.fi/geoserver/ogc/stac/v1"

# Vaasa search box, longitude and latitude (west, south, east, north)
VAASA_BBOX = [21.3, 62.9, 21.9, 63.3]

# 20 km window around Vaasa in the Sentinel-2 tile's own CRS, UTM 34N (EPSG:32634)
VAASA_UTM = (521000, 6991000, 541000, 7011000)

# The same window in ETRS-TM35FIN (EPSG:3067), used for Finnish national data
VAASA_TM35 = (220000, 6993000, 240000, 7013000)

# Reference sites, easting and northing in EPSG:32634 (checked on the 21 June 2026 image)
SITES = {
    "southern bay (plume)": (530005, 6995495),
    "harbour (Vaskiluoto)": (528285, 7000355),
    "open Kvarken":         (523035, 7008955),
}

# Our scene
SCENE_ID = "S2B_MSIL2A_20260621T101019_N0512_R022_T34VER_20260621T140048"


# ----------------------------------------------------------------------
# Finding and opening Sentinel-2 scenes
# ----------------------------------------------------------------------
def find_scenes(bbox=VAASA_BBOX, start="2026-06-01", end="2026-08-31", max_cloud=100,
                collection="sentinel2-l2a"):
    """Search Paituli STAC and return a table of scenes (date, tile, cloud, id) plus the items."""
    from pystac_client import Client
    catalog = Client.open(STAC_URL)
    search = catalog.search(collections=[collection], bbox=bbox, datetime=f"{start}/{end}")
    items = [it for it in search.items() if it.properties.get("eo:cloud_cover", 100) <= max_cloud]
    rows = [{"date": it.datetime.date(), "tile": it.id.split("_")[5][1:],
             "cloud": it.properties.get("eo:cloud_cover"), "id": it.id} for it in items]
    table = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    table.attrs["items"] = {it.id: it for it in items}
    return table


def get_scene(scene_id=SCENE_ID, table=None):
    """Return the STAC item for one scene id (searches the catalogue if no table is given)."""
    if table is None:
        table = find_scenes(start=scene_id[11:15] + "-01-01", end=scene_id[11:15] + "-12-31")
    items = table.attrs["items"]
    if scene_id not in items:
        raise ValueError(f"Scene {scene_id} not found")
    return items[scene_id]


def read_band(item, band, bounds=VAASA_UTM):
    """Read one L2A band over a window and return surface reflectance (0 to 1)."""
    with rasterio.open(item.assets[band].href) as src:
        a = src.read(1, window=from_bounds(*bounds, src.transform)).astype("float32")
    return (a - 1000) / 10000        # processing baseline 05.xx, offset 1000, scale 10000


def read_tci(item, bounds=VAASA_UTM, res="10m"):
    """Read the true colour image over a window (or the whole tile if bounds is None)."""
    with rasterio.open(item.assets[f"TCI_{res}"].href) as src:
        if bounds is None:
            rgb = src.read()
        else:
            rgb = src.read(window=from_bounds(*bounds, src.transform))
    return rgb.transpose(1, 2, 0)


# ----------------------------------------------------------------------
# Water quality
# ----------------------------------------------------------------------
def water_mask(green, red, nir, ndwi_min=-0.1, red_max=0.15):
    """True where a pixel is water (NDWI above threshold and not too bright in red)."""
    ndwi = (green - nir) / (green + nir + 1e-6)
    return (ndwi > ndwi_min) & (red < red_max)


def ndti(red, green):
    """Normalised difference turbidity index, (red minus green) over (red plus green)."""
    return (red - green) / (red + green + 1e-6)


def turbidity_nechad(red, mask, A=228.1, C=0.1641):
    """Turbidity in FNU from red reflectance, Nechad type single band formula, water pixels only.

    Coefficients are the red band values used in the Dogliotti and Nechad family of algorithms.
    They were calibrated in other waters, so the result is indicative, not certified.
    """
    out = np.full_like(red, np.nan)
    out[mask] = A * red[mask] / (1 - red[mask] / C)
    return out


def value_at_sites(arr, bounds=VAASA_UTM, sites=SITES, half=2):
    """Median of a small neighbourhood of `arr` at each site. Returns a dict name to value."""
    T = rasterio.transform.from_bounds(*bounds, arr.shape[1], arr.shape[0])
    result = {}
    for name, (e, n) in sites.items():
        r, c = rowcol(T, e, n)
        result[name] = float(np.nanmedian(arr[r - half:r + half + 1, c - half:c + half + 1]))
    return result


def plot_water_quality(tci, ndti_map, turb_map, mask, title=""):
    """Three panels, true colour, NDTI and turbidity, water pixels only in the index panels."""
    fig, ax = plt.subplots(1, 3, figsize=(19, 6))
    ax[0].imshow(tci); ax[0].set_title("True colour (TCI)")
    im1 = ax[1].imshow(np.where(mask, ndti_map, np.nan), cmap="YlOrBr", vmin=-0.4, vmax=0.2)
    ax[1].set_title("NDTI"); plt.colorbar(im1, ax=ax[1], shrink=0.8)
    im2 = ax[2].imshow(turb_map, cmap="YlOrBr", vmin=0, vmax=30)
    ax[2].set_title("Turbidity, Nechad formula (FNU)"); plt.colorbar(im2, ax=ax[2], shrink=0.8)
    for a in ax[1:]:
        a.set_facecolor("#dddddd")
    for a in ax:
        a.axis("off")
    plt.suptitle(title); plt.tight_layout(); plt.show()


# ----------------------------------------------------------------------
# Elevation model from the Roihu disk
# ----------------------------------------------------------------------
DEM10M = "/dataset/project_2019680/mml/dem10m/dem10m_direct.vrt"   # only on Roihu


def read_dem(bounds=VAASA_TM35, path=DEM10M):
    """Read a window of the NLS 10 m elevation model (EPSG:3067). Works only on Roihu."""
    with rasterio.open(path) as src:
        return src.read(1, window=from_bounds(*bounds, src.transform))


def to_latlon(arr, bounds, crs):
    """Reproject a 2-D array with bounds (xmin, ymin, xmax, ymax) in `crs` to EPSG:4326."""
    xmin, ymin, xmax, ymax = bounds
    src_t = rasterio.transform.from_bounds(xmin, ymin, xmax, ymax, arr.shape[1], arr.shape[0])
    dst_t, w, h = calculate_default_transform(crs, "EPSG:4326", arr.shape[1], arr.shape[0],
                                              left=xmin, bottom=ymin, right=xmax, top=ymax)
    out = np.zeros((h, w), dtype=arr.dtype)
    reproject(arr, out, src_transform=src_t, src_crs=crs,
              dst_transform=dst_t, dst_crs="EPSG:4326", resampling=Resampling.bilinear)
    west, north = dst_t.c, dst_t.f
    return out, (west, west + w * dst_t.a, north + h * dst_t.e, north)


def plot_dem_latlon(dem, bounds, crs, title="", vmax=50, vert_exag=15):
    """Shaded relief map of a DEM window with latitude and longitude axes and water in blue."""
    dem_ll, extent = to_latlon(dem, bounds, crs)
    land = np.ma.masked_less_equal(dem_ll, 0.05)
    shade = LightSource(azdeg=315, altdeg=35).hillshade(
        np.where(land.mask, 0, dem_ll), vert_exag=vert_exag, dx=10, dy=10)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.imshow(shade, cmap="gray", extent=extent, aspect="auto")
    im = ax.imshow(land, cmap="YlGn_r", alpha=0.55, extent=extent, vmin=0, vmax=vmax, aspect="auto")
    ax.imshow(np.where(land.mask, 1, np.nan), cmap=ListedColormap(["#a6cee3"]),
              extent=extent, aspect="auto")
    ax.set_aspect(1 / np.cos(np.deg2rad((extent[2] + extent[3]) / 2)))
    ax.set_xlabel("Longitude (degrees E)")
    ax.set_ylabel("Latitude (degrees N)")
    fig.colorbar(im, ax=ax, shrink=0.7, label="Elevation (m)")
    ax.set_title(title)
    plt.show()
