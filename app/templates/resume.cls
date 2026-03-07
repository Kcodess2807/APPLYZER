%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Fixed Resume Class
% Based on Medium Length Professional CV Template
% Fixed common issues and improved compatibility
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\ProvidesClass{resume}[2024/01/01 v1.0 Fixed Resume class]

\LoadClass[11pt,letterpaper]{article} % Font size and paper type

\RequirePackage[parfill]{parskip} % Remove paragraph indentation
\RequirePackage{array} % Required for boldface tabular columns
\RequirePackage{ifthen} % Required for ifthenelse statements

\pagestyle{empty} % Suppress page numbers

%----------------------------------------------------------------------------------------
%	DEFINE LENGTHS
%----------------------------------------------------------------------------------------

\newlength{\addressskip}
\setlength{\addressskip}{\smallskipamount}

\newlength{\sectionlineskip} 
\setlength{\sectionlineskip}{\medskipamount}

\newlength{\nameskip}
\setlength{\nameskip}{\bigskipamount}

\newlength{\sectionskip}
\setlength{\sectionskip}{\medskipamount}

%----------------------------------------------------------------------------------------
%	HEADINGS COMMANDS
%----------------------------------------------------------------------------------------

\def\name#1{\def\@name{#1}} % Defines the \name command to set name
\def\@name{} % Sets \@name to empty by default

\def\addressSep{$\diamond$} % Set default address separator to a diamond

% Address variables
\let\@addressone\relax
\let\@addresstwo\relax
\let\@addressthree\relax

% \address command can be used to set addresses
\def\address#1{
  \@ifundefined{@addresstwo}{
    \def\@addresstwo{#1}
  }{
  \@ifundefined{@addressthree}{
  \def\@addressthree{#1}
  }{
     \def\@addressone{#1}
  }}
}

% \printaddress is used to style an address line
\def\printaddress#1{
  \begingroup
    \def\\{\addressSep\ }
    \centerline{#1}
  \endgroup
  \par
  \vspace{\addressskip}
}

% \printname is used to print the name as a page header
\def\printname{
  \begingroup
    \hfil{\MakeUppercase{\huge\bfseries\@name}}\hfil
    \vspace{\nameskip}
    \par
  \endgroup
}

%----------------------------------------------------------------------------------------
%	PRINT THE HEADING LINES
%----------------------------------------------------------------------------------------

\let\ori@document=\document
\renewcommand{\document}{
  \ori@document  % Begin document
  \printname % Print the name specified with \name
  \@ifundefined{@addressone}{}{ % Print the first address if specified
    \printaddress{\@addressone}}
  \@ifundefined{@addresstwo}{}{ % Print the second address if specified
    \printaddress{\@addresstwo}}
  \@ifundefined{@addressthree}{}{ % Print the third address if specified
    \printaddress{\@addressthree}}
}

%----------------------------------------------------------------------------------------
%	SECTION FORMATTING
%----------------------------------------------------------------------------------------

% Defines the rSection environment for the large sections within the CV
\newenvironment{rSection}[1]{ % 1 input argument - section name
  \vspace{\sectionskip}
  \MakeUppercase{\bfseries #1} % Section title
  \vspace{\sectionlineskip}
  \hrule % Horizontal line
  \begin{list}{}{ % List for each individual item in the section
    \setlength{\leftmargin}{1.5em} % Margin within the section
  }
  \item[]
}{
  \end{list}
}

%----------------------------------------------------------------------------------------
%	WORK EXPERIENCE FORMATTING  
%----------------------------------------------------------------------------------------

\newenvironment{rSubsection}[4]{ % 4 input arguments - company name, year(s) employed, job title and location
 {\bfseries #1} \hfill {#2} % Bold company name and date on the right
 \ifthenelse{\equal{#3}{}}{}{ % If the third argument is not specified, don't print the job title and location line
  \\
  {\em #3} \hfill {\em #4} % Italic job title and location
  }\smallskip
  \begin{list}{$\cdot$}{\leftmargin=0em} % \cdot used for bullets, no indentation
   \itemsep -0.5em \vspace{-0.5em} % Compress items in list together for aesthetics
  }{
  \end{list}
  \vspace{0.5em} % Some space after the list of bullet points
}