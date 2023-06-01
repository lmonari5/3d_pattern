import subprocess
import plotly
import numpy as np
from stl import mesh  # pip install numpy-stl
import plotly.graph_objects as go
import streamlit as st
import os
import time

def stl2mesh3d(stl_mesh):
    # stl_mesh is read by nympy-stl from a stl file; it is  an array of faces/triangles (i.e. three 3d points)
    # this function extracts the unique vertices and the lists I, J, K to define a Plotly mesh3d
    p, q, r = stl_mesh.vectors.shape #(p, 3, 3)
    # the array stl_mesh.vectors.reshape(p*q, r) can contain multiple copies of the same vertex;
    # extract unique vertices from all mesh triangles
    vertices, ixr = np.unique(stl_mesh.vectors.reshape(p*q, r), return_inverse=True, axis=0)
    I = np.take(ixr, [3*k for k in range(p)])
    J = np.take(ixr, [3*k+1 for k in range(p)])
    K = np.take(ixr, [3*k+2 for k in range(p)])
    return vertices, I, J, K

def figure_mesh(filename):
  my_mesh = mesh.Mesh.from_file(filename)
  vertices, I, J, K = stl2mesh3d(my_mesh)
  x, y, z = vertices.T
  colorscale= [[0, '#e5dee5'], [1, '#e5dee5']]
  mesh3D = go.Mesh3d(
              x=x,
              y=y,
              z=z,
              i=I,
              j=J,
              k=K,
              name='soap_dish_mesh',
              showscale=False,
              colorscale=colorscale, 
              intensity=z,
              flatshading=True,)
  title = "Soap dish mesh"
  layout = go.Layout(
              paper_bgcolor='rgb(1,1,1)',
              title_text=None,# title_x=0.5, font_color='white',
              width=800,
              height=800,
              scene_camera=dict(eye=dict(x=1.25, y=-1.25, z=1)),
              scene_xaxis_visible=False,
              scene_yaxis_visible=False,
              scene_zaxis_visible=False)
  fig = go.Figure(data=[mesh3D], layout=layout)

  fig.data[0].update(lighting=dict(ambient= 0.18,
                                   diffuse= 1,
                                   fresnel=  .1,
                                   specular= 1,
                                   roughness= .1,
                                   facenormalsepsilon=0))
  fig.data[0].update(lightposition=dict(x=3000,
                                        y=3000,
                                        z=10000));
  fig.update_scenes(aspectmode='data')
  fig.write_html("file_stl.html")
  return fig

if __name__ == "__main__":
    st.title('Soap Dish 3D Pattern')
    st.write('Generate a 3D model for a custom soap dish! You can find more information about the soap dish here on [Printables](https://www.printables.com/it/model/489136-geometric-soap-dish-holder-normal-with-plate-or-or).')
    cwd = os.getcwd() + os.sep
    if 'file.png' in os.listdir():
        os.remove('file.png')        
    if 'file.svg' in os.listdir():
        os.remove('file.svg')
    filetype = st.selectbox('Choose the file type', ['svg', 'png'])
    if filetype == 'png':
        st.write('The mesh generated from a png file is not always predictable')
    
    scale = st.checkbox('Rescale the x,y size of the image')
    scales = [0.25, 0.25]
    if scale:
        col1, col2 = st.columns(2)
        with col1:
            scales[0] = scales[0] * st.number_input('X scale %', min_value=0, value=100) / 100
        with col2:
            scales[1] = scales[1] * st.number_input('Y scale %', min_value=0, value=100) / 100

    uploaded_file = st.file_uploader("Upload the file:", type=[filetype])
    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        with open(f'{cwd}file.{filetype}', 'wb') as f:
            f.write(bytes_data)

        # convert the png to svg
        if filetype == 'png':
            subprocess.run(f'convert {cwd}file.png {cwd}file.pnm', shell = True)
            subprocess.run(f'potrace -s -o {cwd}file.svg {cwd}file.pnm', shell = True)
            subprocess.run(f'rm {cwd}file.pnm', shell = True)
        # resize the scale of the svg
        run_file = cwd + 'soap_dish_openscad.scad'
        if scale:
            run_file = cwd + 'soap_dish_openscad_scaled.scad'
            with open(f'{cwd}soap_dish_openscad.scad', 'r') as f:
                text = f.read()
            # replace scales in the openscad template
            text_replaced = text.replace('0.25', str(scales[0]), 1).replace('0.25', str(scales[1]), 1)
            with open(f'{cwd}soap_dish_openscad_scaled.scad', 'w') as f:
                f.write(text_replaced)
        st.write('The program renders with OpenScad, it takes a while. If you want to run it faster on your pc, check out the [Github page](https://github.com/lmonari5/soap_dish_3d_pattern.git).')
        if not st.button('Run'):
            st.stop()
        start = time.time()
        # run openscad
        with st.spinner('Rendering in progress...'):
            subprocess.run(f'openscad {run_file} -o {cwd}file.stl', shell = True)
        end = time.time()
        st.success(f'Rendered in {end-start} seconds', icon="✅")
        with open(f"{cwd}file.stl", "rb") as file:
          btn = st.download_button(
              label="Download mesh",
              data=file,
              file_name="soap_dish.stl",
              mime="model/stl"
          )
        st.write('Preview:')
        st.plotly_chart(figure_mesh(f'{cwd}file.stl'), use_container_width=True)
