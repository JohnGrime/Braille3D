#
# John Grime 2021, Emerging Technologies, University of Oklahoma.
#
# Python3 module for generating 3D models from Braile "dotcodes".
#

import math

#
# Specify the type aliases we'll be using
#

Vtx = [float,float,float]
Tri = [int,int,int]

VtxList = [Vtx]
TriList = [Tri]

Mesh = (VtxList, TriList)

#
# Utility functions
#

def save_wavefront_obj(f, vtx: VtxList, tri: TriList):
	"""Save simple 3D mesh as Wavefront .obj file format

	https://en.wikipedia.org/wiki/Wavefront_.obj_file

	Parameters
	----------

	f : file object or string file path for output
	vtx : list of list of float, [[x,y,z]]
		vertices to write to output
	tri: list of list of int, [[i,j,k]]
		ZERO BASED indices into vtx describing mesh triangles
	"""

	def save(f, vtx: VtxList, tri: TriList):
		for x,y,z in vtx:
			print(f'v {x:.3f} {y:.3f} {z:.3f}', file=f)
		for i,j,k in tri:
			print(f'f {i+1} {j+1} {k+1}', file=f)

	try:
		save(f, vtx, tri)
	except AttributeError:
		with open(f,'w') as f_:
			save(f_, vtx, tri)

#
# Utility classes
#

class Braille3DGenerator:
	"""Utility class for generating 3D models of Braille text"""

	@staticmethod
	def generate_unit_dot(
		taper: float=0.8,
		vtx_per_ring: int=10,
		n_taper_rings: int=5
		) -> Mesh:
		"""Generates mesh model for a Braille "dot" with unit radius and height.

		Center of cylinder base is at the origin, cylinder axis is along +z.
		The dot is cylindrical until a specified proportion of height ("taper"),
		at which point it starts to taper off into a flattened end.

		Parameters
		----------
		taper : float
			Proportion of height at which the cylidrical dot start to taper.

		vtx_per_ring : int, optional
			Number of vertices in each cylinder "ring" (default is 10)

		n_taper_rings : int, optional
			Nunber of rings in the tapering region of the dot (default is 5)
		"""

		vtx, tri, Hc, Ht = [], [], taper, 1.0-taper

		# Triangular mesh for a disc via single central point & vtx ring
		def seal_disc(centre_i: int, ring_i: int) -> TriList:
			t = []
			for i in range(vtx_per_ring):
				j = (i+1)%vtx_per_ring
				t.append( [ring_i0+i, ring_i0+j, centre_i] )
			return t

		# Triangular mesh for a cylinder via two vtx rings
		def seal_cylinder(r1: int, r2: int) -> TriList:
			t = []
			for i in range(vtx_per_ring):
				j = (i+1)%vtx_per_ring
				t.extend( Braille3DGenerator.plane(r1+i,r1+j,r2+j,r2+i) )
			return t

		#
		# Points on a unit circle in the x,y plane, center at (0,0)
		#

		delta = 2.0*math.pi/vtx_per_ring
		unit_circle = [(math.sin(i*delta),math.cos(i*delta),0) for i in range(vtx_per_ring)]

		#
		# Base of dot; disc formed by a central vertex connected to vertices
		# around a circle.
		#

		vtx.append( [0,0,0] )
		vtx.extend( [[x,y,z] for x,y,z in unit_circle] )

		centre_i, ring_i0 = 0, 1
		tri.extend( seal_disc(centre_i,ring_i0) )

		#
		# Cylindrical main body of dot; connect single lower ring to single
		# upper ring of identical width (i.e. no tapering yet)
		#

		vtx.extend( [[x,y,z+Hc] for x,y,z in unit_circle] )

		r1, r2 = len(vtx)-vtx_per_ring, len(vtx)-2*vtx_per_ring
		tri.extend( seal_cylinder(r1,r2) )

		#
		# Upper dome of dot formed by successive tapering rings; dome will be
		# closed later using a disc as per the base of the dot.
		#

		Ntr = n_taper_rings+1
		for i in range(1,Ntr):
			theta = i * (math.pi/2)/(Ntr)
			r = math.cos(theta) # current radius

			theta = i * (math.pi/2)/(Ntr-1)
			h = Hc + math.sin(theta) * Ht # current elevation

			vtx.extend( [[x*r,y*r,z+h] for x,y,z in unit_circle] )

			r1, r2 = len(vtx)-vtx_per_ring, len(vtx)-2*vtx_per_ring
			tri.extend( seal_cylinder(r1,r2) )
		
		#
		# Close the dome by connecting a single central vertex to the final
		# ring added; flip the vtx order so the normal points outwards.
		#

		vtx.append( [0,0,1] )

		centre_i = len(vtx)-1
		ring_i0 = centre_i - vtx_per_ring
		tri.extend( [[j,i,k] for (i,j,k) in seal_disc(centre_i,ring_i0)] )

		return vtx, tri

	@staticmethod
	def generate_unit_cube() -> Mesh:
		"""Generate mesh for a unit cube.

		Can be used to generate a backing panel for sequences of
		Braille characters.
		"""

		vtx = [
			# Lower plane
			[ 0, 0, 0],
			[ 1, 0, 0],
			[ 1, 1, 0],
			[ 0, 1, 0],
			# Upper plane
			[ 0, 0, 1],
			[ 1, 0, 1],
			[ 1, 1, 1],
			[ 0, 1, 1],
		]

		tri = []
		tri.extend( Braille3DGenerator.plane(4,5,6,7) ) # upper plane
		tri.extend( Braille3DGenerator.plane(3,2,1,0) ) # lower plane
		tri.extend( Braille3DGenerator.plane(0,1,5,4) ) # side
		tri.extend( Braille3DGenerator.plane(1,2,6,5) ) # side
		tri.extend( Braille3DGenerator.plane(2,3,7,6) ) # side
		tri.extend( Braille3DGenerator.plane(3,0,4,7) ) # side

		return vtx, tri

	@staticmethod
	def plane(i: int, j: int, k: int, l: int) -> TriList:
		"""Return indices of two triangles forming planar rectangle i->j->k->l

		l--k
		|  | => 2 x triangles
		i--j

		Parameters
		----------

		i : int
			Index of first vertex
		j : int
			Index of second vertex
		k : int
			Index of third vertex
		l : int
			Index of fourth vertex
		"""
		return [ [i,j,k], [k,l,i] ]

	#
	# taper = proportion of cylindrical dot height for onset of tapering
	# vtx_per_ring = radial resolution
	# n_taper_rings = vertical resolution for tapering region
	#
	def __init__(self,
		dot_radius,
		dot_height,
		dot_dx,  # spacing between adjacent dots on horizontal axis
		dot_dy,  # between adjacent dots on vertical axis
		char_dx, # between same dot in adjacent chars on horizontal axis
		char_dy, # between same dot in adjacent chars on vertical axis
		dot_taper=0.8,
		dot_vtx_per_ring=10,
		dot_n_taper_rings=5):

		self.dot_radius, self.dot_height = dot_radius, dot_height

		self.dot_dx, self.dot_dy = dot_dx, dot_dy
		self.char_dx, self.char_dy = char_dx, char_dy

		self.unit_vtx, self.unit_tri = self.generate_unit_dot(
			taper=dot_taper,
			vtx_per_ring=dot_vtx_per_ring,
			n_taper_rings=dot_n_taper_rings)

	def generate_dot(self, xyz: Vtx=[0,0,0]) -> Mesh:
		"""Returns a Mesh for a single Braille dot.

		Parameters
		----------

		xyz : Vtx, optional
			Centre of dot (default is [0,0,0])
		"""

		x,y,z = xyz
		r, h = self.dot_radius, self.dot_height

		vtx = [[x+(vx*r), y+(vy*r), z+(vz*h)] for vx,vy,vz in self.unit_vtx]
		tri = [[i,j,k] for i,j,k in self.unit_tri]
		return vtx, tri

	def generate_char(self, dotstring: str, xyz: Vtx=[0,0,0]) -> Mesh:
		"""Returns a Mesh for a single Braille character.

		Parameters
		----------

		dotstring : str
			Text representation of Braille character using dot pattern of two
			columns, e.g. '010 111'

		xyz : Vtx, optional
			Lower-left of box enclosing the Braille char (default is [0,0,0])
		"""

		x,y,z = xyz
		d_dx, d_dy = self.dot_dx, self.dot_dy
		c_dx, c_dy = self.char_dx, self.char_dy
		vtx, tri = [], []

		# Filter input string so we only have 0 or 1
		s = [c for c in dotstring if c in ['1','0']]

		# Center the dot pattern in rectangular bounding box of character
		x_ofs = 0.5*(c_dx - d_dx*(2-1))
		y_ofs = c_dy - 0.5*(c_dy - d_dy*(3-1))

		x_ = x + x_ofs
		for col in range(2):
			y_ = y + y_ofs
			for row in range(3):
				if s[(col*3)+row] == '1':
					vtx_, tri_ = self.generate_dot([x_,y_,z])
					N = len(vtx)
					vtx.extend( [[x,y,z] for x,y,z in vtx_] )
					tri.extend( [[i+N,j+N,k+N] for i,j,k in tri_] )
				y_ -= d_dy
			x_ += d_dx

		return vtx, tri

	def generate_line(self, dotstrings: [str], xyz: Vtx=[0,0,0]) -> Mesh:
		"""Returns a Mesh for a line of Braille characters.

		Parameters
		----------

		dotstrings : list of str, [str]
			A line of Braiile text, represented as a list of two-column dot
			patterns e.g. ['010 111', '101 011']

		xyz : Vtx, optional
			Lower-left of box enclosing first Braille char (default is [0,0,0])
		"""

		x,y,z = xyz
		dx = self.char_dx
		vtx, tri = [], []
		for dotstring in dotstrings:
			vtx_, tri_ = self.generate_char(dotstring, [x,y,z])
			N = len(vtx)
			vtx.extend( [[x,y,z] for x,y,z in vtx_] )
			tri.extend( [[i+N,j+N,k+N] for i,j,k in tri_] )
			x += dx

		return vtx, tri

	def generate_lines(self, dotstrings_list: [[str]], xyz: Vtx=[0,0,0]) -> Mesh:
		"""Returns a Mesh for a set of line of Braille characters.

		Parameters
		----------

		dotstrings : list of list of str, [[str]]
			A list of lines of Braiile text, with each line represented as a
			list of two-column dot patterns e.g. ['010 111', '101 011']

		xyz : Vtx, optional
			Lower-left of box enclosing first Braille char of the final line
			(default is [0,0,0])
		"""

		x,y,z = xyz
		dy = self.char_dy
		vtx, tri = [], []

		# Adjust so lower left corner of bounding box for final line is origin.
		y += (len(dotstrings_list)-1) * dy

		for dotstrings in dotstrings_list:
			vtx_, tri_ = self.generate_line(dotstrings, [x,y,z])
			N = len(vtx)
			vtx.extend( [[x,y,z] for x,y,z in vtx_] )
			tri.extend( [[i+N,j+N,k+N] for i,j,k in tri_] )
			y -= dy

		return vtx, tri
