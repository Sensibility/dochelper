#!/usr/bin/env python3
"""
A documentation generator for Python3 comments and docstrings.

See the README.md for usage at https://github.com/Sensibility/dochelper
"""
import typing
import re

# A mapping of syntax names to a list of tuples of delimeters that begin and end comments.
# A 2-tuple represents a pair of delimeters meant to begin and subsequently end the comment,
# while a 1-tuple represents a line comment (A comment that ends at the end of a line)
COMMENT_DELIMS = {'Python': [("'''", "'''"), ('"""', '"""'), ('#',)]}

# A mapping of syntax names to regex patterns that show assignment
ASSIGNMENT_PATTERNS = {'Python': re.compile(r'[a-zA-Z_]\w*\s*=')}

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


			return [ x for x in contiguousComment if x ]
	return None


def processPythonFunction(contents: typing.List[str]) -> typing.Tuple[str, str, int]:
	"""
	Processes a Python function.

	Returns the function name, the function docstring, and the number of lines contained in the
	function.
	"""
	global COMMENT_DELIMS

	funcname = contents[0][4:].lstrip()
	funcname = funcname[:funcname.index('(')].rstrip()

	docstring = getContiguousComment('Python', contents[1:])
	if docstring is None:
		docstring = ''

	identRegex = []
	for delim in COMMENT_DELIMS['Python']:
		identRegex.append(delim[0])
	identRegex = re.compile('|'.join(identRegex))

	indentation = contents[1][:identRegex.search(contents[1]).start()]

	numLines = 1 + len(docstring)
	for line in contents[numLines:]:
		if not line.startswith(indentation):
			break
		numLines += 1

	return funcname, docstring, numLines


# A mapping of syntax names to functions that process functions for that syntax.
FUNCTION_PROCESSORS = {'Python': processPythonFunction}


def extractPythonDocumentation(moduleName: str, contents: str) -> str:
	"""
	Processes a single python module for extractable documentation

	Pulls docstrings from applicable objects and comments immediately preceding global
	identifiers (that don't have docstrings) and class data members.

	Returns LaTeX code that outputs documentation for this module.
	"""
	global ASSIGNMENT_PATTERNS, FUNCTION_PROCESSORS

	latex = [r"\subsection{%s}\label{sec:py:%s}" % (moduleName, moduleName)]

	# Get all lines that are not empty or just whitespace (and eliminate trailing whitespace)
	contentLines = []
	currentLine = ''
	for line in contents.strip().split('\n'):
		if line and line.strip():
			if line.endswith('\\'):
				currentLine += line
			else:
				contentLines.append(currentLine + line)
				currentLine = ''

	contentLines = [x.rstrip() for x in contents.strip().split('\n') if x and x.strip()]

	# Check for module docstring/top-level comments (first line could be shebang)
	if contentLines[0].startswith("#!"):
		_ = contentLines.pop(0)

	moduleDocstring = getContiguousComment('Python', contentLines)
	processedLines = len(moduleDocstring)

	latex.append('\n'.join(moduleDocstring))

	constants, functions, classes = {}, {}, {}
	while processedLines < len(contentLines):
		comments = getContiguousComment('Python', contentLines[processedLines:])
		if comments is None:
			print(contentLines[processedLines])
			if contentLines[processedLines].startswith('def'):
				funcname,\
				docstring,\
				containedLines = FUNCTION_PROCESSORS['Python'](contentLines[processedLines:])
				functions[funcname] = '\n'.join(docstring)
				processedLines += containedLines
			elif ASSIGNMENT_PATTERNS['Python'].match(contentLines[processedLines]):
				constants[contentLines[processedLines].split('=')[0].strip()] = ''
				processedLines += 1
			else:
				processedLines += 1
		elif ASSIGNMENT_PATTERNS['Python'].match(contentLines[processedLines+len(comments)]):
			processedLines += len(comments)
			constants[contentLines[processedLines].split('=')[0].strip()] = '\n'.join(comments)
			processedLines += 1
		else:
			processedLines += len(comments)

	if constants:
		latex.append(r"\subsubsection{Constants}\label{sec:py:%s:constants}" % moduleName)
		latex.append(r"\begin{itemize}")
		for constant in sorted(constants):
			latex.append(r"\item{}\lstinline{%s}\\" % constant)
			latex.append("\t%s\\\\" % constants[constant])

		latex.append(r"\end{itemize}")

	if functions:
		latex.append(r"\subsubsection{Functions})\label{sec:py:%s:funcs}" % moduleName)
		latex.append(r"\begin{itemize}")
		for func in sorted(functions):
			latex.append(r"\item{}\lstinline{%s}\\" % func)
			latex.append("\t%s\\\\" % functions[func])

		latex.append(r"\end{itemize}")


	return '\n'.join(latex)

# Supported extensions and the functions that parse them for documentation
                  # Python file extensions
SUPPORTED_EXTS = {'py': extractPythonDocumentation,
                  'py3': extractPythonDocumentation}

def handleFile(filename: str) -> typing.Tuple[str, str]:
	"""
	Processes a single file for documentation, according to its type.

	Uses the SUPPORTED_EXTS dict to choose the proper method for the source code type, based on
	its extension.

	Returns the name of the output file and latex code that generates documentation for this file
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

	return "%s.%s.tex" % (fname, ext), SUPPORTED_EXTS[ext](fname, contents)

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

	if not os.path.exists(outputDir):
		try:
			os.makedirs(outputDir)
		except OSError as e:
			print("Could not create output directory '%s': '%s'" % (outputDir, e), file=sys.stderr)
			exit(1)

	elif not os.path.isdir(outputDir):
		print("Cannot write to output directory '%s' - it already exists but is not a directory!"\
		                                   % outputDir, file=sys.stderr)
		exit(1)

	outputFiles = set()

	for module in modules:
		try:
			fname, output = handleFile(module)
		except EOFError as e:
			print(e, file=sys.stderr)
		else:
			with open(os.path.join(outputDir, fname), 'w') as outfile:
				outfile.write(output)

			outputFiles.add(fname)

	with open(os.path.join(outputDir, 'index.tex')) as idxfile:
		idxfile.write('\n'.join(r"\include{%s}" % outputFile for outputFile in outputFiles))

	print("Done. Output in '%s' in files: " % outputDir)
	for file in outputFiles:
		print("\t", file)


if __name__ == '__main__':
	main()
