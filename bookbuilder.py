"""\

Book Builder.

Usage:
    bookbuilder.py status
    bookbuilder.py build [<format>...]
    bookbuilder.py -h --help

Options:
    status            # Shows status of every chapter file in the current repo

    build <format>... # Transform chapters to specified output formats. If no
                      # formats are specified, all implemented formats will be
                      # used. These can be one or more of (tex, html )

    -h --help         # print help message

Examples:
    bookbuilder.py status
    bookbuilder.py build
    bookbuilder.py build tex
    bookbuilder.py build tex html


"""

try:
    from docopt import docopt
except ImportError:
    logging.error("Please install docopt:\n sudo pip install docopt")

import libbookbuilder

if __name__ == "__main__":
    arguments = docopt(__doc__)
    # TODO remove this print statement
    print(arguments)
    # Initialise the book. This will read the cache object in .bookbuilder
    # and create it if it is not there
    Book = libbookbuilder.book()

    if arguments['status']:
        Book.show_status()
    elif arguments['build']:
        print("Building book")
        formats = arguments['<format>']
        if not formats:
            formats = ['tex', 'html']
        for f in formats:
            print("Transforming book to {f}".format(f=f))

    # Save the cache object again 
    Book.write_cache()
