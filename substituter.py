#!/usr/bin/env python

import configparser
import re
import unittest

from typing import Dict, Set, List

class SubstitutionError(Exception): pass

class CyclicSubstitutionError(SubstitutionError):
	def __init__(self, chain: Set[str]):
		self.chain = chain
		super(SubstitutionError, self).__init__(\
			"Encountered cyclic substitution in chain: {}".format(chain))

class UndefinedSubstitutionError(SubstitutionError):
	def __init__(self, name: str):
		self.name = name
		super(SubstitutionError, self).__init__(\
			"Encountered undefined substitution by {}".format(name))


def substitute(entries: Dict[str, str]) -> Dict[str, str]:
	'''
	Iteratively and recursively resolves all possible substitutions
	within the given dictionary.

	This mutates the given dictionary!
	'''
	resolved = set()

	def resolve_substitution(entry: str, seen: List[str] = None) -> str:
		'''
		Returns the entirely resolved entries content
		after resolution of all possible, recursive substitutions.
		'''
		def capture_substituter(match_obj) -> str:
			capture = match_obj.group(1)
			if   capture not in entries:
				raise UndefinedSubstitutionError(capture)
			elif capture in resolved:
				return entries[capture]
			elif capture in seen:
				seen.append(capture)
				raise CyclicSubstitutionError(seen)
			return resolve_substitution(capture, seen)

		if seen is None: seen = list()
		seen.append(entry)
		subst = re.sub('\$\{([a-zA-Z0-9_]+)\}', capture_substituter, entries[entry])
		if entry != subst: entries[entry] = subst
		resolved.add(entry)
		return subst

	for entry in entries:
		if entry not in resolved:
			resolve_substitution(entry)
	return entries


class TestSubstituter(unittest.TestCase):
	def test_trivial(self):
		given  = {'A':'${B}', 'B':'x'}
		target = {'A':'x'   , 'B':'x'}
		self.assertEqual(substitute(given), target)

	def test_trivial_twice(self):
		given  = {'A':'${B}', 'B':'x'}
		target = {'A':'x'   , 'B':'x'}
		self.assertEqual(substitute(given.copy()), target)
		self.assertEqual(substitute(given.copy()), target)
		self.assertEqual(substitute(given.copy()), target)

	def test_normal_substitution(self):
		given  = {'A':'a', 'B':'b', 'C':'c', 'foo': '${A}${B}${C}', 'bar': '${foo} ${foo}'}
		target = {'A':'a', 'B':'b', 'C':'c', 'foo': 'abc', 'bar': 'abc abc'}	
		self.assertEqual(substitute(given), target)

	def test_long_chain(self):
		given  = {'A': '${B}', 'B': '${C}', 'C': '${D}',\
			      'D': '${E}', 'E': '${F}', 'F': '${G}',\
			      'G': '${H}', 'H': '${I}', 'I': '${J}',\
			      'J': '${K}', 'K': '${L}', 'L': '${M}',\
			      'M': '${N}', 'N': '${O}', 'O': '${P}', 'P': '${Q}',\
			      'Q': '${R}', 'R': '${S}', 'S': '${T}', 'T': '${U}',\
			      'U': '${V}', 'V': '${W}', 'W': '${X}',\
			      'X': '${Y}', 'Y': '${Z}', 'Z': ''    }
		target = {'A': '', 'B': '', 'C': '',\
			      'D': '', 'E': '', 'F': '',\
			      'G': '', 'H': '', 'I': '',\
			      'J': '', 'K': '', 'L': '',\
			      'M': '', 'N': '', 'O': '', 'P': '',\
			      'Q': '', 'R': '', 'S': '', 'T': '',\
			      'U': '', 'V': '', 'W': '',\
			      'X': '', 'Y': '', 'Z': '' }	
		self.assertEqual(substitute(given), target)

	def test_self_substitution(self):
		with self.assertRaises(CyclicSubstitutionError):
			substitute({'A':'${A}'})

	def test_circular_substitution(self):
		with self.assertRaises(CyclicSubstitutionError):
			substitute({'A': '${B}', 'B': '${C}', 'C': '${A}'})

	def test_undef_substitution(self):
		with self.assertRaises(UndefinedSubstitutionError):
			substitute({'A': '${B}'})

if __name__ == '__main__':
	unittest.main()
