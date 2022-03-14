# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration.  All Rights Reserved.

import h5py
import io
import numpy as np
import requests
import zipfile

datasets = ['DS01-005', 'DS02-006', 'DS03-012', 'DS04', 'DS05', 'DS06', 'DS07', 'DS08a-009', 'DS08c-008', 'DS08d-010']
cache = None

def load_data(dataset_id):
    """
    Loads data for one CMAPSS2 trajectory from NASA's PCoE Dataset
    https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/

    Args:
        dataset_id (int): Dataset id (see nasa_cmapss2.datasets)

    Raises:
        ValueError: Data not in dataset

    Returns:
        h5py.File: h5py file containing the data 

    Note:
        There is A LOT of data in this dataset, running load_data can take a while (especially on slower internet connections)
    """
    global cache

    if dataset_id not in datasets:
        raise ValueError("Invalid dataset id. Available datasets: {}".format(datasets))

    URL = "https://ti.arc.nasa.gov/c/47/"
    if cache is None:
        # Download data
        response = requests.get(URL, allow_redirects=True)

        # Unzip response
        cache = zipfile.ZipFile(io.BytesIO(response.content))

    # Read Files
    return h5py.File(cache.open(f'data_set/N-CMAPSS_{dataset_id}.h5', mode='r'))

def clear_cache():
    """
    Clears the cache of downloaded data
    """
    global cache
    cache = None
