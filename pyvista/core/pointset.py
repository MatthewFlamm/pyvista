"""Sub-classes for vtk.vtkPolyData."""
import logging
import os

import numpy as np
import vtk
from vtk import (VTK_HEXAHEDRON, VTK_PYRAMID, VTK_QUAD,
                 VTK_QUADRATIC_HEXAHEDRON, VTK_QUADRATIC_PYRAMID,
                 VTK_QUADRATIC_QUAD, VTK_QUADRATIC_TETRA,
                 VTK_QUADRATIC_TRIANGLE, VTK_QUADRATIC_WEDGE, VTK_TETRA,
                 VTK_TRIANGLE, VTK_WEDGE, vtkPolyData, vtkStructuredGrid,
                 vtkUnstructuredGrid)
from vtk.util.numpy_support import (numpy_to_vtk, numpy_to_vtkIdTypeArray,
                                    vtk_to_numpy)

import pyvista
from pyvista.utilities.fileio import set_vtkwriter_mode
from .common import DataSet
from .filters import PolyDataFilters, UnstructuredGridFilters
from ..utilities.fileio import get_ext

log = logging.getLogger(__name__)
log.setLevel('CRITICAL')


class PointSet(DataSet):
    """PyVista's equivalent of vtk.vtkPointSet.

    This holds methods common to PolyData and UnstructuredGrid.
    """

    def center_of_mass(self, scalars_weight=False):
        """Return the coordinates for the center of mass of the mesh.

        Parameters
        ----------
        scalars_weight : bool, optional
            Flag for using the mesh scalars as weights. Defaults to False.

        Return
        ------
        center : np.ndarray, float
            Coordinates for the center of mass.

        """
        alg = vtk.vtkCenterOfMass()
        alg.SetInputDataObject(self)
        alg.SetUseScalarsAsWeights(scalars_weight)
        alg.Update()
        return np.array(alg.GetCenter())


    def shallow_copy(self, to_copy):
        """Do a shallow copy the pointset."""
        # Set default points if needed
        if not to_copy.GetPoints():
            to_copy.SetPoints(vtk.vtkPoints())
        return DataSet.shallow_copy(self, to_copy)


class PolyData(vtkPolyData, PointSet, PolyDataFilters):
    """Extend the functionality of a vtk.vtkPolyData object.

    Can be initialized in several ways:

    - Create an empty mesh
    - Initialize from a vtk.vtkPolyData
    - Using vertices
    - Using vertices and faces
    - From a file

    Examples
    --------
    >>> import pyvista
    >>> from pyvista import examples
    >>> import vtk
    >>> import numpy as np

    >>> surf = pyvista.PolyData()  # Create an empty mesh

    >>> # Initialize from a vtk.vtkPolyData object
    >>> vtkobj = vtk.vtkPolyData()
    >>> surf = pyvista.PolyData(vtkobj)

    >>> # initialize from just vertices
    >>> vertices = np.array([[0, 0, 0], [1, 0, 0], [1, 0.5, 0], [0, 0.5, 0],])
    >>> surf = pyvista.PolyData(vertices)

    >>> # initialize from vertices and faces
    >>> faces = np.hstack([[3, 0, 1, 2], [3, 0, 3, 2]]).astype(np.int8)
    >>> surf = pyvista.PolyData(vertices, faces)

    >>>  # initialize from a filename
    >>> surf = pyvista.PolyData(examples.antfile)

    """

    _vtk_readers = {'.ply': vtk.vtkPLYReader, '.stl': vtk.vtkSTLReader, '.vtk': vtk.vtkPolyDataReader,
                    '.vtp': vtk.vtkXMLPolyDataReader, '.obj': vtk.vtkOBJReader}
    _vtk_writers = {'.ply': vtk.vtkPLYWriter, '.vtp': vtk.vtkXMLPolyDataWriter, '.stl': vtk.vtkSTLWriter,
                    '.vtk': vtk.vtkPolyDataWriter}

    def __init__(self, *args, **kwargs):
        """Initialize the polydata."""
        super(PolyData, self).__init__()

        deep = kwargs.pop('deep', False)

        if not args:
            return
        elif len(args) == 1:
            if isinstance(args[0], vtk.vtkPolyData):
                if deep:
                    self.deep_copy(args[0])
                else:
                    self.shallow_copy(args[0])
            elif isinstance(args[0], str):
                self._load_file(args[0])
            elif isinstance(args[0], np.ndarray):
                points = args[0]
                if points.ndim != 2:
                    points = points.reshape((-1, 3))
                cells = self._make_vertice_cells(points.shape[0])
                self._from_arrays(points, cells, deep, verts=True)
            else:
                raise TypeError('Invalid input type')

        elif len(args) == 2:
            if all(isinstance(arg, np.ndarray) for arg in args):
                self._from_arrays(vertices=args[0], faces=args[1], deep=deep)
            else:
                raise TypeError('Invalid input type')
        else:
            raise TypeError('Invalid input type')

        # Check if need to make vertex cells
        if self.n_points > 0 and self.n_cells == 0:
            # make vertex cells
            self.faces = self._make_vertice_cells(self.n_points)

    def __repr__(self):
        """Return the standard representation."""
        return DataSet.__repr__(self)

    def __str__(self):
        """Return the standard str representation."""
        return DataSet.__str__(self)

    @staticmethod
    def _make_vertice_cells(npoints):
        cells = np.hstack((np.ones((npoints, 1)),
                           np.arange(npoints).reshape(-1, 1)))
        cells = np.ascontiguousarray(cells, dtype=pyvista.ID_TYPE)
        cells = np.reshape(cells, (2*npoints))
        return cells

    @property
    def lines(self):
        """Return a pointer to the lines as a numpy object."""
        return vtk_to_numpy(self.GetLines().GetData())

    @lines.setter
    def lines(self, lines):
        """Set the lines of the polydata."""
        if lines.dtype != pyvista.ID_TYPE:
            lines = lines.astype(pyvista.ID_TYPE)

        # get number of lines
        if lines.ndim == 1:
            log.debug('efficiency warning')
            c = 0
            nlines = 0
            while c < lines.size:
                c += lines[c] + 1
                nlines += 1
        else:
            nlines = lines.shape[0]

        vtkcells = vtk.vtkCellArray()
        vtkcells.SetCells(nlines, numpy_to_vtkIdTypeArray(lines, deep=False))
        self.SetLines(vtkcells)

    @property
    def faces(self):
        """Return a pointer to the points as a numpy object."""
        return vtk_to_numpy(self.GetPolys().GetData())

    @faces.setter
    def faces(self, faces):
        """Set faces without copying."""
        if faces.dtype != pyvista.ID_TYPE:
            faces = faces.astype(pyvista.ID_TYPE)

        # get number of faces
        if faces.ndim == 1:
            log.debug('efficiency warning')
            c = 0
            nfaces = 0
            while c < faces.size:
                c += faces[c] + 1
                nfaces += 1
        else:
            nfaces = faces.shape[0]

        vtkcells = vtk.vtkCellArray()
        vtkcells.SetCells(nfaces, numpy_to_vtkIdTypeArray(faces, deep=False))
        if faces.ndim > 1 and faces.shape[1] == 2:
            self.SetVerts(vtkcells)
        else:
            self.SetPolys(vtkcells)
        self._face_ref = faces
        self.Modified()

    # @property
    # def lines(self):
    #     """ returns a copy of the indices of the lines """
    #     lines = vtk_to_numpy(self.GetLines().GetData()).reshape((-1, 3))
    #     return np.ascontiguousarray(lines[:, 1:])


    def is_all_triangles(self):
        """Return True if all the faces of the polydata are triangles."""
        return self.faces.size % 4 == 0 and (self.faces.reshape(-1, 4)[:, 0] == 3).all()

    def _from_arrays(self, vertices, faces, deep=True, verts=False):
        """Set polygons and points from numpy arrays.

        Parameters
        ----------
        vertices : np.ndarray of dtype=np.float32 or np.float64
            Vertex array.  3D points.

        faces : np.ndarray of dtype=np.int64
            Face index array.  Faces can contain any number of points.

        Examples
        --------
        >>> import numpy as np
        >>> import pyvista
        >>> vertices = np.array([[0, 0, 0],
        ...                      [1, 0, 0],
        ...                      [1, 1, 0],
        ...                      [0, 1, 0],
        ...                      [0.5, 0.5, 1]])
        >>> faces = np.hstack([[4, 0, 1, 2, 3],
        ...                    [3, 0, 1, 4],
        ...                    [3, 1, 2, 4]])  # one square and two triangles
        >>> surf = pyvista.PolyData(vertices, faces)

        """
        if deep or verts:
            vtkpoints = vtk.vtkPoints()
            vtkpoints.SetData(numpy_to_vtk(vertices, deep=deep))
            self.SetPoints(vtkpoints)

            # Convert to a vtk array
            vtkcells = vtk.vtkCellArray()
            if faces.dtype != pyvista.ID_TYPE:
                faces = faces.astype(pyvista.ID_TYPE)

            # get number of faces
            if faces.ndim == 1:
                c = 0
                nfaces = 0
                while c < faces.size:
                    c += faces[c] + 1
                    nfaces += 1
            else:
                nfaces = faces.shape[0]

            idarr = numpy_to_vtkIdTypeArray(faces.ravel(), deep=deep)
            vtkcells.SetCells(nfaces, idarr)
            if (faces.ndim > 1 and faces.shape[1] == 2) or verts:
                self.SetVerts(vtkcells)
            else:
                self.SetPolys(vtkcells)
        else:
            self.points = vertices
            self.faces = faces

    def __sub__(self, cutting_mesh):
        """Subtract two meshes."""
        return self.boolean_cut(cutting_mesh)

    @property
    def n_faces(self):
        """Return the number of cells.

        Alias for ``n_cells``.

        """
        return self.n_cells

    @property
    def number_of_faces(self):
        """Return the number of cells."""
        return self.n_cells


    def save(self, filename, binary=True):
        """Write a surface mesh to disk.

        Written file may be an ASCII or binary ply, stl, or vtk mesh
        file. If ply or stl format is chosen, the face normals are
        computed in place to ensure the mesh is properly saved.

        Parameters
        ----------
        filename : str
            Filename of mesh to be written.  File type is inferred from
            the extension of the filename unless overridden with
            ftype.  Can be one of the following types (.ply, .stl,
            .vtk)

        binary : bool, optional
            Writes the file as binary when True and ASCII when False.

        Notes
        -----
        Binary files write much faster than ASCII and have a smaller
         file size.

        """
        filename = os.path.abspath(os.path.expanduser(filename))
        ftype = get_ext(filename)
        # Recompute normals prior to save.  Corrects a bug were some
        # triangular meshes are not saved correctly
        if ftype in ['stl', 'ply']:
            self.compute_normals(inplace=True)
        super().save(filename, binary)


    @property
    def area(self):
        """Return the mesh surface area.

        Return
        ------
        area : float
            Total area of the mesh.

        """
        mprop = vtk.vtkMassProperties()
        mprop.SetInputData(self)
        return mprop.GetSurfaceArea()

    @property
    def volume(self):
        """Return the mesh volume.

        This will throw a VTK error/warning if not a closed surface

        Return
        ------
        volume : float
            Total volume of the mesh.

        """
        mprop = vtk.vtkMassProperties()
        mprop.SetInputData(self.triangulate())
        return mprop.GetVolume()


    @property
    def point_normals(self):
        """Return the point normals."""
        mesh = self.compute_normals(cell_normals=False, inplace=False)
        return mesh.point_arrays['Normals']


    @property
    def cell_normals(self):
        """Return the cell normals."""
        mesh = self.compute_normals(point_normals=False, inplace=False)
        return mesh.cell_arrays['Normals']


    @property
    def face_normals(self):
        """Return the cell normals."""
        return self.cell_normals


    @property
    def obbTree(self):
        """Return the obbTree of the polydata.

        An obbTree is an object to generate oriented bounding box (OBB)
        trees. An oriented bounding box is a bounding box that does not
        necessarily line up along coordinate axes. The OBB tree is a
        hierarchical tree structure of such boxes, where deeper levels of OBB
        confine smaller regions of space.
        """
        if not hasattr(self, '_obbTree'):
            self._obbTree = vtk.vtkOBBTree()
            self._obbTree.SetDataSet(self)
            self._obbTree.BuildLocator()

        return self._obbTree


    @property
    def n_open_edges(self):
        """Return the number of open edges on this mesh."""
        alg = vtk.vtkFeatureEdges()
        alg.FeatureEdgesOff()
        alg.BoundaryEdgesOn()
        alg.NonManifoldEdgesOn()
        alg.SetInputDataObject(self)
        alg.Update()
        return alg.GetOutput().GetNumberOfCells()


class PointGrid(PointSet):
    """Class in common with structured and unstructured grids."""

    def __new__(cls, *args, **kwargs):
        """Allocate memory for the point grid."""
        if cls is PointGrid:
            raise TypeError("pyvista.PointGrid is an abstract class and may not be instantiated.")
        return object.__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        """Initialize the point grid."""
        super(PointGrid, self).__init__()

    def plot_curvature(self, curv_type='mean', **kwargs):
        """Plot the curvature of the external surface of the grid.

        Parameters
        ----------
        curv_type : str, optional
            One of the following strings indicating curvature types

            - mean
            - gaussian
            - maximum
            - minimum

        **kwargs : optional
            Optional keyword arguments.  See help(pyvista.plot)

        Return
        ------
        cpos : list
            Camera position, focal point, and view up.  Used for storing and
            setting camera view.

        """
        trisurf = self.extract_surface().triangulate()
        return trisurf.plot_curvature(curv_type, **kwargs)

    @property
    def volume(self):
        """Compute the volume of the point grid.

        This extracts the external surface and computes the interior volume
        """
        surf = self.extract_surface().triangulate()
        return surf.volume



class UnstructuredGrid(vtkUnstructuredGrid, PointGrid, UnstructuredGridFilters):
    """
    Extends the functionality of a vtk.vtkUnstructuredGrid object.

    Can be initialized by the following:

    - Creating an empty grid
    - From a vtk.vtkPolyData object
    - From cell, offset, and node arrays
    - From a file

    Examples
    --------
    >>> import pyvista
    >>> from pyvista import examples
    >>> import vtk

    >>> # Create an empty grid
    >>> grid = pyvista.UnstructuredGrid()

    >>> # Copy a vtkUnstructuredGrid
    >>> vtkgrid = vtk.vtkUnstructuredGrid()
    >>> grid = pyvista.UnstructuredGrid(vtkgrid)  # Initialize from a vtkUnstructuredGrid

    >>> # from arrays
    >>> #grid = pyvista.UnstructuredGrid(offset, cells, cell_type, nodes, deep=True)

    >>> # From a string filename
    >>> grid = pyvista.UnstructuredGrid(examples.hexbeamfile)

    """

    _vtk_readers = {'.vtu': vtk.vtkXMLUnstructuredGridReader, '.vtk': vtk.vtkUnstructuredGridReader}
    _vtk_writers = {'.vtu': vtk.vtkXMLUnstructuredGridWriter, '.vtk': vtk.vtkUnstructuredGridWriter}

    def __init__(self, *args, **kwargs):
        """Initialize the unstructured grid."""
        super(UnstructuredGrid, self).__init__()
        deep = kwargs.pop('deep', False)

        if len(args) == 1:
            if isinstance(args[0], vtk.vtkUnstructuredGrid):
                if deep:
                    self.deep_copy(args[0])
                else:
                    self.shallow_copy(args[0])

            elif isinstance(args[0], str):
                self._load_file(args[0])

            elif isinstance(args[0], vtk.vtkStructuredGrid):
                vtkappend = vtk.vtkAppendFilter()
                vtkappend.AddInputData(args[0])
                vtkappend.Update()
                self.shallow_copy(vtkappend.GetOutput())

            else:
                raise Exception('Cannot work with input type %s' % type(args[0]))

        elif len(args) == 4:
            if all(isinstance(arg, np.ndarray) for arg in args):
                self._from_arrays(*args, deep=deep)
            else:
                raise Exception('All input types must be np.ndarray')


    def __repr__(self):
        """Return the standard representation."""
        return DataSet.__repr__(self)


    def __str__(self):
        """Return the standard str representation."""
        return DataSet.__str__(self)


    def _from_arrays(self, offset, cells, cell_type, points, deep=True):
        """Create VTK unstructured grid from numpy arrays.

        Parameters
        ----------
        offset : np.ndarray dtype=np.int64
            Array indicating the start location of each cell in the cells
            array.

        cells : np.ndarray dtype=np.int64
            Array of cells.  Each cell contains the number of points in the
            cell and the node numbers of the cell.

        cell_type : np.uint8
            Cell types of each cell.  Each cell type numbers can be found from
            vtk documentation.  See example below.

        points : np.ndarray
            Numpy array containing point locations.

        Examples
        --------
        >>> import numpy
        >>> import vtk
        >>> import pyvista
        >>> offset = np.array([0, 9])
        >>> cells = np.array([8, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11, 12, 13, 14, 15])
        >>> cell_type = np.array([vtk.VTK_HEXAHEDRON, vtk.VTK_HEXAHEDRON], np.int8)

        >>> cell1 = np.array([[0, 0, 0],
        ...                   [1, 0, 0],
        ...                   [1, 1, 0],
        ...                   [0, 1, 0],
        ...                   [0, 0, 1],
        ...                   [1, 0, 1],
        ...                   [1, 1, 1],
        ...                   [0, 1, 1]])

        >>> cell2 = np.array([[0, 0, 2],
        ...                   [1, 0, 2],
        ...                   [1, 1, 2],
        ...                   [0, 1, 2],
        ...                   [0, 0, 3],
        ...                   [1, 0, 3],
        ...                   [1, 1, 3],
        ...                   [0, 1, 3]])

        >>> points = np.vstack((cell1, cell2))

        >>> grid = pyvista.UnstructuredGrid(offset, cells, cell_type, points)

        """
        if offset.dtype != pyvista.ID_TYPE:
            offset = offset.astype(pyvista.ID_TYPE)

        if cells.dtype != pyvista.ID_TYPE:
            cells = cells.astype(pyvista.ID_TYPE)

        if not cells.flags['C_CONTIGUOUS']:
            cells = np.ascontiguousarray(cells)

        # if cells.ndim != 1:
        # cells = cells.ravel()

        if cell_type.dtype != np.uint8:
            cell_type = cell_type.astype(np.uint8)

        # Get number of cells
        ncells = cell_type.size

        # Convert to vtk arrays
        cell_type = numpy_to_vtk(cell_type, deep=deep)
        offset = numpy_to_vtkIdTypeArray(offset, deep=deep)

        vtkcells = vtk.vtkCellArray()
        vtkcells.SetCells(ncells, numpy_to_vtkIdTypeArray(cells.ravel(), deep=deep))

        # Convert points to vtkPoints object
        points = pyvista.vtk_points(points, deep=deep)

        # Create unstructured grid
        self.SetPoints(points)
        self.SetCells(cell_type, offset, vtkcells)

    @property
    def cells(self):
        """Return a pointer to the cells as a numpy object."""
        return vtk_to_numpy(self.GetCells().GetData())

    def linear_copy(self, deep=False):
        """Return a copy of the unstructured grid containing only linear cells.

        Converts the following cell types to their linear equivalents.

        - VTK_QUADRATIC_TETRA      --> VTK_TETRA
        - VTK_QUADRATIC_PYRAMID    --> VTK_PYRAMID
        - VTK_QUADRATIC_WEDGE      --> VTK_WEDGE
        - VTK_QUADRATIC_HEXAHEDRON --> VTK_HEXAHEDRON

        Parameters
        ----------
        deep : bool
            When True, makes a copy of the points array.  Default
            False.  Cells and cell types are always copied.

        Return
        ------
        grid : pyvista.UnstructuredGrid
            UnstructuredGrid containing only linear cells.

        """
        lgrid = self.copy(deep)

        # grab the vtk object
        vtk_cell_type = numpy_to_vtk(self.GetCellTypesArray(), deep=True)
        celltype = vtk_to_numpy(vtk_cell_type)
        celltype[celltype == VTK_QUADRATIC_TETRA] = VTK_TETRA
        celltype[celltype == VTK_QUADRATIC_PYRAMID] = VTK_PYRAMID
        celltype[celltype == VTK_QUADRATIC_WEDGE] = VTK_WEDGE
        celltype[celltype == VTK_QUADRATIC_HEXAHEDRON] = VTK_HEXAHEDRON

        # track quad mask for later
        quad_quad_mask = celltype == VTK_QUADRATIC_QUAD
        celltype[quad_quad_mask] = VTK_QUAD

        quad_tri_mask = celltype == VTK_QUADRATIC_TRIANGLE
        celltype[quad_tri_mask] = VTK_TRIANGLE

        vtk_offset = self.GetCellLocationsArray()
        cells = vtk.vtkCellArray()
        cells.DeepCopy(self.GetCells())
        lgrid.SetCells(vtk_cell_type, vtk_offset, cells)

        # fixing bug with display of quad cells
        if np.any(quad_quad_mask):
            quad_offset = lgrid.offset[quad_quad_mask]
            base_point = lgrid.cells[quad_offset + 1]
            lgrid.cells[quad_offset + 5] = base_point
            lgrid.cells[quad_offset + 6] = base_point
            lgrid.cells[quad_offset + 7] = base_point
            lgrid.cells[quad_offset + 8] = base_point

        if np.any(quad_tri_mask):
            tri_offset = lgrid.offset[quad_tri_mask]
            base_point = lgrid.cells[tri_offset + 1]
            lgrid.cells[tri_offset + 4] = base_point
            lgrid.cells[tri_offset + 5] = base_point
            lgrid.cells[tri_offset + 6] = base_point

        return lgrid

    @property
    def celltypes(self):
        """Get the cell types array."""
        return vtk_to_numpy(self.GetCellTypesArray())

    @property
    def offset(self):
        """Get Cell Locations Array."""
        return vtk_to_numpy(self.GetCellLocationsArray())



class StructuredGrid(vtkStructuredGrid, PointGrid):
    """Extend the functionality of a vtk.vtkStructuredGrid object.

    Can be initialized in several ways:

    - Create empty grid
    - Initialize from a vtk.vtkStructuredGrid object
    - Initialize directly from the point arrays

    See _from_arrays in the documentation for more details on initializing
    from point arrays

    Examples
    --------
    >>> import pyvista
    >>> import vtk
    >>> import numpy as np

    >>> # Create empty grid
    >>> grid = pyvista.StructuredGrid()

    >>> # Initialize from a vtk.vtkStructuredGrid object
    >>> vtkgrid = vtk.vtkStructuredGrid()
    >>> grid = pyvista.StructuredGrid(vtkgrid)

    >>> # Create from NumPy arrays
    >>> xrng = np.arange(-10, 10, 2)
    >>> yrng = np.arange(-10, 10, 2)
    >>> zrng = np.arange(-10, 10, 2)
    >>> x, y, z = np.meshgrid(xrng, yrng, zrng)
    >>> grid = pyvista.StructuredGrid(x, y, z)

    """

    _vtk_writers = {'.vtk': vtk.vtkStructuredGridWriter, '.vts': vtk.vtkXMLStructuredGridWriter}
    _vtk_readers = {'.vtk': vtk.vtkStructuredGridReader, '.vts': vtk.vtkXMLStructuredGridReader}

    def __init__(self, *args, **kwargs):
        """Initialize the structured grid."""
        super(StructuredGrid, self).__init__()

        if len(args) == 1:
            if isinstance(args[0], vtk.vtkStructuredGrid):
                self.deep_copy(args[0])
            elif isinstance(args[0], str):
                self._load_file(args[0])
        elif len(args) == 3 and all(isinstance(arg, np.ndarray) for arg in args):
            self._from_arrays(*args)

    def __repr__(self):
        """Return the standard representation."""
        return DataSet.__repr__(self)


    def __str__(self):
        """Return the standard str representation."""
        return DataSet.__str__(self)


    def _from_arrays(self, x, y, z):
        """Create VTK structured grid directly from numpy arrays.

        Parameters
        ----------
        x : np.ndarray
            Position of the points in x direction.

        y : np.ndarray
            Position of the points in y direction.

        z : np.ndarray
            Position of the points in z direction.

        """
        if not (x.shape == y.shape == z.shape):
            raise Exception('Input point array shapes must match exactly')

        # make the output points the same precision as the input arrays
        points = np.empty((x.size, 3), x.dtype)
        points[:, 0], points[:, 1], points[:, 2] = x.ravel('F'), y.ravel('F'), z.ravel('F')

        # ensure that the inputs are 3D
        dim = list(x.shape) + [1] * (3 - len(x.shape))

        # Create structured grid
        self.SetDimensions(dim)
        self.SetPoints(pyvista.vtk_points(points))

    @property
    def dimensions(self):
        """Return a length 3 tuple of the grid's dimensions."""
        return list(self.GetDimensions())

    @dimensions.setter
    def dimensions(self, dims):
        """Set the dataset dimensions. Pass a length three tuple of integers."""
        self.SetDimensions(*dims)
        self.Modified()

    @property
    def x(self):
        """Return the X coordinates of all points."""
        return self.points[:, 0].reshape(self.dimensions, order='F')

    @property
    def y(self):
        """Return the Y coordinates of all points."""
        return self.points[:, 1].reshape(self.dimensions, order='F')

    @property
    def z(self):
        """Return the Z coordinates of all points."""
        return self.points[:, 2].reshape(self.dimensions, order='F')

    def _get_attrs(self):
        """Return the representation methods (internal helper)."""
        attrs = PointGrid._get_attrs(self)
        attrs.append(("Dimensions", self.dimensions, "{:d}, {:d}, {:d}"))
        return attrs
