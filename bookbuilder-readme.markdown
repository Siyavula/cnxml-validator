Bookbuilder
===========

Bookbuilder is a tool that automates validation and conversion of Siyavula
cnxmlplus content to LaTeX and soon HTML for web and mobile and Epub3.



## Installation

Installation instructions for Ubuntu 12.04 (and possibly newer versions of
Ubuntu).  You need `git`:

    sudo apt-get install git

Bookbuilder is part of the cnxml-validator repo. Make a clone of the git repository:

    git clone git@github.com:Siyavula/cnxml-validator.git


You need the following packages installed for `python`:
    
    * termcolor
    * lxml
    * docopt

To install them:

    sudo apt-get install python-lxml
    sudo pip install termcolor
    sudo pip install docopt




## Usage

bookbuilder is meant to be run in die repository where the book cnxmlplus
content lives e.g.

    user@computer:/path/to/book/$ ll
    total 2168
    drwx------  8 user user   4096 Jul 25 14:31 ./
    drwx------ 29 user user   4096 Dec  6  2013 ../
    -rw-rw-r--  1 user user 190947 Jul 24 12:28 01-algebraic-expressions.cnxmlplus
    -rw-rw-r--  1 user user  42649 Jul 23 15:53 02-exponentials.cnxmlplus
    -rw-rw-r--  1 user user  44796 Jul 23 16:38 03-number-patterns.cnxmlplus
    -rw-rw-r--  1 user user 112762 Jul 18 11:36 04-equations-and-inequalities.cnxmlplus
    -rw-rw-r--  1 user user 105511 Jul 18 11:36 05-trigonometry.cnxmlplus
    -rw-rw-r--  1 user user 357151 Jul 18 11:36 06-functions.cnxmlplus
    -rw-rw-r--  1 user user 244738 Jul 18 11:36 07-euclidean-geometry.cnxmlplus
    -rw-rw-r--  1 user user 109271 Jul 15 11:48 08-analytical-geometry.cnxmlplus
    -rw-rw-r--  1 user user  72264 Jul 18 11:36 09-finance-and-growth.cnxmlplus
    -rw-rw-r--  1 user user 177904 Jul 18 11:36 10-statistics.cnxmlplus
    -rw-rw-r--  1 user user  40934 Jul 18 11:36 11-trigonometry.cnxmlplus
    -rw-rw-r--  1 user user  86199 Jul 18 11:36 12-euclidean-geometry.cnxmlplus
    -rw-rw-r--  1 user user 185455 Jul 18 11:36 13-measurement.cnxmlplus
    -rw-rw-r--  1 user user 132501 Jul 18 11:36 14-probability.cnxmlplus
    -rw-rw-r--  1 user user 166550 Jul 22 12:03 15-exercise-solutions.cnxmlplus
    -rw-rw-r--  1 user user    560 Jul  1 16:31 comment-exercises.py
    -rw-rw-r--  1 user user     78 Jul  1 16:31 comment-exercises.sh
    drwx------  8 user user   4096 Jul 24 12:27 .git/
    -rw-------  1 user user     28 Jan 10  2013 .gitignore
    drwx------  2 user user   4096 Jul 23 13:56 images/
    drwx------  2 user user   4096 Jan 10  2013 includes/
    drwx------  2 user user   4096 Jul  2 15:08 mmltex/
    -rw-rw-r--  1 user user   4323 Jul  3 11:20 oldcnxml2newcnxml.py
    -rw-rw-r--  1 user user     78 Jul  2 13:28 oldcnxml2newcnxml.sh
    drwx------  3 user user   4096 Nov  1  2013 _plone_ignore_/
    drwx------  2 user user   4096 Jan 10  2013 presentations/
    -rw-rw-r--  1 user user  48841 Jul 23 15:06 test.tex
    -rw-rw-r--  1 user user    716 Jul 24 12:04 texput.log
    -rw-rw-r--  1 user user    115 Jul  2 13:30 tolatex.sh
    -rw-rw-r--  1 user user   4680 Nov 11  2013 updatecnxml.py



When bookbuilder is run inside a folder for the first time, it creates a folder
called `.bookbuilder` which contains (at the moment) only a single file that
is used to save caching information.

### status
To get the status of your book repository, use the `status` argument:

    user@computer:/path/to/book/$ python ~/programming/cnxml-validator/bookbuilder.py status
    Creating .bookbuilder folder
    Validating 01-algebraic-expressions.cnxmlplus
    Validating 02-exponentials.cnxmlplus
    Validating 03-number-patterns.cnxmlplus
    Validating 04-equations-and-inequalities.cnxmlplus
    Validating 05-trigonometry.cnxmlplus
    Validating 06-functions.cnxmlplus
    Validating 07-euclidean-geometry.cnxmlplus
    Validating 08-analytical-geometry.cnxmlplus
    Validating 09-finance-and-growth.cnxmlplus
    Validating 10-statistics.cnxmlplus
    Validating 11-trigonometry.cnxmlplus
    Validating 12-euclidean-geometry.cnxmlplus
    Validating 13-measurement.cnxmlplus
    Validating 14-probability.cnxmlplus
    Validating 15-exercise-solutions.cnxmlplus

    Ch.  Valid     File
    -------------------------------------------------------------------------------
    1      OK      01-algebraic-expressions.cnxmlplus
    2      OK      02-exponentials.cnxmlplus
    3      OK      03-number-patterns.cnxmlplus
    4      OK      04-equations-and-inequalities.cnxmlplus
    5      OK      05-trigonometry.cnxmlplus
    6      OK      06-functions.cnxmlplus
    7      OK      07-euclidean-geometry.cnxmlplus
    8      OK      08-analytical-geometry.cnxmlplus
    9      OK      09-finance-and-growth.cnxmlplus
    10     OK      10-statistics.cnxmlplus
    11     OK      11-trigonometry.cnxmlplus
    12     OK      12-euclidean-geometry.cnxmlplus
    13     OK      13-measurement.cnxmlplus
    14     OK      14-probability.cnxmlplus
    15     OK      15-exercise-solutions.cnxmlplus
    -------------------------------------------------------------------------------


### converting your book to LaTeX

To convert a repository to LaTeX use the `build tex` argument:

    user@computer:/path/to/book/$ python ~/programming/cnxml-validator/bookbuilder.py build tex
    Building book
    Converting 01-algebraic-expressions.cnxmlplus to tex
    Converting 02-exponentials.cnxmlplus to tex
    Converting 03-number-patterns.cnxmlplus to tex
    Converting 04-equations-and-inequalities.cnxmlplus to tex
    Converting 05-trigonometry.cnxmlplus to tex
    Converting 06-functions.cnxmlplus to tex
    Converting 07-euclidean-geometry.cnxmlplus to tex
    Converting 08-analytical-geometry.cnxmlplus to tex
    Converting 09-finance-and-growth.cnxmlplus to tex
    Converting 10-statistics.cnxmlplus to tex
    Converting 11-trigonometry.cnxmlplus to tex
    Converting 12-euclidean-geometry.cnxmlplus to tex
    Converting 13-measurement.cnxmlplus to tex
    Converting 14-probability.cnxmlplus to tex
    Converting 15-exercise-solutions.cnxmlplus to tex


Once you have run the `build` argument there should be a folder in your current
folder called `build` which should contain a `tex` folder. Inside that folder
you should your tex files as well as any image files linked to from within 
your cnxmlplus files:

    user@computer:/path/to/book$ cd build/tex/
    user@computer:/path/to/book/build/tex$ ls -l
    total 828
    -rw-rw-r-- 1 user user  48842 Jul 25 14:36 01-algebraic-expressions.cnxmlplus.tex
    -rw-rw-r-- 1 user user  14961 Jul 25 14:36 02-exponentials.cnxmlplus.tex
    -rw-rw-r-- 1 user user  18643 Jul 25 14:36 03-number-patterns.cnxmlplus.tex
    -rw-rw-r-- 1 user user  42145 Jul 25 14:36 04-equations-and-inequalities.cnxmlplus.tex
    -rw-rw-r-- 1 user user  32049 Jul 25 14:36 05-trigonometry.cnxmlplus.tex
    -rw-rw-r-- 1 user user 127463 Jul 25 14:36 06-functions.cnxmlplus.tex
    -rw-rw-r-- 1 user user  85163 Jul 25 14:36 07-euclidean-geometry.cnxmlplus.tex
    -rw-rw-r-- 1 user user  39218 Jul 25 14:36 08-analytical-geometry.cnxmlplus.tex
    -rw-rw-r-- 1 user user  33558 Jul 25 14:36 09-finance-and-growth.cnxmlplus.tex
    -rw-rw-r-- 1 user user  64761 Jul 25 14:36 10-statistics.cnxmlplus.tex
    -rw-rw-r-- 1 user user  19354 Jul 25 14:36 11-trigonometry.cnxmlplus.tex
    -rw-rw-r-- 1 user user   9227 Jul 25 14:36 12-euclidean-geometry.cnxmlplus.tex
    -rw-rw-r-- 1 user user 113065 Jul 25 14:36 13-measurement.cnxmlplus.tex
    -rw-rw-r-- 1 user user  46481 Jul 25 14:36 14-probability.cnxmlplus.tex
    -rw-rw-r-- 1 user user 119117 Jul 25 14:36 15-exercise-solutions.cnxmlplus.tex
    drwxrwxr-x 2 user user   4096 Jul 25 14:36 images



