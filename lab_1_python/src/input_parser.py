import sys
from typing import Set


class InputParser:
	"""Minimal positional parser mirroring the C++ InputParser.

	Usage (positional):
	  python main.py <FA|KMP> <pattern> <filename>

	The constructor expects argv (full argv including script name) or uses sys.argv.
	"""

	def __init__(self, argv=None):
		argv = argv if argv is not None else sys.argv
		self.is_valid = False
		self.algorithm = ""
		self.pattern = ""
		self.text = ""
		self.alphabet = set()
		self.filename = ""

		# Expect exactly: [script, algorithm, pattern, filename]
		if len(argv) != 4:
			print("Usage: <FA|KMP> <pattern> <filename>", file=sys.stderr)
			return

		self.algorithm = argv[1]
		self.pattern = argv[2]
		self.filename = argv[3]

		# Read file to text
		try:
			with open(self.filename, 'r', encoding='utf-8', errors='replace') as f:
				self.text = f.read()
		except Exception as e:
			print(f"Cannot open file: {self.filename} ({e})", file=sys.stderr)
			return

		# Normalize CRLF (remove CR)
		self.pattern = self.pattern.replace('\r', '')
		self.text = self.text.replace('\r', '')

		# Build alphabet from text and pattern
		for c in self.text:
			self.alphabet.add(c)
		for c in self.pattern:
			self.alphabet.add(c)

		self.is_valid = True

	def validate(self) -> bool:
		return self.is_valid

	def get_algorithm(self) -> str:
		return self.algorithm

	def get_pattern(self) -> str:
		return self.pattern

	def get_text(self) -> str:
		return self.text

	def get_alphabet(self) -> Set[str]:
		return set(self.alphabet)

	def get_filename(self) -> str:
		return self.filename

