#
# John Grime 2021, Emerging Technologies, University of Oklahoma.
#
# Main driver script for the Braille translation / model generation package.
#

#!/usr/bin/env python3

import sys

from braille_3d import Braille3DGenerator
from braille_3d import save_wavefront_obj as save

from braille_unicode import get_conversion_maps


if len(sys.argv) < 2:
	print(f'Usage: python3 {sys.argv[0]} "text to convert" [dumb]')
	print(f"Output: a Wavefront .obj file of the converted text.")
	print(f'If optional "dumb" parameter is specified, uses dumb internal translator. WARNING: Only for emergencies!')
	sys.exit(-1)

input_txt = sys.argv[1]
use_liblouis = False if (len(sys.argv)>2 and sys.argv[2] == 'dumb') else True

#
# Two options; use Python bindings for liblouis, or the internal translation
# system ("dumb"). As you might infer from the naming, the internal system is
# not very good and should only be considered for emergency purposes; it's only
# a partial implementation of the Braille system, and I stopped development
# after integrating liblouis support. However, it's quite simple and flexible
# so the functionality can be extended in future for a lightweight system that
# has no external dependencies if that is desired.
#

if use_liblouis:
	import louis

	tableList = ["en-ueb-g2.ctb"]
	unicode_dots = louis.translateString(tableList, input_txt, typeform=None, mode=louis.dotsIO|louis.ucBrl)
	backTranslation = louis.backTranslateString(tableList, unicode_dots, typeform=None, mode=0)
	
	print(f'# input => Braille => back translation : "{input_txt}" => "{unicode_dots}" => "{backTranslation}"')

else:
	from braille_fsm import BrailleTokeniser as Tokeniser
	from braille_fsm import BrailleTranslator as Translator

	btok, btrn = Tokeniser(), Translator()
	tokens = btok.process(input_txt)
	unicode_dots = btrn.process(tokens)
	unicode_dots = unicode_dots[0][0]

	print('# WARNING - dumb translation! Probably wrong, for emergency use!')
	print(f'# input => Braille : "{input_txt}" => "{unicode_dots}"')

#
# National Library Service for the Blind and Physically Handicapped of the Library of Congress,
# Specification 800 (see http://www.brailleauthority.org/sizespacingofbraille/sizespacingofbraille.pdf)
# All units in mm, except dot_taper (which is proportional to dot_height)
#

params = {
	'dot_radius': 1.44/2, # dot diameter at base = 1.44mm
	'dot_height': 0.48,   # dot height = 0.48mm
	'dot_taper': 0.75,    # arbitrary, proportional to height
	'dot_dx': 2.340,      # center-to-center of adjacent dots in same cell = 2.340mm
	'dot_dy': 2.340,      # center-to-center of adjacent dots in same cell = 2.340mm
	'char_dx': 6.2,       # center-to-center of corresponding dots in adjacent cells = 6.2mm
	'char_dy': 10.0,      # center-to-center of corresponding dots in adjacent cells = 10mm
	'dot_vtx_per_ring': 10,
	'dot_n_taper_rings': 5,
}

bgen = Braille3DGenerator(**params)
d2u, u2d = get_conversion_maps()

#
# Convert unicode Braille symbols into the two-column binary representation
# used by the 3d model generation class.
#

line = [u2d[x] for x in unicode_dots]
lines = [line]

#
# Convert two-column Braille representation into vertices and triangle mesh
#

vtx, tri = bgen.generate_lines(lines)

#
# Generate a box below the Braille dots to act as a support; rescale
# box on x and y dims according to max line length and line count.
#

box_vtx, box_tri = bgen.generate_unit_cube()
N, x_, y_, z_ = len(vtx), bgen.char_dx, bgen.char_dy, 0.5
x_ *= max( [len(l) for l in lines] )
y_ *= len(lines)
box_vtx = [ [x*x_,y*y_,(-z_)+(z*z_)] for x,y,z in box_vtx ]
box_tri = [ [i+N,j+N,k+N] for i,j,k in box_tri ]

#
# Add box info to vertex / triangle set
#

vtx.extend(box_vtx)
tri.extend(box_tri)

#
# Save 3d object
#

save(sys.stdout, vtx, tri)
