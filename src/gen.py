# --- built in ---
import os
from typing import List, Tuple, Dict, Sequence
# --- 3rd party ---
import numpy as np
import trimesh
import PIL.Image
# --- my module ---


def create_verts(
  width: float,
  height: float,
  thickness: float
) -> np.ndarray:
  """Create certices of cube

  # vertices of cube
  #
  #    1.+------+ 0
  #   .' |    .'|
  # 5+---+--+'4 |
  #  |   |  |   |
  #  | 3,+--+---+ 2
  #  |.'    | .'
  # 7+------+'6

  # AR quick look coordinate systems (facing -z)
  #
  #      ^ (+y)
  #      |
  #      |
  #      |
  #     ,+------> (+x)
  #   .'
  #  v (+z)

  Args:
    width (float): cube width
    height (float): cube height
    thickness (float): cube thickness

  Returns:
    np.ndarray: 8 vertices of cube
  """
  x = width/2
  y = height/2
  z = thickness/2

  return np.array([
    [ x,  y, -z],
    [-x,  y, -z],
    [ x, -y, -z],
    [-x, -y, -z],
    [ x,  y, z],
    [-x,  y, z],
    [ x, -y, z],
    [-x, -y, z],
  ], dtype=np.float32)

def create_cubefaces(
  vert8: np.ndarray
) -> List[trimesh.Trimesh]:
  face6 = np.array([
    # back (-z)
    0, 1, 2, 3,
    # front (+z)
    5, 4, 7, 6,
    # up (+y)
    1, 0, 5, 4,
    # bottom (-y)
    7, 6, 3, 2,
    # left (-x)
    1, 5, 3, 7,
    # right (+x)
    4, 0, 6, 2
  ], dtype=np.int64)

  face_normals = np.array([
    [0, 0, -1],
    [0, 0, 1],
    [0, 1, 0],
    [0, -1, 0],
    [-1, 0, 0],
    [1, 0, 0],
  ], dtype=np.float32)

  vert_uvs = np.array([
    [0, 1],
    [1, 1],
    [0, 0],
    [1, 0]
  ], dtype=np.float32)

  triangles = np.array([0, 2, 3, 0, 3, 1], dtype=np.int64)
  faces = []
  for i in range(6):
    vertices = []
    normals = []
    uvs = []
    for j in range(4):
      vertices.append(vert8[face6[i * 4 + j]])
      normals.append(face_normals[i])
      uvs.append(vert_uvs[j])
    faces.append(trimesh.Trimesh(
      vertices = vertices,
      faces = triangles,
      vertex_normals = normals,
      visual = trimesh.visual.TextureVisuals(
        uv = uvs
      )
    ))
  return faces

def create_cube(vert8: np.ndarray) -> trimesh.Trimesh:
  faces = create_cubefaces(vert8)
  cube = merge_meshes(faces)
  return cube

def merge_meshes(meshes: List[trimesh.Trimesh]) -> trimesh.Trimesh:
  vertice_list = [mesh.vertices for mesh in meshes]
  faces_list = [mesh.faces for mesh in meshes]
  normal_list = [mesh.vertex_normals for mesh in meshes]
  uv_list = [mesh.visual.uv for mesh in meshes]
  faces_offset = np.cumsum([v.shape[0] for v in vertice_list])
  faces_offset = np.insert(faces_offset, 0, 0)[:-1]

  vertices = np.vstack(vertice_list)
  faces = np.vstack([face + offset for face, offset in zip(faces_list, faces_offset)])
  normals = np.vstack(normal_list)
  uvs = np.vstack(uv_list)

  merged_meshes = trimesh.Trimesh(
    vertices = vertices,
    faces = faces,
    vertex_normals = normals
  )
  merged_meshes.visual = trimesh.visual.TextureVisuals(uv=uvs)
  return merged_meshes

def create_oneside_border(
  width: float,
  height: float,
  thickness: float
) -> trimesh.Trimesh:
  x = width/2
  y = height/2
  vert8 = create_verts(width, height, thickness)
  vert8[1, 1] += x*2
  vert8[3, 1] -= x*2
  vert8[5, 1] += x*2
  vert8[7, 1] -= x*2
  return create_cube(vert8)


def gen_canvas(
  width: int,
  height: int,
  canvas_height: float = 2.0,
  frame_width: float = 0.04,
  border_ratio: float = 0.08,
  frame_thickness: float = 0.08,
  back_thickness: float = 0.02,
  canvas_thickness: float = 0.4,
  glass_thickness: float = 0.1,
  back_offset: Tuple[int, int, int] = (0, 0, -0.02),
  canvas_offset: Tuple[int, int, int] = (0, 0, 0.01),
  glass_offset: Tuple[int, int, int] = (0, 0, 0.025),
  frame_color: Tuple[int, int, int, int] = (0.123, 0.0495, 0.0257, 1.0),
  back_color: Tuple[int, int, int, int] = (0.9, 0.9, 0.9, 1.0),
) -> Dict[str, trimesh.Trimesh]:
  assert width > 0 and height > 0
  aspect = width / height
  canvas_height
  canvas_width = canvas_height * aspect
  inner_height = canvas_height + border_ratio * canvas_height * 2
  inner_width = canvas_width + border_ratio * canvas_height * 2

  xoff = (frame_width + inner_width) / 2
  yoff = (frame_width + inner_height) / 2

  def transform(mesh, translate, axis, angle):
    rot = trimesh.transformations.rotation_matrix(
      np.deg2rad(angle), axis, point=mesh.centroid
    )
    mesh.apply_transform(rot)
    mesh.apply_translation(translate)
    return mesh

  z = [0, 0, 1]
  border1 = create_oneside_border(frame_width, inner_height, frame_thickness)
  border1 = transform(border1, [-xoff, 0, 0], z, 0)
  border2 = create_oneside_border(frame_width, inner_height, frame_thickness)
  border2 = transform(border2, [xoff, 0, 0], z, 180)
  border3 = create_oneside_border(frame_width, inner_width, frame_thickness)
  border3 = transform(border3, [0, yoff, 0], z, -90)
  border4 = create_oneside_border(frame_width, inner_width, frame_thickness)
  border4 = transform(border4, [0, -yoff, 0], z, 90)
  
  frame = merge_meshes([border1, border2, border3, border4])

  frame_mat = trimesh.visual.material.PBRMaterial('framemat')
  frame_mat.alphaMode = 'OPAQUE'
  frame_mat.baseColorFactor = (np.array(frame_color) * 255).astype(np.uint8)
  frame_mat.metallicFactor = 0.5
  frame_mat.roughnessFactor = 0.2

  frame.visual = trimesh.visual.TextureVisuals(
    uv = frame.visual.uv,
    material = frame_mat
  )

  # make back face
  back_face = create_cube(create_verts(inner_width, inner_height, frame_thickness * canvas_thickness))
  back_face.apply_translation(back_offset)
  back_mat = trimesh.visual.material.PBRMaterial('backmat')
  back_mat.alphaMode = 'OPAQUE'
  back_mat.baseColorFactor = (np.array(back_color) * 255).astype(np.uint8)
  back_mat.metallicFactor = 0.0
  back_mat.roughnessFactor = 0.5

  back_face.apply_translation(canvas_offset)
  back_face.visual = trimesh.visual.TextureVisuals(
    uv = back_face.visual.uv,
    material = back_mat
  )

  # make canvas
  canvas_faces = create_cubefaces(create_verts(canvas_width, canvas_height, frame_thickness * canvas_thickness))
  canvas_front = canvas_faces[1]
  canvas_faces.pop(1)
  canvas_side = merge_meshes(canvas_faces)
  canvas_side.apply_translation(canvas_offset)
  canvas_front.apply_translation(canvas_offset)

  canvas_mat = trimesh.visual.material.PBRMaterial('canvasmat')
  canvas_mat.alphaMode = 'OPAQUE'
  #canvas_mat.baseColorFactor = np.array([255, 255, 255], dtype=np.uint8)
  #canvas_mat.baseColorTexture = image
  canvas_mat.metallicFactor = 0.0
  canvas_mat.roughnessFactor = 1.0
  #canvas_mat.emissiveFactor = np.array((0.1, 0.1, 0.1))

  canvas_side.visual = trimesh.visual.TextureVisuals(
    uv = canvas_side.visual.uv,
    material = back_mat
  )

  canvas_front.visual = trimesh.visual.TextureVisuals(
    uv = canvas_front.visual.uv,
    material = canvas_mat
  )

  glass = create_cube(create_verts(inner_width, inner_height, frame_thickness * glass_thickness))
  glass.apply_translation(glass_offset)

  glass_mat = trimesh.visual.material.PBRMaterial('glassmat')
  glass_mat.alphaMode = 'BLEND'
  glass_mat.baseColorFactor = np.array([255, 255, 255, 20], dtype=np.uint8)
  glass_mat.metallicFactor = 0.2
  glass_mat.roughnessFactor = 0.0
  
  glass.visual = trimesh.visual.TextureVisuals(
    uv = glass.visual.uv,
    material = glass_mat
  )

  return dict(
    frame = frame,
    back_face = back_face,
    canvas_side = canvas_side,
    canvas_front = canvas_front,
    glass = glass
  )

def gen_model(
  canvas: Dict,
  image: PIL.Image,
  canvas_front_key='canvas_front'
) -> Sequence[bytes]:
  scene = trimesh.Scene()
  # apply image
  canvas[canvas_front_key].visual.material.baseColorTexture = image

  for key, obj in canvas.items():
    scene.add_geometry(obj)

  return trimesh.exchange.gltf.export_glb(scene, include_normals=True)
