# --- built in ---
import os
import io
import time
import uuid
import subprocess
from typing import List
# --- 3rd party ---
import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = 10000000000
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette.background import BackgroundTask
import starlette.status as status
# --- my module ---
import gen


app = FastAPI()

def remove_file_after_n_sec(sec: int, *paths: List[str]) -> None:
  time.sleep(sec)
  for path in paths:
    os.unlink(path)

@app.get("/")
async def redirect():
  return RedirectResponse("/upload")


@app.get(
  "/upload",
  responses = {
    200: {"content": {"text/html": {}}}
  },
  response_class=HTMLResponse)
async def upload_form():

  return HTMLResponse("""
  <!doctype html>
  <html lang="en">
    <head>
      <title>Secret Converter.</title>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootswatch@4.5.2/dist/darkly/bootstrap.min.css">
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
      <style>
        .jumbotron{ height: 100vh; }
        .navbar { margin-bottom: 0px; }

      </style>
    </head>
    <body>
      <div class="jumbotron text-center vertical-center">
        <h1>Secret Converter.</h1>
        <h5>Upload some images and to see what will happen....</h5>
        <div class="container">
          <form action="/api/upload" enctype="multipart/form-data" method="post" autocomplete="off">
            <div class="row justify-content-center">
              <div class="input-group col-md-4">
                <input class="form-control" type="file" id="file" name="file">
                <div class="input-group-append">
                  <button type="submit" class="btn btn-primary">Upload</button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </body>
  </html>
  """)


@app.post(
  "/api/upload",
  responses = {
    200: {"content": {"model/usd": {}}}
  },
  response_class=FileResponse)
async def upload_file(file: UploadFile):
  user_filename = os.path.basename(file.filename)
  user_filename = os.path.splitext(user_filename)[0]
  user_filename = user_filename[:10]
  user_filename = user_filename + '.usdz'

  image = PIL.Image.open(io.BytesIO(file.file.read()))

  width, height = image.size
  canvas = gen.gen_canvas(width=width, height=height)
  model_bytes = gen.gen_model(canvas, image)
  # save temporary glb files
  file_id = str( uuid.uuid4())
  glb_filename = file_id + '.glb'
  usd_filename = file_id + '.usdz'
  with open(glb_filename, 'wb') as f:
    f.write(model_bytes)
  subprocess.run(["usd_from_gltf", glb_filename, usd_filename])

  return RedirectResponse(
    f"/download/{file_id}",
    status_code=status.HTTP_302_FOUND,
    background = BackgroundTask(remove_file_after_n_sec, 60, glb_filename, usd_filename)
  )


@app.get('/download/{file_id}')
async def downloa_file(file_id: str):
  usd_filename = os.path.basename(file_id) + '.usdz'
  if os.path.isfile(usd_filename):
    return FileResponse(
      path = usd_filename,
      media_type = 'model/usd',
      filename = usd_filename
    )
  else:
    return {'error': 'file not found'}


if __name__ == '__main__':
  filename = 'megami2.jpg'
  image = PIL.Image.open(filename)
  width, height = image.size
  canvas = gen.gen_canvas(width=width, height=height)
  model = gen.gen_model(canvas, image)
  with open('mesh.glb', 'wb') as f:
    f.write(model)
