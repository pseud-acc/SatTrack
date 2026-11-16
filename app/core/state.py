#!/usr/bin/env python

"""

This module initialises app state data used in the app 

Example:

        $ python state.py

Functions:
    import_data: Import satellite data and earth map
    initialise_app_data: Run functions to initialise app
    get_app_data: Get cached app data
    clear_app_data_cache: Clear cached app data
Todo:
    *

"""
## Packages
import pandas as pd
import hashlib
import io
import json
import os
import sys
import numpy as np
from PIL import Image

## Internal Modules
sys.path.append("../../")
# user config
from app.config.user_setup_app import img_loc
# helper scripts
from app.helper.helper__constants import _resolution_3d_earth_map__c
from app.helper.helper__plot_display import (create_3d_layout, create_3d_surface, create_3d_figure, 
                                             create_2d_layout, create_2d_figure)
from app.helper.helper__table_display import create_table_mapping
from app.helper.helper__app_data import create_data_filters

# Global cache for app data (lazy initialization)
_app_data_cache = None

S3_APP_PREFIX = "app/"   # fixed: the pipeline's state script (infra/state/sattrack_state.py) publishes here


def read_app_csvs_from_s3(bucket):
    '''
    Read satellite and metadata csvs from the private S3 bucket (boto3, credentials from the environment:
    AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY, or AWS_PROFILE locally; region AWS_REGION, default eu-west-1).
    The pipeline writes app/current.json last; it names the exact object version and SHA-256 of each csv,
    so both files always come from the same run. Error text carries only the exception type, never keys.

    @param bucket: (str) bucket name (SATTRACK_S3_BUCKET, the same variable the pipeline uses)
    @return satcat, metadata: dataframes
    '''
    import boto3
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-west-1"
    client = boto3.client("s3", region_name=region)
    pointer_key = S3_APP_PREFIX + "current.json"
    try:
        pointer = json.loads(client.get_object(Bucket=bucket, Key=pointer_key)["Body"].read())
        print(f" - Data source: s3://{bucket}/{pointer_key} (region {region}), run {pointer.get('run_id')}, "
              f"published {pointer.get('published_at')}")
        frames = {}
        for name in ("satcat_tle.csv", "last_data_update.csv"):
            entry = pointer["files"][name]
            body = client.get_object(Bucket=bucket, Key=entry["key"], VersionId=entry["version_id"])["Body"].read()
            if hashlib.sha256(body).hexdigest() != entry["sha256"]:
                raise ValueError("checksum mismatch for " + name)
            frames[name] = pd.read_csv(io.BytesIO(body))
            print(f"   - s3://{bucket}/{entry['key']} version {entry['version_id']}: {len(body):,} bytes, "
                  f"{len(frames[name]):,} rows, sha256 ok")
    except Exception as exc:
        raise RuntimeError("Could not read app data from S3 (" + type(exc).__name__ + ")") from None
    return frames["satcat_tle.csv"], frames["last_data_update.csv"]

def read_app_csvs_from_dir(data_dir):
    '''
    Read satellite and metadata csvs from a local folder holding the pipeline's app files (satcat_tle.csv,
    last_data_update.csv): a downloaded copy of the bucket's app/ folder for local development, or the
    small committed sample in tests/app_data/ that CI runs the app with.

    @param data_dir: (str) folder (SATTRACK_APP_DATA_DIR)
    @return satcat, metadata: dataframes
    '''
    print(f" - Data source: local folder {data_dir}")
    frames = {}
    for name in ("satcat_tle.csv", "last_data_update.csv"):
        path = os.path.join(data_dir, name)
        frames[name] = pd.read_csv(path)
        print(f"   - {path}: {len(frames[name]):,} rows")
    return frames["satcat_tle.csv"], frames["last_data_update.csv"]

def import_app_data(img_loc, res):
    '''
    Import satellite data and earth map.

    Satellite data comes from the pipeline's app files (Space-Track + GCAT): the private S3 bucket when
    SATTRACK_S3_BUCKET is set (Heroku), otherwise the folder in SATTRACK_APP_DATA_DIR (local runs, CI).

    @param img_loc: static location of Earth map
    @param res: integer - Earth map resolution in increments of 2^x for integer x
    @return satcat:  dataframe of satellite data
    @return img_compr:  compressed image array of Earth map
    @return tle_metadata: last update time of the element sets
    @return data_source: 's3' or 'local'
    '''

    ## Satellite catalogue data - contains TLEs
    s3_bucket = os.environ.get("SATTRACK_S3_BUCKET")
    data_dir = os.environ.get("SATTRACK_APP_DATA_DIR")
    if s3_bucket:
        satcat, metadata = read_app_csvs_from_s3(s3_bucket)
        data_source = "s3"
    elif data_dir:
        satcat, metadata = read_app_csvs_from_dir(data_dir)
        data_source = "local"
    else:
        raise RuntimeError("No app data source: set SATTRACK_S3_BUCKET (the pipeline's S3 bucket) or "
                           "SATTRACK_APP_DATA_DIR (a folder with satcat_tle.csv and last_data_update.csv, "
                           "e.g. tests/app_data)")
    print("Satellite catalogue and TLE data successfully imported!")

    # Freshness of the element sets (Space-Track GP download)
    tle_metadata = metadata.loc[metadata["Source"] == "SpaceTrack_GP", "Last Update"].values[0]
    print("TLE metadata successfully imported!")    

    img = np.asarray(Image.open(img_loc))
    print("Earth Map successfully imported!")
    # url = 'https://raw.githubusercontent.com/pseud-acc/SatTrack/refs/heads/main/static/gray_scale_earth_2048_1024.jpg'
    # response = requests.get(url)
    # img = np.asarray(Image.open((BytesIO(response.content))))
    img = img.T
    # Compress image
    img_compr = img[0:-1:res,0:-1:res]

    return satcat, img_compr, tle_metadata, data_source

def initialise_app_data():
    '''
        Run functions to initialise app
    '''

    print("Initialising app data...")
    # Import data for visualisations
    df, img, tle_metadata, data_source = import_app_data(img_loc, _resolution_3d_earth_map__c)

    # Logging - to replace print w/ logging module later
    print(f" - Satellite catalogue size: {df.shape}")
    print(f" - Earth map size (compressed): {img.shape}")
    print(f" - TLE metadata: {tle_metadata}")
    print(f" - Data source: {data_source} (Space-Track + GCAT)")

    # Initialise Filters
    options, initial_filter = create_data_filters(df)

    # Initilise Visualisations
    surf_3d = create_3d_surface(img)
    layout_3d = create_3d_layout()
    figure_3d = create_3d_figure(layout_3d, surf_3d)
    layout_2d = create_2d_layout()
    figure_2d = create_2d_figure(layout_2d)

    # Define table column mapping
    tbl_column_map = create_table_mapping()

    # Store app data in dictionary
    app_data = dict()

    # Satellite Visualisation Data
    app_data['data'] = dict()
    app_data['data']['satcat_df'] = df
    app_data['data']['tle_metadata'] = tle_metadata
    app_data['data']['data_source'] = data_source  # 's3' or 'local'; both are the pipeline's Space-Track + GCAT files
    app_data['data']['tbl_col_map'] = tbl_column_map

    # Visualisation filters
    app_data['filter'] = dict()
    app_data['filter']['options'] = options
    app_data['filter']['initial_filter'] = initial_filter
    # 3D Visualisation
    app_data['viz_3d'] = dict()
    app_data['viz_3d']['surface'] = surf_3d
    app_data['viz_3d']['layout'] = layout_3d
    app_data['viz_3d']['base_figure'] = figure_3d
    # 2D Visualisation
    app_data['viz_2d'] = dict()
    app_data['viz_2d']['layout'] = layout_2d
    app_data['viz_2d']['base_figure'] = figure_2d

    return app_data

def get_app_data():
    """Lazy initialization singleton"""
    global _app_data_cache
    if _app_data_cache is None:
        _app_data_cache = initialise_app_data()
    return _app_data_cache

def clear_app_data_cache():
    """Force reinitialization (useful for testing or data reload)"""
    global _app_data_cache
    _app_data_cache = None
