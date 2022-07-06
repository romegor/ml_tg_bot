from typing import Optional, List, Dict
import argparse
import os
from fastapi import FastAPI, Response
import uvicorn
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import base64
import io
from PIL import Image

from starlette.responses import StreamingResponse
import io

if 'ml_srv_port' in os.environ.keys():
    ml_srv_port = int(os.environ['ml_srv_port'])
else:
    ml_srv_port = 5001
if 'ml_srv_imgsize' in os.environ.keys():
    ml_srv_imgsize = int(os.environ['ml_srv_imgsize'])
else:
    ml_srv_imgsize = 384
if 'ml_srv_imgsize_cpu' in os.environ.keys():
    ml_srv_imgsize_cpu = int(os.environ['ml_srv_imgsize_cpu'])
else:
    ml_srv_imgsize_cpu = 224

class Payload(BaseModel):
    data: str = ""


import vgg16model as slow_model
model = slow_model.vgg16model(ml_srv_imgsize, ml_srv_imgsize_cpu)

import super_res_model
model_sr = super_res_model.sr_model()

app = FastAPI(docs_url=None, redoc_url=None, version="2022.01", title="ML service")
app.mount("/static", StaticFiles(directory="static"), name="static")

class SlowModelRequest(BaseModel):
    image1: Optional[str]
    image2: Optional[str]
    epoch: Optional[int]
    user_id: Optional[int]
class SuperResModelRequest(BaseModel):
    image: Optional[str]
    user_id: Optional[int]


# ----------------------------------------------
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )
@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Redoc",
        redoc_js_url="/static/redoc.standalone.js",
    )
# -----------------------------------------------

@app.post("/image_transform")
async def image_transform(data: SlowModelRequest):
    img_bytes_1 = base64.b64decode(data.image1.encode('utf-8'))
    img_bytes_2 = base64.b64decode(data.image2.encode('utf-8'))
    img1 = io.BytesIO(img_bytes_1)
    img2 = io.BytesIO(img_bytes_2)
    if data.epoch == None:
        data.epoch = 300
    res = model.image_transformation(img1,img2, data.epoch)
    res.seek(0)
    # return StreamingResponse(res, media_type="image/png")
    im_bytes = res.read()
    return {'magic_image':base64.b64encode(im_bytes).decode("utf8") }

@app.post("/image_superres")
async def image_transform(data: SuperResModelRequest):
    img_bytes_1 = base64.b64decode(data.image.encode('utf-8'))
    res = model_sr.get_sr_image(io.BytesIO(img_bytes_1))
    res.seek(0)
    im_bytes = res.read()
    return {'superres_image': base64.b64encode(im_bytes).decode("utf8") }

@app.post("/image_transform_hr")
async def image_transform(data: SlowModelRequest):
    img_bytes_1 = base64.b64decode(data.image1.encode('utf-8'))
    img_bytes_2 = base64.b64decode(data.image2.encode('utf-8'))
    img1 = io.BytesIO(img_bytes_1)
    img2 = io.BytesIO(img_bytes_2)
    if data.epoch == None:
        data.epoch = 300
    res = model.image_transformation(img1,img2, data.epoch)
    res.seek(0)
    # return StreamingResponse(res, media_type="image/png")
    im_bytes = res.read()
    res = model_sr.get_sr_image(io.BytesIO(im_bytes))
    res.seek(0)
    im_bytes = res.read()
    return {'magic_image':base64.b64encode(im_bytes).decode("utf8") }

@app.get("/")
async def try_connect():
    return {"ping": "True"}

if __name__ == "__main__":
    uvicorn.run("ml_server:app", host="0.0.0.0", port=ml_srv_port, log_level="info")
