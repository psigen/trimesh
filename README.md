trimesh.py
==========

Python library for loading triangular meshes and doing simple operations on them. Included loaders are binary/ASCII STL and Wavefront (OBJ), included exporters are binary STL or COLLADA. If Assimp/pyassimp are available, meshes can be loaded using the assimp loaders. Note that this requires a version of the assimp python bindings from after September 2014. 

### Features
* Fast loading of binary STL files (on 234,230 face mesh, was 24.5x faster than assimp)
* Preview meshes (requires pyglet). 
* Calculate face adjacencies quickly (for the same 234,230 face mesh .248 s)
* Calculate cross sections (.146 s)
* Split mesh based on face connectivity, requires networkx (4.96 s) or graph-tool (.584 s)
* Calculate mass properties, including volume, center of mass, and moment of inertia (.246 s)
* Find planar facets (.454 s)
* Find and fix face normals and triangle winding (not fast or robust, 32.05 s)
* Find convex hulls of meshes (.21 s)
* Compute a rotation/translation invarient identifier for meshes
* Merge duplicate meshes, based off of identifier
* Determine if a mesh is watertight
* Repair single triangle and single quad holes
* Uniformly sample the surface of a mesh
* Numerous utility functions, such as transforming points, unitizing vectors, etc. 

### Installation:
The easiest way to install is:

    sudo pip install git+https://github.com/mikedh/trimesh.py.git

To get the latest version of assimp/pyassimp from github:

    sudo pip install git+https://github.com/robotics/assimp_latest.git 

### Example
    import numpy as np
    import trimesh
    
    # load_mesh can accept a filename or file object, 
    # however file objects require 'file_type' specified (eg. file_type='stl')
    # on load, does basic cleanup of mesh, including merging vertices 
    # and removing duplicate/degenerate faces
    mesh = trimesh.load_mesh('./models/unit_cube.STL')
    
    # split mesh based on connected components
    # by default this will only return watertight meshes, but the check can be disabled
    meshes = mesh.split() 

    # first component  
    m = meshes[0]

    # assign all faces a color
    m.generate_face_colors()

    # find groups of coplanar adjacent faces
    facets, facets_area = m.facets(return_area=True)

    # the largest group of faces by area    
    largest_facet = facets[np.argmax(facets_area)]

    # set all faces of the largest facet to a random color
    m.faces[largest_facet] = trimesh.color.random_color()

    # preview mesh in an opengl window
    m.show()
    

In the mesh view window, dragging rotates the view, ctl + drag pans, mouse wheel scrolls, 'z' returns to the base view, 'w' toggles wireframe mode, and 'c' toggles backface culling (useful if viewing non-watertight meshes).  