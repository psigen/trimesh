import numpy as np
import struct

from ..base import Trimesh
from ..constants import *
 
def load_stl(file_obj, file_type=None):
    if detect_binary_file(file_obj): return load_stl_binary(file_obj)
    else:                            return load_stl_ascii(file_obj)
        
def load_stl_binary(file_obj):
    '''
    Load a binary STL file into a trimesh object. 
    Uses a single main struct.unpack call, and is significantly faster
    than looping methods or ASCII STL. 
    '''
    # get the file_obj header
    header = file_obj.read(80)
    
    # get the file information about the number of triangles
    tri_count    = int(struct.unpack("@i", file_obj.read(4))[0])
    
    # now we check the length from the header versus the length of the file
    # data_start should always be position 84, but hard coding that felt ugly
    data_start = file_obj.tell()
    # this seeks to the end of the file (position 0, relative to the end of the file 'whence=2')
    file_obj.seek(0, 2)
    # we save the location of the end of the file and seek back to where we started from
    data_end = file_obj.tell()
    file_obj.seek(data_start)
    # the binary format has a rigidly defined structure, and if the length
    # of the file doesn't match the header, the loaded version is almost
    # certainly going to be garbage. 
    data_ok = (data_end - data_start) == (tri_count * 50)
   
    # this check is to see if this really is a binary STL file. 
    # if we don't do this and try to load a file that isn't structured properly 
    # the struct.unpack call uses 100% memory until the whole thing crashes, 
    # so it's much better to raise an exception here. 
    if not data_ok:
        raise NameError('Attempted to load binary STL with incorrect length in header!')
    
    # all of our vertices will be loaded in order due to the STL format, 
    # so faces are just sequential indices reshaped. 
    faces        = np.arange(tri_count*3).reshape((-1,3))

    # this blob extracts 12 float values, with 2 pad bytes per face
    # the first three floats are the face normal
    # the next 9 are the three vertices 
    blob = np.array(struct.unpack("<" + "12fxx"*tri_count, 
                                  file_obj.read())).reshape((-1,4,3))

    face_normals = blob[:,0]
    vertices     = blob[:,1:].reshape((-1,3))
    
    return Trimesh(vertices     = vertices,
                   faces        = faces, 
                   face_normals = face_normals)

def load_stl_ascii(file_obj):
    '''
    Load an ASCII STL file.
    
    Should be pretty robust to whitespace changes due to the use of split()
    '''
    
    header = file_obj.readline()
    blob   = np.array(file_obj.read().split())
    
    # there are 21 'words' in each face
    face_len     = 21
    face_count   = float(len(blob) - 1) / face_len
    if (face_count % 1) > TOL_ZERO:
        raise NameError('Incorrect number of values in STL file!')
    face_count   = int(face_count)
    # this offset is to be added to a fixed set of indices that is tiled
    offset       = face_len * np.arange(face_count).reshape((-1,1))
    # these hard coded indices will break if the exporter adds unexpected junk
    # but then it wouldn't really be an STL file... 
    normal_index = np.tile([2,3,4], (face_count, 1)) + offset
    vertex_index = np.tile([8,9,10,12,13,14,16,17,18], (face_count, 1)) + offset
    
    # faces are groups of three sequential vertices, as vertices are not references
    faces        = np.arange(face_count*3).reshape((-1,3))
    face_normals = blob[normal_index].astype(float)
    vertices     = blob[vertex_index.reshape((-1,3))].astype(float)
    
    return Trimesh(vertices     = vertices,
                   faces        = faces, 
                   face_normals = face_normals)

def detect_binary_file(file_obj):
    '''
    Returns True if file has non-ASCII characters (> 0x7F, or 127)
    Should work in both Python 2 and 3
    '''
    start  = file_obj.tell()
    fbytes = file_obj.read(1024)
    file_obj.seek(start)
    is_str = isinstance(fbytes, str)
    for fbyte in fbytes:
        if is_str: code = ord(fbyte)
        else:      code = fbyte
        if code > 127: return True
    return False

_stl_loaders = {'stl':load_stl}

