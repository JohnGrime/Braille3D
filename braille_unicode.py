#
# http://www.unicode.org/charts/PDF/U2800.pdf
#
# Dot locations: 1 4
#                2 5
#                3 6
#               [7 8] <- for 8-dot codes; not used here.
#
# The Unicode representation of Braille is divided into several "pages" with 16
# glyphs per page. Using the dot order shown above, we can directly encode
# sequential dot patterns as sequential integers because the binary strings are
# the same (albeit reversed). Note that the final two 'bits' of the 6-bit dot
# pattern (5&6) also specify Unicode code page in binary (also reversed!).
#
# E.g.:
#
# 1 0
# 0 0
# 1 0
#
# Sequence = 101 000 => 1010 00 => reverse => 00 0101 == 0 5.
# Unicode is therefore 0x('28'+'0'+'5') = 0x2805
#
# 1 0
# 0 1
# 1 0
#
# Sequence = 101 010 => 1010 10 => reverse => 01 0101 == 1 5.
# Unicode is therefore 0x('28'+'1'+'5') = 0x2815
#
# The following routine returns a dictionary where:
#  - keys: 6-dot bitstrings as '123 456'
#  - vals: Unicode char corresponding to the bit pattern
#
# Should be easy to extend if needed.
#
def get_conversion_maps() -> ( {str: str}, {str: str} ):
	dots2unicode = {} # dot representation to unicode
	unicode2dots = {} # unicode to dot representation

	for page_i in range(0,4):
		for i in range(0,16):
			dot_str = f'{page_i:02b}{i:04b}'[::-1]
			dot_str  = dot_str[0:3] + ' ' + dot_str[3:] # 'xxxyyy' -> 'xxx yyy'

			uni_hex_str = f'28{page_i:1}{i:1X}'
			uni_char = chr( int(uni_hex_str,16) )

			dots2unicode[dot_str] = f'{uni_char}'
			unicode2dots[f'{uni_char}'] = dot_str

	return dots2unicode, unicode2dots
