# -*- coding: utf-8 -*-

import getpass

import matplotlib.pyplot as plt
import requests
from osgeo import gdal

"""The most important module here is `requests`, we'll use this module to communicate with the WaPOR server.
`gdal` is used download a subset of the data to our local machine. 
`matplotlib` is used to have a look at the downloaded data. 
Finally, `getpass` is simply used to savely work with your API token.

## Requesting a WaPOR tif-file (Part 1)

Requesting a specific tif-file from the WaPOR server is done by specifying a URL and sending this URL to the server. 
There are three important variables in this URL, i.e. `workspace`, `cubecode` and `rasterid`. 
`workspace` defines which dataset we want to access, we'll leave that set to `WAPOR_2` for the rest of this workbook. 
`cubecode` defines which variable we are interested in, I'm setting it to `L1_AETI_A` for now, 
which stands for something like "Level 1 Actual Evapotranspiration Annual". 
Lastly, `rasterid` in this case allows us to specify for which year we are requesting data (2016 in this example).
"""

workspace = "WAPOR_2"
cubecode = "L1_AETI_A"
rasterid = "L1_AETI_16"

tif_request_url = f"https://io.apps.fao.org/gismgr/api/v1/download/{workspace}?requestType=MAPSET_RASTER&cubeCode={cubecode}&rasterId={rasterid}"
#
# """Using the `requests` module, we can send this request to the WaPOR server. """
# tif_request_response = requests.get(tif_request_url)
#
# """And we can check if the request was succesfull or not (⚠️ spoiler: it's not succesfull ⚠️)."""
# tif_request_response.raise_for_status()

"""We can't just request data like that, we need to include some authorization in that request. 
Let's prepare the authorization in the next part, before we come back to this request.
## Authorization
We are first going to send our API token to the server, let's start by storing the token in a variable.
"""

api_token = r'f0e760e0d7df3a909b854256f8ca68da5753a6e5c821c5caa37e65c81704e3d255d8250e2159b84a' #getpass.getpass("WaPOR API Token:")

"""Ok, now that we have a variable called `api_token`, we can communicate it to the server."""

authorization_request_url = "https://io.apps.fao.org/gismgr/api/v1/iam/sign-in"
authorization_headers = {"X-GISMGR-API-KEY": api_token}
authorization_request_response = requests.post(authorization_request_url, headers=authorization_headers)
authorization_request_response.raise_for_status()

"""And check what is in the response like this."""

authorization_request_response.json()

"""There are a couple of important things here. First, we see a `status` of 200, 
that's good (basically anything between 200 and 299 is good, 
see [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status) for more info). 
Then we see a `accessToken`, this is another (temporary) token which we can include with our request for data 
(the one that failed before). So lets save that `accessToken` to a variable.
"""

access_token = authorization_request_response.json()["response"]["accessToken"]

"""## Requesting a WaPOR tif-file (Part 2)
Now that we have this access token, we can include it with our previous failed request.
"""

tif_headers = {"Authorization": f"Bearer {access_token}"}
tif_request_response = requests.get(tif_request_url, headers=tif_headers)
tif_request_response.raise_for_status()

"""No error this time! 
Let's have a look at the response.
"""
tif_request_response.json()

"""Status is good (again), and now we see a new URL under `downloadUrl`. 
This is a direct link to the tif file we are interested in. 
You could stop reading the rest of this notebook and just past this URL in your browser and get the file.
However, this file is quite large (about 1.5GB) and perhaps you are only interested in a small part of it. 
Luckily for us, its not just any tif-file, but a [Cloud Optimized Geotiff](https://www.cogeo.org). 
In the next section, we'll see how we can download a small subset of this file using `gdal`. 
For now lets store the URL in a new variable.
"""

tif_url = tif_request_response.json()["response"]["downloadUrl"]

"""## Downloading a subset of a COG

Using the Python implementation of [gdal_translate](https://gdal.org/programs/gdal_translate.html) we can download a part of the file (the command line version would work as well ofcourse). We start by specifying a bounding-box, which bands (this particular file has only 1 band so it's an easy choice) of the Geotiff we want to have and where we want to store the downloaded file.
"""

bounding_box = [30.0, 30.5, 31.5, 28.5]  # left, top, right, bottom
bands = [1]
output_filepath = r"example_subset.tif"

"""Then we pass these variables to `gdal.TranslateOptions` (you can check out what other options are available by running `help(gdal.TranslateOptions)`, e.g. you can also create a netCDF file instead of a GeoTIFF or add a download progress bar)."""

translate_options = gdal.TranslateOptions(projWin=bounding_box, bandList=bands)

"""Next we can run `gdal.Translate`. 

> ⚠️ You'll see that we have to add a small string (`"/vsicurl/"`) in front of the URL we've found earlier, this is to tell `gdal` that we are not dealing with a normal local file, but with a file somewhere on a server (see [here](https://gdal.org/user/virtual_file_systems.html#gdal-virtual-file-systems-compressed-network-hosted-etc-vsimem-vsizip-vsitar-vsicurl) for more info).



"""

ds = gdal.Translate(output_filepath, f"/vsicurl/{tif_url}", options=translate_options)

"""That should finish in a couple of seconds, finally we can quickly create a simple plot to see if the data was really downloaded."""

array = ds.GetRasterBand(1).ReadAsArray()

plt.imshow(array)

"""Until now we have used only one specific `cubecode` and `rasterid`. Below I'll show how you can figure out what other valid values for them exist.

## Cubecodes

We can send a request to the WaPOR server asking it to tell us more about the valid values for `cubecode` like this.
"""

cubes_request_url = "https://io.apps.fao.org/gismgr/api/v1/catalog/workspaces/WAPOR_2/cubes"
cubes_request_response = requests.get(cubes_request_url)
cubes_request_response.raise_for_status()

"""And inspect the response like this."""

{x["code"]: x["caption"] for x in cubes_request_response.json()["response"]["items"]}

"""## RasterIDs

For a specific `cubecode`, we can ask which valid values for `rasterid` exist like this.
"""

cubecode = 'L1_NPP_D'
rasterid_request_url = f"https://io.apps.fao.org/gismgr/api/v1/catalog/workspaces/WAPOR_2/cubes/{cubecode}/rasters"
rasterid_request_response = requests.get(rasterid_request_url)
rasterid_request_response.raise_for_status()

"""And inspect the response."""

{x["rasterId"]: (x["DEKAD"]["caption"]) for x in rasterid_request_response.json()["response"]["items"]}