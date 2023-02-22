# -*- coding: utf-8 -*-

"""
Download WAPoR datasets from FAO repository

Date: 22/Feb/2023
Required inputs:
    WAPOR API Token (check :https://wapor.apps.fao.org/profile)
    Product name
    Coverage (Full scene or for bounding box)
Outputs:
    Geotiff file
"""

import os
import time

import requests
from osgeo import gdal

# Change here to your api token which can be generated from https://wapor.apps.fao.org/profile
api_token = r'enter-your-wapor-api-key'

# Globals
workspace = "WAPOR_2"
authorization_request_url = "https://io.apps.fao.org/gismgr/api/v1/iam/sign-in"
authorization_headers = {"X-GISMGR-API-KEY": api_token}
authorization_request_response = requests.post(authorization_request_url, headers=authorization_headers)
access_token = authorization_request_response.json()["response"]["accessToken"]
tif_headers = {"Authorization": f"Bearer {access_token}"}
#


def list_cubes():
    cubes_request_url = "https://io.apps.fao.org/gismgr/api/v1/catalog/workspaces/WAPOR_2/cubes"
    cubes_request_response = requests.get(cubes_request_url)
    inp_cubes_list = cubes_request_response.json()["response"]["items"]
    print("Please select appropriate code from list:")
    for x in inp_cubes_list:
        print(x["caption"],' : ', x["code"])


def download_data(cubecode, output_folder_name, coverage=False, bounding_box = [30.0, 30.5, 31.5, 28.5]):
    print("Checking available datasets for: ", cubecode)
    rasterid_request_url = f"https://io.apps.fao.org/gismgr/api/v1/catalog/workspaces/WAPOR_2/cubes/{cubecode}/rasters"

    rasterid_request_response = requests.get(rasterid_request_url)
    try:
        rasterid_request_response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        list_cubes()
        # if it wasn't a 200
        return "Error: " + str(e)

    # Code will continue if status was 200
    inp_cubecodes = rasterid_request_response.json()["response"]["items"]

    for x in inp_cubecodes:
        print("Exporting: ", x["rasterId"])
        rasterid = x["rasterId"]
        tif_request_url = f"https://io.apps.fao.org/gismgr/api/v1/download/{workspace}?requestType=MAPSET_RASTER&cubeCode={cubecode}&rasterId={rasterid}"
        tif_request_response = requests.get(tif_request_url, headers=tif_headers)
        try:
            tif_request_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return "Error: " + str(e)

        tif_url = tif_request_response.json()["response"]["downloadUrl"]
        bands = [1]
        output_filepath = os.path.join(output_folder_name, rasterid + ".tif")
        if coverage:
            print("Exporting for bounding box:", bounding_box)
            translate_options = gdal.TranslateOptions(projWin=bounding_box)  # , bandList=bands
            ds = gdal.Translate(output_filepath, f"/vsicurl/{tif_url}", options=translate_options)
        else:
            print("Exporting total data coverage")
            ds = gdal.Translate(output_filepath, f"/vsicurl/{tif_url}")

        time.sleep(10)  # Giving time for the gdal translate to process and save data
        # ds = None  #housekeeping to prevent mixing of data that is being exported. UNCOMMENT ONLY IF REQUIRED
    return "Exports Done"


if __name__ == '__main__':
    # # # Lists all available datasets
    # print(list_cubes())

    # # # Downloading individual datasets
    # Output folder absolute path
    outfolder = r'D:\output_Wapor_folder\test_folder'

    # if you don't know the code then please run print(list_cubes()) first and copy the specific data code from there.
    ccode = "L1_AETI_A"  # "L1_AETI_M"

    """
    If get_full_coverage is True then it will download whole scene (Arabia + Africa),then you don't need to modify b_box.
    
    If get_full_coverage is False then it will clip the raster for the b_box extent mentioned.  
    b_box parameter is mandatory otherwise it will clip to default b_box
    """
    get_full_coverage = True
    b_box = [30.0, 30.5, 31.5, 28.5]  # left, top, right, bottom

    output = download_data(cubecode=ccode, coverage=get_full_coverage, bounding_box=b_box, output_folder_name=outfolder)
    print("output")
