$pdf_mode = 1;
$bibtex_use = 2;
$out_dir = 'build';
$clean_ext = 'bbl nav out snm synctex.gz run.xml bcf';

$ENV{'BIBINPUTS'} = join($search_path_separator, '..', '.', $ENV{'BIBINPUTS'} // '');
