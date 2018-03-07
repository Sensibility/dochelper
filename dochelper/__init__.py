#!/usr/bin/env python3
"""
A documentation generator for Python3 comments and docstrings.

See the README.md for usage at https://github.com/Sensibility/dochelper
"""
import typing

# A mapping of syntax names to a list of tuples of delimeters that begin and end comments.
# A 2-tuple represents a pair of delimeters meant to begin and subsequently end the comment,
# while a 1-tuple represents a line comment (A comment that ends at the end of a line)
COMMENT_DELIMS = {'Python': [("'''", "'''"), ('"""', '"""'), ('#',)]}

def getContiguousComment(syntax:str, contents:typing.List[str])->typing.Optional[typing.List[str]]:
	"""
	Gets a contiguous comment from the file content

	Concatenates sequential line comments.
	Expects 'contents' to start with the comment in question.

	Returns the concatenation of sequential line comments, or the contents of a multiline comment.
	Returns `None` if the contents do not start with a comment in this syntax.
	Raises an EOFError if EOF is encountered while scanning a multiline comment.
	"""
	global COMMENT_DELIMS

	delims = COMMENT_DELIMS[syntax]
	thisLine = contents[0].lstrip()

	for delim in delims:
		if thisLine.startswith(delim[0]):
			contiguousComment = []
			if len(delim) == 1:
				for contentLine in contents:
					if not contentLine.lstrip().startswith(delim[0]):
						break
					contiguousComment.append(contentLine.lstrip(' \t%s' % delim[0]))
			else:
				contents[0] = contents[0].lstrip(' \t%s' % delim[0])
				for contentLine in contents:
					if delim[1] in contentLine:
						contiguousComment.append(\
						    contentLine[:contentLine.index(delim[1])].lstrip(' \t%s' % delim[0]))
						break
					contentLine = contentLine.lstrip(' \t%s' % delim[0])
					contiguousComment.append(contentLine)
				else:
					raise EOFError("EOF encountered while scanning block comment.")


			return contiguousComment
	return None



def extractPythonDocumentation(moduleName: str, contents: str) -> str:
	"""
	Processes a single python module for extractable documentation

	Pulls docstrings from applicable objects and comments immediately preceding global
	identifiers (that don't have docstrings) and class data members.

	Returns LaTeX code that outputs documentation for this module.
	"""

	latex = "\subsection{%s}\label{sec:py:%s}\n" % (moduleName, moduleName)

	# Get all lines that are not empty or just whitespace (and eliminate trailing whitespace)
	contentLines = [x.rstrip() for x in contents.strip().split('\n') if x and x.strip()]

	# Check for module docstring/top-level comments (first line could be shebang)
	if contentLines[0].startswith("#!"):
		_ = contentLines.pop(0)

	print(contentLines)

	moduleDocstring = getContiguousComment('Python', contentLines)

	print(moduleDocstring)

	latex += '\n'.join(moduleDocstring)

	return latex

# Supported extensions and the functions that parse them for documentation
                  # Python file extensions
SUPPORTED_EXTS = {'py': extractPythonDocumentation,
                  'py3': extractPythonDocumentation}

def handleFile(filename: str) -> str:
	"""
	Processes a single file for documentation, according to its type.

	Uses the SUPPORTED_EXTS dict to choose the proper method for the source code type, based on
	its extension.

	Returns the latex code that generates documentation for this file
	Raises a TypeError if the file extension is not supported.
	"""
	global SUPPORTED_EXTS
	import os

	basenameParts = os.path.basename(filename).split('.')

	fname, ext = ''.join(basenameParts[:-1]), basenameParts[-1]

	if ext not in SUPPORTED_EXTS:
		raise TypeError("Unsupported file type, ext: '.%s'" % ext)

	# Parse the file
	contents = None
	with open(filename) as infile:
		contents = infile.read()

	return SUPPORTED_EXTS[ext](fname, contents)

def main():
	"""
	Runs the main program.
	"""

	import argparse
	import os
	import sys

	parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
	parser.add_argument("PATH", nargs="+", help="Path to a module or package.")
	parser.add_argument("-o", "--output-path", type=str, default='.', dest='output')

	args = parser.parse_args()

	packages, modules = [], []
	for path in args.PATH:
		if not os.path.exists(path):
			print("File/Directory not found: '%s' attempting to continue..."%path, file=sys.stderr)
		elif os.path.isfile(path):
			modules.append(path)
		elif os.path.isdir(path):
			if not os.path.isabs(path):
				path = os.path.abspath(path)
			packages.append(path)

	if not packages and not modules:
		print("No inputs could be found on the filesystem. Exiting.", file=sys.stderr)
		exit(1)

	outputDir = args.output
	if not os.path.isabs(args.output):
		outputDir = os.path.abspath(args.output)

	print("Parsing modules:", modules,
	      "and packages:", packages,
	      "to output directory '%s'" % outputDir)


if __name__ == '__main__':
	main()
