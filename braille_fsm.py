#
# John Grime 2021, Emerging Technologies, University of Oklahoma.
#
# Python3 module for various finite state machine (FSM) based functionality for
# the Braille utilities.
#

from braille_unicode import get_conversion_maps

#
# Type aliases we'll be using.
#
# Token: some text, tagged with metadata
# Transition: [txt to modify input], [txt to modify output], new state
# TransitionMap
#

Token = (str,str)
Transition = ([str], [str], str)

#
# Simple finite state machine; override the setup(), preprocess(), and
# postprocess() methods for specific FSM implementations.
#
# An input/output token is composed of a piece of text and some metadata.
#
# The FSM processes a list of input tokens, building and adding tokens to an
# output list (and potentially modifying the input token list) and moving into
# a specified "new" state (which may simply be the previous state).
#
# A state transition is triggered by a recognised input token for the current
# state, and is composed of:
#   1. A list of str pushed as tokens onto the input stack (can be empty)
#   1. A list of str pushed as tokens onto the output stack (can be empty)
#   3. The name of the new state (can be the same as the old state)
#
# The base FSM class contains a member "end", which is used as an end marker
# for e.g. token processing. Rather than assign a specific value to "end",
# which could force the user to avoid that specific text, we instead check
# for it by equality of REFERENCE (e.g., "if x is self.end") instad of equality
# of VALUE (e.g., "if x == self.end").
#

class FSM:
	"""
	Utility base class for the finite state machines used in thie module
	"""

	def __init__(self):
		# Actual value irrelevant; detect via REFERENCE not VALUE
		self.end = '|'

		self.states = {}
		self.start_state = None
		self.setup()

	def add_state(self, name: str, transition_map_list: [{str: Transition}]):
		"""
		Add a named state to the FSM, with the specified transitions

		Parameters
		----------

		name : string
			name of the state
		transition_map_list : list of transitions of form { input: ([in toks], [out toks], state) }
			Here, "input" is an input token that results in the tokens of
			"[in toks]" being added to the input token list and "[out toks]"
			being added to the output token list. state is then changed to
			"state" (which may simply be the original state).
		"""

		t = {}
		for transition_map in transition_map_list:
			t.update(transition_map)

		self.states[name] = { 'transitions': t }

	def process(self, in_toks: [Token], debug: bool = False) -> [Token]:
		"""
		Process the list of input tokens "in_toks" and return an output list

		Parameters
		----------

		in_toks : string, or list of tokens of the form (tok:string,tag:string)
		where tok and tag are strings
			This token list is processed until empty, or an undefined state is
			reached. If in_toks is actually a string, process it as a sequence
			of characters
		debug : bool
			Optional flag to specify printing the FSM state at each stage for
			debug purposes.

		Returns
		-------

		List of output tokens of the form [(tok,tag)] where tok and tag are
		strings
		"""

		# if "in_toks" is a string, process as sequence of characters - else
		# process as sequence of tokens
		in_seq = [(t,None) for t in in_toks] if isinstance(in_toks,str) else in_toks
		out_txt, out_seq = None, []
		state = self.start_state

		while len(in_seq)>0:

			# Unrecognised state?
			if state not in self.states:
				print(f'Reached undefined state: "{state}"')
				return None

			# pop next input off the front of in_seq, and set in_seq to rest
			in_tok, in_seq = in_seq[0], in_seq[1:]
			txt,tag = in_tok

			# If this input is not explicitly handled, attempt to transform it
			# into something we CAN handle via user-specified routine.
			tr = self.states[state]['transitions']
			result = tr[txt] if (txt in tr) else self.transform(txt,tag,state)

			if result == None:
				print(f'"{txt}" not recognised by state "{state}"; ignoring')
				continue

			in_, out_, state_ = result

			# Update output text, add to out_seq if special end code found.
			# We call the user-specified postprocess() routine here for any
			# final modification of the output text.
			for txt in out_:
				if txt is self.end: # Check same REFERENCE, not same value!
					out_seq = out_seq + self.postprocess(out_txt,tag,state)
					out_txt = None
				else:
					out_txt = txt if (out_txt==None) else out_txt+txt

			# Update input token sequence ("in_" is typically an empty list, so
			# doesn't ordinarily modify "in_seq")
			in_seq = in_ + in_seq

			if debug == True:
				print('')
				print(f'{in_tok} =={in_},{out_}=> "{out_txt}" ({state} => {state_})')
				print(f'  in_seq={in_seq[:5]}')
				print(f'  out_seq={out_seq}')

			# Update current FSM state
			state = state_

		# Add any trailing data to the output sequence
		if out_txt != None: out_seq.append( (out_txt,state) ) 

		return out_seq

	#
	# Implement these in subclasses to provide specialisation.
	#

	def setup(self):
		"""
		Set up internal data needed in process()
		"""

		pass

	def transform(self, txt: str, tag: str, state: str) -> Transition:
		"""
		Attempt to transform a specified token, given the token tag and
		current FSM state.

		Parameters
		----------

		txt : string
			Text to transform
		tag : string
			User-defined metadata tag for the text (can be useful for e.g.
			specifying that the text has specific characteristics, such as
			numeric, alphanumeric, call caps, ...)
		state : string
			State of the FSM when the transform is attempted.

		Returns
		-------

		None if text could not be transformed, otherwise a tuple of the form
		(in,out,state), where:
		- in    : list of tokens of the form (txt,tag)
		- out   : list of output text strings
		- state : new state (string)
		This is the same format as a standard FSM transition entry.
		"""

		return None

	def postprocess(self, txt: str, tag: str, state: str) -> [Token]:
		"""
		Postprocess output text (included for generality). Allow empty text
		to e.g. record state changes in the output with no associated text.

		Parameters
		----------

		txt : string
			Text to transform
		tag : string
			User-defined metadata tag for the text (can be useful for e.g.
			specifying that the text has specific characteristics, such as
			numeric, alphanumeric, call caps, ...)
		state : string
			State of the FSM when the transform is attempted.

		Returns
		-------

		Empty list of txt == None, else tuple ofthe form (txt,state) where txt
		and state are strings.
		"""

		return [] if (txt == None) else [ (txt,state) ]


class BrailleFSM(FSM):
	"""
	Braille finite state machine to contain common tag definitions etc used in
	the Braille-handling FSMs that follow. Should help keep things consistent!
	"""

	# Tags for token types; also used as state names where appropriate.
	whitespace_tag  = 'whitespace' # whitespace
	lower_tag       = 'lower_str'  # sequence with only lower case letters,
	upper_tag       = 'upper_str'  # only upper case letters,
	mixed_tag       = 'mixed_str'  # both upper & lower case letters,
	alphanum_tag    = 'alphanum'   # upper/lower case letters & digits,
	number_tag      = 'number'     # can be interpreted as a number.
	punctuation_tag = 'punctuation'


class BrailleTokeniser(BrailleFSM):
	"""
	FSM to tokenize an input stream, producing output suitable for use in the
	Braille translation FSM.
	This example assumes U.S. English, but it should be trivial to modify this
	example for other languages by e.g. modifying the upper & lower case letter
	sets and modifying definition of whitespace etc as required.
	"""

	def setup(self):
		"""
		Sets up the internal data fpr the FMS, including transitions and
		start state.
		"""

		#
		# Can't rely on e.g. locale strings in Python's standard string module
		# to be USA! We also need only a limited Braille character set ...
		#
		lower = 'abcdefghijklmnopqrstuvwxyz'
		upper = lower.upper()
		digit  = '0123456789'
		white = '\t '  # whitespace characters
		punct = ',.;:' # punctuation characters
		
		w_tag = self.whitespace_tag
		u_tag = self.upper_tag
		l_tag = self.lower_tag
		m_tag = self.mixed_tag
		a_tag = self.alphanum_tag
		n_tag = self.number_tag
		p_tag = self.punctuation_tag

		# Transitions for "punctuation" state
		self.add_state( p_tag,
			[
			{k: ([], [k], p_tag) for k in punct},
			{k: ([], [self.end,k], l_tag) for k in lower},
			{k: ([], [self.end,k], u_tag) for k in upper},
			{k: ([], [self.end,k], n_tag) for k in digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			])

		# Transitions for "whitespace" state
		self.add_state( w_tag,
			[
			{k: ([], [self.end,k], l_tag) for k in lower},
			{k: ([], [self.end,k], u_tag) for k in upper},
			{k: ([], [self.end,k], n_tag) for k in digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			{k: ([], [self.end,k], p_tag) for k in punct},
			])

		# Transitions for "lower case sequence" state
		self.add_state( l_tag,
			[
			{k: ([], [k],          l_tag) for k in lower},
			{k: ([], [k],          m_tag) for k in upper},
			{k: ([], [k],          a_tag) for k in digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			{k: ([], [self.end,k], p_tag) for k in punct},
			])

		# Transitions for "upper case sequence" statr
		self.add_state( u_tag,
			[
			{k: ([], [k],          m_tag) for k in lower},
			{k: ([], [k],          u_tag) for k in upper},
			{k: ([], [k],          a_tag) for k in digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			{k: ([], [self.end,k], p_tag) for k in punct},
			])

		# Transitions for "mixed case sequence" state; could simply merge this
		# with the alphanumerical state to simplify the FSM, but it's here to
		# retain as much metadata and context as possible (this tag indicates
		# a sequence that contains no digits, only upper/lower case letters).
		self.add_state( m_tag,
			[
			{k: ([], [k],          m_tag) for k in lower+upper},
			{k: ([], [k],          a_tag) for k in digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			{k: ([], [self.end,k], p_tag) for k in punct},
			])

		# Transitions for "alphanumeric" state; upper/lower case characters
		# and digits keep us in alphanumeric state, whitespace bumps us out.
		self.add_state( a_tag,
			[
			{k: ([], [k],          a_tag) for k in lower+upper+digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			{k: ([], [self.end,k], p_tag) for k in punct},
			])

		# Transitions for "number" state; numbers keep us in, anything else
		# bumps us out. EXTREMELY crude! Doesn't properly handle e.g. decimal place!
		self.add_state( n_tag,
			[
			{k: ([], [k],          a_tag) for k in lower+upper},
			{k: ([], [k],          n_tag) for k in digit},
			{k: ([], [self.end,k], w_tag) for k in white},
			{k: ([], [self.end,k], p_tag) for k in punct},
			])

		self.start_state = w_tag


class BrailleTranslator(BrailleFSM):
	"""
	FSM to translate tokens generated by the Tokeniser FSM into Braille.
	"""

	def setup(self):
		"""
		Sets up the internal data for the FSM, including transitions and
		start state.
		"""

		dots_to_uni, _ = get_conversion_maps()
		state = 'default' # only one state in this FSM!
		l_tag = self.lower_tag
		w_tag = self.whitespace_tag
		spaces_per_tab = 2

		# One upper_code indicates that the following letter is upper case, two
		# indicates that the ENTIRE following sequence is upper case. Number
		# code indicates that following sequence is be interpreted as a number.
		self.upper_code  = dots_to_uni['000 001']
		self.number_code = dots_to_uni['001 111']

		# Special fragments to break down input
		self.fragments = [ 'ed', 'ing' ]

		# Lower case letter => Braille dot code
		lower = {
			'a': '100 000',
			'b': '110 000',
			'c': '100 100',
			'd': '100 110',
			'e': '100 010',
			'f': '110 100',
			'g': '110 110',
			'h': '110 010',
			'i': '010 100',
			'j': '010 110',

			'k': '101 000',
			'l': '111 000',
			'm': '101 100',
			'n': '101 110',
			'o': '101 010',
			'p': '111 100',
			'q': '111 110',
			'r': '111 010',
			's': '011 100',
			't': '011 110',

			'u': '101 001',
			'v': '111 001',
			'w': '010 111',
			'x': '101 101',
			'y': '101 111',
			'z': '101 011',
		}
		lower = { k: ([], [dots_to_uni[v]], state) for k,v in lower.items() }

		# Misc. input that can be translated directly into a Braille dot code
		misc = {
			' ': '000 000',
			',': '010 000',
			'.': '010 011',

			# Common words with Braille dot code representation
			'for': '111 111',
			'and': '111 101',
			'the': '011 101',

			# Word fragments with Braille dot code representation
			'ed':  '110 101',
			'ing': '001 101',
		}
		misc = { k: ([], [dots_to_uni[v]], state) for k,v in misc.items() }

		# Straight substitutions of literal text => list of Braille tokens
		swap = {
			# Recognised standard Braille abbreviations
			'tomorrow': [ ('tm',l_tag) ],
			'friend':   [ ('fr',l_tag) ],
			'little':   [ ('ll',l_tag) ],
			'you':      [ ( 'y',l_tag) ],
			'like':     [ ( 'l',l_tag) ],
			'him':      [ ('hm',l_tag) ],
			# Handle some whitespace expansions
			'\t':       [ ( ' ',w_tag) for i in range(spaces_per_tab) ],
		}
		swap = { k: (v, [], state) for k,v in swap.items() }

		#
		# Upper case letters are just lower case letters preceeded by the
		# special upper case indicator. Special case: entire token upper case,
		# in which case the output is preceeded by 2 upper case indicators;
		# this special case is handled elsewhere.
		#
		upper = { k.upper(): (i,[self.upper_code]+o,s) for k,(i,o,s) in lower.items() }

		#
		# Digits 1-0 are the same code as letters a-j in the Braille basic
		# Latin set; we insert the special digit code into the output stream to
		# distinguish.
		#
		number = { k: lower['abcdefghij'[i]] for (i,k) in enumerate('1234567890') }

		#
		# Braille unicode tokens are "identities"; they output themselves. This
		# lets us embed Braille unicode directly into the input and have it
		# output along with the other information.
		#
		uni = { v: ([], [v], state) for k,v in dots_to_uni.items() }

		#
		# Build default state and transitions, specify start state.
		#
		self.add_state(state, [lower, upper, number, misc, uni, swap, ])
		self.start_state = state

	def transform(self, txt: str, tag: str, state: str) -> Transition:
		"""
		Attempt to transform a token generated by the BrailleTokeniser FSM.

		Parameters
		----------

		txt : string
			Text to transform
		tag : string
			Metadata tag for the text as set by BrailleTokeniser FSM
		state : string
			State of the FSM when the transform is attempted.

		Returns
		-------

		Tuple of the form (in,out,state), where:
		- in    : list of tokens of the form (txt,tag)
		- out   : list of output text strings
		- state : new state (string)
		This is the same format as a standard FSM transition entry.
		"""

		u_tag = self.upper_tag
		l_tag = self.lower_tag
		n_tag = self.number_tag

		#
		# If txt is tagged as a number, insert the number code into the output
		# sequence and push number back onto input as text; need text tag to
		# prevent infinite loop of read a number => add number to input => read
		# number again ...
		#
		if tag == n_tag:
			tok, numtok = (txt, l_tag), (self.number_code, tag)
			return [numtok,tok], [], state

		#
		# If txt is tagged as entirely upper case, insert two upper codes into
		# the input sequence followed by the token text as lower case.
		#
		if tag == u_tag:
			tok, uptok = (txt.lower(), l_tag), (self.upper_code, tag)
			return [uptok,uptok,tok], [], state

		#
		# Does the token contain special fragments? If so, decompose and add
		# the smaller subtokens to the input sequence.
		#
		for x in self.fragments:
			i = txt.find(x)
			if i == -1: continue

			pre, post = txt[:i], txt[i+len(x):]
			return [(t,tag) for t in [pre,x,post] if t != ''], [], state

		#
		# Assume parse down to individual characters?
		#
		return [(t,tag) for t in txt], [], state
