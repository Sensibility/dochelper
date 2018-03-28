\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{documentation}[2018/03/05 LaTeX class for documenting code]

% Based on the 'article' class.
\LoadClass[a4paper,12pt]{article}

% Package dependencies.
\RequirePackage{xcolor}
\RequirePackage{listings}
\RequirePackage{fontspec}
\RequirePackage{tcolorbox}
\RequirePackage[margin=1in]{geometry}
%\RequirePackage{hyperref}

%sets the default fonts
\setmainfont{Ubuntu}
\setmonofont{Ubuntu Mono}

%sets paragraph style to value contiguous command output over constant line width.
\AtBeginDocument{\raggedright}

%Define some colors
\definecolor{orchid}{HTML}{F92672}
\definecolor{sundriedClay}{HTML}{272822}
\definecolor{deepred}{rgb}{0.6,0,0}
\definecolor{stringlit}{HTML}{E6DB74}
\definecolor{secondaryKeyword}{HTML}{66D9EF}
\definecolor{monokaiGreen}{HTML}{A6E22E}
\definecolor{monokaiPurple}{HTML}{AE81FF}
\definecolor{monokaiOrange}{HTML}{FD971F}
\definecolor{offGray}{HTML}{808080}
\definecolor{comment}{rgb}{0.5,0.5,0.5}
\definecolor{keyword}{rgb}{0.8,0,0.2}
\definecolor{numberconst}{rgb}{0.58,0,0.82}
\definecolor{identifier}{rgb}{0.1,0.6,0.1}

% Inline code markup
\newtcbox{\@code}{nobeforeafter,colback=sundriedClay,boxsep=0pt,left=6pt,right=6pt,top=2pt,bottom=1pt,tcbox raise base}

\DeclareRobustCommand{\code}[1]{\@code{\small\ttfamily\color{orchid}#1}}

\lstset{% Lets the style for numeric constants and keyword groups
   backgroundcolor=\color{sundriedClay},
   literate=%
*{0}{{{\bfseries\color{monokaiPurple}{0}}}}1
{1}{{{\bfseries\color{monokaiPurple}{1}}}}1
{0x}{{{\bfseries\color{monokaiPurple}{0x}}}}1
{2}{{{\bfseries\color{monokaiPurple}{2}}}}1
{3}{{{\bfseries\color{monokaiPurple}{3}}}}1
{4}{{{\bfseries\color{monokaiPurple}{4}}}}1
{5}{{{\bfseries\color{monokaiPurple}{5}}}}1
{6}{{{\bfseries\color{monokaiPurple}{6}}}}1
{7}{{{\bfseries\color{monokaiPurple}{7}}}}1
{8}{{{\bfseries\color{monokaiPurple}{8}}}}1
{9}{{{\bfseries\color{monokaiPurple}{9}}}}1,
showstringspaces=false,
showspaces=false,
tabsize=2,
breaklines,
breakatwhitespace,
showtabs=false,
captionpos=t,
extendedchars=true,
frame=l,
framesep=4.5mm,
framexleftmargin=2.5mm,
framextopmargin=0,
framexbottommargin=0,
fillcolor=\color{sundriedClay},
rulecolor=\color{offGray},
numberstyle=\normalfont\tiny\color{white},
numbers=left,
keywordstyle=\color{orchid}\bfseries,% Primary language constructs, gets highlighted in red
keywordstyle=[2]{\color{secondaryKeyword}},% Builtins and standard functions, blue
keywordstyle=[3]{\itshape\color{monokaiGreen}},% storage modifiers, like 'class' in python
keywordstyle=[4]{\bfseries\color{monokaiPurple}},% Language constants like 'True' and 'null', purple
keywordstyle=[5]{\itshape\color{secondaryKeyword}},% format specifiers, italic blue
keywordstyle=[6]{\itshape\color{monokaiOrange}},% context-special identifiers, italic orange
identifierstyle=\color{white},
basicstyle=\footnotesize\ttfamily\color{white},,
commentstyle=\color{comment}\ttfamily,
stringstyle=\color{stringlit}\ttfamily
}

%Python language variant 3. Has some issues highlighting arithmetic operators inside of strings.
\lstdefinelanguage[3]{Python}{
   keywords={while,if,else,del,try,except,def,as,in,from,for,import,elif,finally,break,return,assert,is,and,or,not,global,nonlocal,async,continue,raise},
   morekeywords=[2]{abs,all,any,ascii,bin,bool,bytearray,bytes,callable,chr,classmethod,compile,complex,delattr,dict,dir,divmod,enumerate,eval,exec,filter,float,format,frozenset,getattr,globals,hasattr,hash,help,hex,id,input,int,isinstance,issubclass,iter,len,list,locals,map,max,memoryview,min,next,object,oct,open,ord,pow,print,property,range,repr,reversed,round,set,setattr,slice,sorted,staticmethod,str,sum,super,tuple,type,vars,zip,__import__,append,index,keys,items},
   otherkeywords={+,=,-,*,&,|,/,>,<,^,\%,:,@},
   morekeywords=[3]{class},
   morekeywords=[4]{True,False,None,NotImplemented,Ellipses,...},
   morekeywords=[5]{b,r,f,__init__,__repr__,__str__,__int__,__eq__,__ne__,__bool__,__len__,__getitem__,__iter__,OSError,AttributeError,AssertionError,Exception,IndexError,SyntaxError,FileNotFoundError,ValueError},
   morekeywords=[6]{self,cls},
   comment=[l]{\#},
   morestring=*[b]",
   morestring=*[b]',
   morestring=[s][\color{monokaiPurple}]{\{}{\}},
   morecomment=[s]{"""}{"""},
   morecomment=[s]{'''}{'''}
}

% Force page clearing before a new section
\let\oldsection\section
\renewcommand\section{\clearpage\oldsection}

% Don't put page numbers on the title page or table of contents
\let\oldmaketitle\maketitle
\renewcommand\maketitle{\pagenumbering{roman}\clearpage\oldmaketitle\thispagestyle{empty}}
\let\oldtoc\tableofcontents
\renewcommand\tableofcontents{\clearpage\oldtoc\thispagestyle{empty}\pagenumbering{arabic}\setcounter{page}{0}}

% Names of things don't necessarily belong in a \code environment.
\DeclareRobustCommand{\identifier}[1]{\texttt{\textcolor{orchid}{#1}}}
