# Data Sample

## Input Data

The input data directory mimics the structure of our input S3 bucket. The application was designed to consume NetCDF file output from [Gridpoint Statistical Interpoliation (GSI) diagnostic files](https://web.archive.org/web/20240521023824/https://dtcenter.org/sites/default/files/community-code/gsi/docs/users-guide/html_v3.7/gsi_ch3.html#gsi-analysis-result-files-in-run-directory).

## App Data

This directory contains outlines of the Zarr data structure, a dump from our SQL database, and the outlines of the Parquet data structure.

- `app_data/s3_diag_zarr_inventory.*.txt` - a few files showing the bucket layout of the Zarr array in S3. One focus is on the general group structure, the other file is focused on data for a particular day. The full array was to big to preserve and it was difficult to extract a subset.
- `app_data/*.sql` - the SQL DB dump
- `app_data/HRRR_RTMA_.../...` - the parquet store with sample data

## Parquet Data Structure

We attempted to use Parquet tables to get around some limitations we were finding with Zarr arrays. The jury is still out if a tabular or array form is better for accessing the data. There's a chance our Zarr array was just too large (we only had one for all data) and we could have benefitted by creating numerous Zarr arrays with consolidated metadata.

```python
>>> import pyarrow.parquet as pq
>>> import pandas as pd
>>> parquet_table = pq.read_table('RTMA_HRRR_WCOSS_CONUS_REALTIME/t/loop=anl/0004ee89f24c4f4784f76d1384e23588-0.parquet')
>>> df = parquet_table.to_pandas()
>>> print(df)
nobs    observation  forecast_unadjusted  forecast_adjusted  obs_minus_forecast_unadjusted  obs_minus_forecast_adjusted   latitude   longitude  is_used initialization_time
0       226.350006           225.855835         225.855835                       0.494174                     0.494174  32.733002 -125.932999    False 2024-03-07 09:00:00
1       225.949997           226.027313         226.027313                      -0.077320                    -0.077320  32.910000 -125.223007    False 2024-03-07 09:00:00
2       226.149994           225.890976         225.890976                       0.259025                     0.259025  32.813000 -125.639999    False 2024-03-07 09:00:00
3       226.350006           225.801147         225.801147                       0.548863                     0.548863  32.715000 -126.057999    False 2024-03-07 09:00:00
4       226.550003           226.019058         226.019058                       0.530942                     0.530942  32.615002 -126.477005    False 2024-03-07 09:00:00
...            ...                  ...                ...                            ...                          ...        ...         ...      ...                 ...
73958   273.750000           273.555115         273.586578                       0.194870                     0.163422  46.250832  -63.334167     True 2024-03-07 09:00:00
73959   273.750000           273.594238         273.586578                       0.155760                     0.163422  46.250832  -63.334167     True 2024-03-07 09:00:00
73960   272.549988           273.157928         273.146973                      -0.607946                    -0.596997  46.299500  -63.176331     True 2024-03-07 09:00:00
73961   273.149994           273.147095         273.147003                       0.002895                     0.003003  46.299500  -63.176331     True 2024-03-07 09:00:00
73962   273.149994           273.060333         273.147003                       0.089654                     0.003003  46.299500  -63.176331     True 2024-03-07 09:00:00

[73963 rows x 9 columns]
>>> parquet_table = pq.read_table('RTMA_HRRR_WCOSS_CONUS_REALTIME/t/loop=anl/0019cd0014f94635aad5b82c4c4b7cb4-0.parquet')
>>> df = parquet_table.to_pandas()
>>> print(df)
nobs   observation  forecast_unadjusted  forecast_adjusted  obs_minus_forecast_unadjusted  obs_minus_forecast_adjusted   latitude   longitude  is_used initialization_time
0       226.449997           226.298874         226.298874                       0.151119                     0.151119  31.202000 -123.207993     True 2023-11-13 20:00:00
1       226.149994           226.220901         226.220901                      -0.070908                    -0.070908  31.150000 -123.460999     True 2023-11-13 20:00:00
2       225.949997           226.098465         226.098465                      -0.148462                    -0.148462  31.118999 -123.718002    False 2023-11-13 20:00:00
3       225.949997           226.062836         226.062836                      -0.112842                    -0.112842  31.118000 -123.742004     True 2023-11-13 20:00:00
4       226.149994           225.935959         225.935959                       0.214042                     0.214042  31.098000 -124.001999     True 2023-11-13 20:00:00
...            ...                  ...                ...                            ...                          ...        ...         ...      ...                 ...
92779   275.350006           275.182159         275.144073                       0.167840                     0.205931  46.250832  -63.334167     True 2023-11-13 20:00:00
92780   275.350006           275.256195         275.408539                       0.093802                    -0.058537  46.299500  -63.176331    False 2023-11-13 20:00:00
92781   275.350006           275.271393         275.408539                       0.078619                    -0.058537  46.299500  -63.176331    False 2023-11-13 20:00:00
92782   275.350006           275.271393         275.408539                       0.078619                    -0.058537  46.299500  -63.176331     True 2023-11-13 20:00:00
92783   274.850006           275.256195         275.408539                      -0.406198                    -0.558537  46.299500  -63.176331     True 2023-11-13 20:00:00
>>> parquet_table = pq.read_table('RTMA_HRRR_WCOSS_CONUS_REALTIME/t/loop=ges/001760e535744f958328694b4b0a68b3-0.parquet')
>>> pd = parquet_table.to_pandas()
>>> print(pd)
nobs   observation  forecast_unadjusted  forecast_adjusted  obs_minus_forecast_unadjusted  obs_minus_forecast_adjusted   latitude   longitude  is_used initialization_time
0       221.149994           220.868866         220.868866                       0.281134                     0.281134  35.980000 -125.253006    False 2024-04-23 14:00:00
1       220.149994           220.890320         220.890320                      -0.740329                    -0.740329  36.037998 -125.147003    False 2024-04-23 14:00:00
2       282.850006           282.224060         282.342255                       0.625944                     0.507754  46.143330 -131.089996    False 2024-04-23 14:00:00
3       282.950012           282.224060         282.342255                       0.725944                     0.607754  46.143330 -131.089996    False 2024-04-23 14:00:00
4       282.950012           282.224060         282.342255                       0.725944                     0.607754  46.143330 -131.089996    False 2024-04-23 14:00:00
...            ...                  ...                ...                            ...                          ...        ...         ...      ...                 ...
96622   278.750000           278.530273         279.071014                       0.219722                    -0.321001  46.250832  -63.334167    False 2024-04-23 14:00:00
96623   279.250000           278.215424         278.905365                       1.034572                     0.344643  46.299500  -63.176331    False 2024-04-23 14:00:00
96624   279.250000           278.215424         278.905365                       1.034572                     0.344643  46.299500  -63.176331    False 2024-04-23 14:00:00
96625   279.250000           278.197266         278.905365                       1.052734                     0.344643  46.299500  -63.176331    False 2024-04-23 14:00:00
96626   279.250000           278.215424         278.905365                       1.034572                     0.344643  46.299500  -63.176331    False 2024-04-23 14:00:00

[96627 rows x 9 columns]
```

## Zarr Data Structure

To give an idea of the shape of the data in a Zarr array:

```python
>>> import xarray
>>> import zarr
>>> ds = xarray.open_dataset("s3://osti-modeling-dev-rtma-vis-prod/diagnostics.zarr/RTMA/WCOSS/CONUS/HRRR/REALTIME/t/2024-09-18T00:00/anl/", engine="zarr")
>>> print(ds)
<xarray.Dataset> Size: 3MB
Dimensions:                        (nobs: 116004)
Coordinates:
    is_used                        (nobs) bool 116kB ...
    latitude                       (nobs) float32 464kB ...
    longitude                      (nobs) float32 464kB ...
Dimensions without coordinates: nobs
Data variables:
    forecast_adjusted              (nobs) float32 464kB ...
    forecast_unadjusted            (nobs) float32 464kB ...
    obs_minus_forecast_adjusted    (nobs) float32 464kB ...
    obs_minus_forecast_unadjusted  (nobs) float32 464kB ...
    observation                    (nobs) float32 464kB ...
Attributes:
    background:           HRRR
    domain:               CONUS
    frequency:            REALTIME
    initialization_time:  2024-09-18T00:00
    loop:                 anl
    model:                RTMA
    name:                 t
    system:               WCOSS
```

The "first guess" (ges) file has a similar structure.
