#!/usr/bin/env python3
"""
A documentation generator for Python3 comments and docstrings.

See the README.md for usage at https://github.com/Sensibility/dochelper
BTW, this is riddled with inefficiencies. I'm filing all of that under "wontfix" for now.
"""
import typing
import re
import sys

# A mapping of syntax names to a list of tuples of delimeters that begin and end comments.
# A 2-tuple represents a pair of delimeters meant to begin and subsequently end the comment,
# while a 1-tuple represents a line comment (A comment that ends at the end of a line)
COMMENT_DELIMS = {'Python': [("'''", "'''"), ('"""', '"""'), ('#',)]}

# A mapping of syntax names to regex patterns that show assignment
ASSIGNMENT_PATTERNS = {'Python': re.compile(r'[a-zA-Z_]\w*\s*=')}

def processComment(comment: str) -> str:
	"""
	Processes a comment for things that should be interpreted in a special way.

	Some day I'll detail the specifics, but it does markdown-like things like turning backticks
	into inline code and underscores into italics.
	"""
	sugar = {'_': r'\textit{', '*': r'\textbf{', '`': r'\code{'}

	# This stack is used to "solve" the dangling brace problem.
	# Currently, it doesn't do that , as it doesn't solve double-nesting.
	# Which you should never do anyway, since 'double bold font' isn't a thing.
	braces = {'*': 0, '_': 0, '`': 0}

	output = []
	for i, char in enumerate(comment):
		if char in sugar and i and comment[i-1] != '\\':
			if braces[char]:
				braces[char] -= 1
				char = '}'
			else:
				braces[char] += 1
				char = sugar[char]
		output.append(char)

	if any(braces.values()):
		# need to forcibly close braces, then issue a warning
		output += ['}']*sum(braces.values())
		print("Warning!! Unterminated format specifier encountered!", file=sys.stderr)

	return ''.join(output)


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


			return [ x.replace('_', r'\_') for x in contiguousComment if x ]
	return None


def processPythonFunction(contents: typing.List[str]) -> typing.Tuple[str, str, int]:
	"""
	Processes a Python function.

	Returns the function name, the function docstring, and the number of lines contained in the
	function.
	"""
	global COMMENT_DELIMS

	funcname = contents[0][4:].lstrip()
	argsStart = funcname.index('(')
	argsEnd = -(funcname[::-1].index(')')) - 1
	if ',' in funcname[argsStart:argsEnd]:
		args = [a.strip().replace("_", r"\_") for a in funcname[argsStart+1:argsEnd].split(',') if a]
	else:
		args = []
	funcname = funcname[:argsStart].rstrip()

	argslist = []
	for arg in args:
		thisArg = []
		if ':' in arg:
			thisArg.append(arg.split(':')[0].strip())
			if '=' in arg:
				lastParts = arg.split(':')[1].split('=')
				thisArg += [part.strip() for part in lastParts if part]
			else:
				thisArg.append(arg.split(':')[1].strip())
				thisArg.append(None)
		elif '=' in arg:
			parts = [part.strip() for part in arg.split('=') if part and part.strip()]
			thisArg = (parts[0], None, parts[1])
		else:
			thisArg = (arg, None, None)
		argslist.append(thisArg)

	del args

	try:
		returnType = funcname.index("->", argsEnd)
		returnType = funcname[returnType+1:].strip()[:-1].rstrip()
	except ValueError:
		returnType = None

	docstring = getContiguousComment('Python', contents[1:])
	if docstring is None:
		docstring = ''

	identRegex = re.compile(r'"""|#|%s' % "'''")

	try:
		indentation = contents[1][:identRegex.search(contents[1]).start()]
	except AttributeError as e:
		print(contents[1])
		raise e

	numLines = 1 + len(docstring)
	for line in contents[numLines:]:
		if not line.startswith(indentation):
			break
		numLines += 1

	output = [processComment('\n'.join(docstring))]

	if argslist:
		output.append(r"\\\textbf{\textit{Arguments:}}")
		output.append(r"\begin{itemize}")
		for arg in argslist:
			outarg = [r"\item{}\identifier{%s}" % arg[0]]
			if arg[1] is not None:
				outarg.append(r" - \identifier{%s}" % arg[1])
			if arg[2] is not None:
				outarg.append(r" - \textit{Default:} \identifier{%s}" % arg[2])
			output.append(''.join(outarg))
		output.append(r"\end{itemize}")

	if returnType is not None:
		output.append(r"\textbf{\textit{Returns:} %s" % returnType)

	return funcname, '\n'.join(output), numLines


def processPythonClass(contents: typing.List[str]) -> typing.Tuple[str, str, int]:
	"""
	Processes a Python class.

	Returns the class name, the class docstring, and the number of lines contained in the class.
	"""
	# global COMMENT_DELIMS

	clsName = contents[0][6:].lstrip()
	try:
		clsName = clsName[:clsName.index('(')].rstrip()
	except ValueError:
		raise ValueError("'(' not found in class decl on line '%s'" % contents[0])

	docstring = getContiguousComment('Python', contents[1:])
	if docstring is None:
		docstring = ''

	identRegex = re.compile(r'"""|#|%s' % "'''")

	indentation = contents[1][:identRegex.search(contents[1]).start()]

	numLines = 1 + len(docstring)
	for line in contents[numLines:]:
		if not line.startswith(indentation):
			break
		numLines += 1

	return clsName, processComment('\n'.join(docstring)), numLines


# A mapping of syntax names to functions that process functions for that syntax.
FUNCTION_PROCESSORS = {'Python': processPythonFunction}

# A mapping of syntax names to functions that process datatype declarations for that syntax.
# Note that I don't support `collections` or `typing` `NewType`s/`NamedTuple`s
DATATYPE_PROCESSORS = {'Python': processPythonClass}


def extractPythonDocumentation(moduleName: str, contents: str) -> str:
	"""
	Processes a single python module for extractable documentation

	Pulls docstrings from applicable objects and comments immediately preceding global
	identifiers (that don't have docstrings) and class data members.

	Returns LaTeX code that outputs documentation for this module.
	"""
	global ASSIGNMENT_PATTERNS, FUNCTION_PROCESSORS

	#Underscores are the bane of my existence
	safeName = moduleName.replace('_', 'UnDeRsCoRe')

	latex = [r"\subsection{%s}\label{sec:py:%s}" % (moduleName.replace('_', r'\_'), safeName)]

	# Get all lines that are not empty or just whitespace (and eliminate trailing whitespace)
	contentLines = []
	currentLine = ''
	for line in contents.strip().split('\n'):
		if line and line.strip():
			# I assume that lines ending with commas are continued tuples/argument lists
			if line.endswith('\\'):
				currentLine += ' ' + line[:-1]
			elif line.endswith(','):
				currentLine += ' ' + line
			else:
				contentLines.append((currentLine + line).strip())
				currentLine = ''

	# contentLines = [x.rstrip() for x in contents.strip().split('\n') if x and x.strip()]

	# Check for module docstring/top-level comments (first line could be shebang)
	if contentLines[0].startswith("#!"):
		_ = contentLines.pop(0)

	moduleDocstring = getContiguousComment('Python', contentLines)
	processedLines = len(moduleDocstring)

	latex.append(processComment('\n'.join(moduleDocstring)))

	constants, functions, classes = {}, {}, {}
	while processedLines < len(contentLines):
		comments = getContiguousComment('Python', contentLines[processedLines:])
		if comments is None:
			# print(contentLines[processedLines])
			if contentLines[processedLines].startswith('def'):
				funcname,\
				docstring,\
				containedLines = FUNCTION_PROCESSORS['Python'](contentLines[processedLines:])
				functions[funcname] = docstring
				processedLines += containedLines
			elif contentLines[processedLines].startswith("class"):
				classname,\
				docstring,\
				containedLines = DATATYPE_PROCESSORS['Python'](contentLines[processedLines:])
				classes[classname] = docstring
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
			processedLines += len(comments) if comments else 1 # This is a dirty hack. Much like the rest of the code

	if constants:
		latex.append(r"\subsubsection{Constants}\label{sec:py:%s:constants}" % safeName)
		latex.append(r"\begin{itemize}")
		for constant in sorted(constants):
			latex.append(r"\item{}\identifier{%s}\\" % constant.replace('_', r'\_'))
			if constants[constant]:
				latex.append("\t%s\\\\" % constants[constant])

		latex.append(r"\end{itemize}")

	if functions:
		latex.append(r"\subsubsection{Functions}\label{sec:py:%s:funcs}" % safeName)
		latex.append(r"\begin{itemize}")
		for func in sorted(functions):
			latex.append(r"\item{}\identifier{%s}\\" % func.replace('_', r'\_'))
			latex.append("\t%s\\\\" % functions[func])

		latex.append(r"\end{itemize}")

	if classes:
		latex.append(r"\subsubsection{Classes}\label{sec:py:%s:classes}" % safeName)
		latex.append(r"\begin{itemize}")
		for cls in sorted(classes):
			latex.append(r"\item{}\identifier{%s}\\" % cls.replace('_', r'\_'))
			latex.append("\t%s\\\\" % classes[cls])
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

	packages, modules = [], {}
	for path in args.PATH:
		if not os.path.exists(path):
			print("File/Directory not found: '%s' attempting to continue..."%path, file=sys.stderr)
		elif os.path.isfile(path):
			modules[os.path.basename(path)] = path
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

	for module in sorted(modules):
		try:
			fname, output = handleFile(modules[module])
			#output = output.replace('_', r'\_')
		except EOFError as e:
			print(e, "(file: '%s'" % module, ')', file=sys.stderr)
		except Exception as e:
			print("Generic Error in file '%s':" % module, e, file=sys.stderr)
		else:
			with open(os.path.join(outputDir, fname), 'w') as outfile:
				outfile.write(output)

			outputFiles.add(fname)

	with open(os.path.join(outputDir, 'index.tex'), 'w') as idxfile:
		idxfile.write('\n'.join(r'\input{"%s/%s"}' % (outputDir, outputFile) for outputFile in sorted(outputFiles)))

	print("Done. Output in '%s' in files: " % outputDir)
	for file in outputFiles:
		print("\t", file)


if __name__ == '__main__':
	main()
