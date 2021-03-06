import numpy as np
import time

import rtree.index as rtree

from ..constants       import *
from ..geometry        import unitize
from .ray_triangle_cpu import rays_triangles_id

class RayMeshIntersector:
    '''
    An object to query a mesh for ray intersections. 
    Precomputes an r-tree for each triangle on the mesh.
    '''
    def __init__(self, mesh):
        self.mesh = mesh

        # create triangles and tree from mesh only when requested,
        # rather than on initialization. 
        self._triangles = None
        self._tree      = None

    @property
    def triangles(self):
        '''
        A (n, 3, 3) array of triangle vertices
        Only created when requested.
        '''
        if self._triangles is None:
            self._triangles = self.mesh.vertices[self.mesh.faces]
        return self._triangles

    @property
    def tree(self):
        '''
        An r-tree that contains every triangle
        This is moderately expensive and can be reused,
        and is only created when requested
        '''

        if self._tree is None:
            self._tree = create_tree(self.triangles)
        return self._tree
            
    def intersects_location(self, rays, return_all=True):
        '''
        Find out whether the rays in question hit any triangle on the mesh.

        Arguments
        ---------
        rays: (n, 2, 3) array of ray origins and directions

        Returns
        ---------
        intersections: (n) sequence of triangle indexes
        '''
        pass

    def intersects_id(self, rays, return_any=False):
        '''
        Find the indexes of triangles the rays intersect

        Arguments
        ---------
        rays: (n, 2, 3) array of ray origins and directions

        Returns
        ---------
        
        intersections, return_any=True:
            (n) sequence of triangle indexes which hit the ray
        intersections, return_any=False:
            (n) boolean array of whether the ray hit *any* triangle

        
        '''
        ray_candidates = ray_triangle_candidates(rays = rays, 
                                                 tree = self.tree)
        intersections  = rays_triangles_id(triangles      = self.triangles, 
                                           rays           = rays, 
                                           ray_candidates = ray_candidates,
                                           return_any     = return_any)
        return intersections

    def intersects_any(self, rays):
        '''
        Find out whether the rays in question hit *any* triangle on the mesh.

        Arguments
        ---------
        rays: (n, 2, 3) array of ray origins and directions

        Returns
        ---------
        intersections: (n) boolean array of whether or not the ray hit a triangle
        '''
        return self.intersects_id(rays, return_any=True)

def ray_triangle_candidates(rays, triangles=None, tree=None):
    '''
    Do broad- phase search for triangles that the rays
    may intersect. 

    Does this by creating a bounding box for the ray as it 
    passes through the volume occupied by 
    '''
    if tree is None:
        tree = create_tree(triangles)

    ray_bounding   = ray_bounds(rays, tree.bounds)
    ray_candidates = [None] * len(rays)
    for ray_index, bounds in enumerate(ray_bounding):
        ray_candidates[ray_index] = list(tree.intersection(bounds))
    return ray_candidates

def create_tree(triangles):
    '''
    Given a set of triangles, create an r-tree for broad- phase 
    collision detection

    Arguments
    ---------
    triangles: (n, 3, 3) list of vertices

    Returns
    ---------
    tree: Rtree object 
    '''
  
    # the property object required to get a 3D r-tree index
    properties = rtree.Property()
    properties.dimension = 3
    # the (n,6) interleaved bounding box for every triangle
    tri_bounds = np.column_stack((triangles.min(axis=1), triangles.max(axis=1)))
  
    # stream loading wasn't getting proper index
    tree       = rtree.Index(properties=properties)  
    for i, bounds in enumerate(tri_bounds):
        tree.insert(i, bounds)
    
    return tree

def ray_bounds(rays, bounds, buffer_dist = 1e-5):
    '''
    Given a set of rays and a bounding box for the volume of interest
    where the rays will be passing through, find the bounding boxes 
    of the rays as they pass through the volume. 
    '''
    # separate out the (n, 2, 3) rays array into (n, 3) 
    # origin/direction arrays
    ray_ori    = rays[:,0,:]
    ray_dir = unitize(rays[:,1,:])

    # bounding box we are testing against
    bounds  = np.array(bounds)

    # find the primary axis of the vector
    axis       = np.abs(ray_dir).argmax(axis=1)
    axis_bound = bounds.reshape((2,-1)).T[axis]
    axis_ori   = np.array([ray_ori[i][a] for i, a in enumerate(axis)]).reshape((-1,1))
    axis_dir   = np.array([ray_dir[i][a] for i, a in enumerate(axis)]).reshape((-1,1))

    # parametric equation of a line
    # point = direction*t + origin
    # p = dt + o
    # t = (p-o)/d
    t = (axis_bound - axis_ori) / axis_dir

    # prevent the bounding box from including triangles
    # behind the ray origin
    t[t < buffer_dist] = buffer_dist

    # the value of t for both the upper and lower bounds
    t_a = t[:,0].reshape((-1,1))
    t_b = t[:,1].reshape((-1,1))

    # the cartesion point for where the line hits the plane defined by
    # axis
    on_a = (ray_dir * t_a) + ray_ori
    on_b = (ray_dir * t_b) + ray_ori

    on_plane = np.column_stack((on_a, on_b)).reshape((-1,2,ray_dir.shape[1]))
    
    ray_bounding = np.hstack((on_plane.min(axis=1), on_plane.max(axis=1)))
    # pad the bounding box by TOL_BUFFER
    # not sure if this is necessary, but if the ray is  axis aligned
    # this function will otherwise return zero volume bounding boxes
    # which may or may not screw up the r-tree intersection queries
    ray_bounding += np.array([-1,-1,-1,1,1,1]) * buffer_dist

    return ray_bounding
