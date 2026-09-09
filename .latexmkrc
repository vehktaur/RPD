$pdf_mode = 1;              # pdflatex
$bibtex_use = 2;           # run bibtex, clean .bbl
$out_dir = 'build';
$clean_ext = 'bbl nav out snm synctex.gz run.xml bcf';

# With $out_dir set, latexmk runs bibtex from inside build/, so kpathsea
# cannot see ./references.bib and silently falls back to an unrelated
# references.bib shipped with MiKTeX (feupphdteses) -- every citation then
# comes back undefined, with no error beyond a bibtex "didn't find a
# database entry" warning.
#
# Put the project directory first on BIBINPUTS: ".." for the bibtex run
# inside build/, "." for a run from the project root. Keep these relative
# -- an absolute path from getcwd() comes out MSYS-style ("/c/Users/...")
# when latexmk is launched from Git Bash, which kpathsea cannot resolve.
# The trailing separator appends the normal search path after ours.
$ENV{'BIBINPUTS'} = join($search_path_separator, '..', '.', $ENV{'BIBINPUTS'} // '');
