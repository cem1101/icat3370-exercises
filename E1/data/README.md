# Course data

Two kinds of files live under `data/`, and only the first kind is in GitHub.

**Small files.** `missions.csv`, the metadata files of the 21 June 2026 scene (`MTD_MSIL2A.xml`, `MTD_TL.xml`, and the L1C pair), the compact spectral cubes and thumbnails used by the interactive cells (`spectral_cube_*.npz`, `rgb_*.jpg`), and the `hitachi_fire_2023` folder. About 4 MB in total. Exercise 1 needs nothing else.

**Large files, on CSC only, never in GitHub.** The full band files of the scenes (`*.jp2`, about 1 GB for the L1C and L2A pair), the 12 km all-band crops around Vaasa (`*_vaasa.tif`, 11 MB, used from Exercise 3), and the KOMPSAT-2 scene (`KO2_*.SIP.ZIP`, 350 MB). They are kept in the course project space on CSC and reached through the `ICAT3370_SCENES` environment variable that `helpers.py` reads; on a student's CSC session the course module sets it. Locally, set it to the folder that holds the scene directories.

Scene folders are named after the product, for example
`S2B_MSIL2A_20260621T101019_N0512_R022_T34VER_20260621T140048/`, and hold the band files with short names (`B04_10m.jp2`) next to the two metadata files.
