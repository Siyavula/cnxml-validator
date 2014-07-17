"""Usage: bookbuilder.py

"""

import os
import sys
import logging

from lxml import etree

try:
    from docopt import docopt
except ImportError:
    logging.error("Please install docopt")


class chapter:
    ''' Class to represent a single chapter
    '''
    def __init__(self, cnxmlplusfile):
        ''' cnxmlplus file is the path of the file
        '''
        self.file = cnxmlplusfile
        self.chapter_number = None
        self.title = None
        self.parse_cnxmlplus()

    def parse_cnxmlplus(self):
        ''' Parse the xml file and save some information
        '''
        content = open(self.file, 'r').read()
        xml = etree.XML(content)

        # save the number
        try:
            self.chapter_number = int(self.file[0:self.file.index('-')])
        except:
            self.chapter_number = 'N/A'
            logging.warn("{file} doesn't follow naming convention CC-title-here.cnxmlplus".format(file=self.file))

        # The title should be in in an element called <title> 
        # inside a <section type="chapter"> and there should only be one in the
        # file. For now.
        chapters = xml.findall('.//section[@type="chapter"]')
        if len(chapters) > 1:
            logging.error("{filename} contains more than 1 chapter!".format(filename=self.file))
        elif len(chapters) < 1:
            logging.error("{filename} contains no chapters!".format(filename=self.file))
        else:
            self.title = chapters[0].find('.//title').text

    def __str__(self):
        return "{number} {title}".format(number=self.chapter_number, title=self.title)


class book:
    ''' Class to represent a whole book
    '''
    def __init__(self):
        self.repo_folder = os.path.abspath(os.curdir)
        self.chapters = []
        self._discover_chapters()

    def _discover_chapters(self):
        ''' Add all the .cnxmlplus files in the current folder'''

        cnxmlplusfiles = [f for f in os.listdir(os.curdir) if f.strip().endswith('.cnxmlplus')]
        if len(cnxmlplusfiles) < 1:
            logging.warn("No cnxmlplus files found in current folder")

        cnxmlplusfiles.sort()

        for cf in cnxmlplusfiles:
            self.chapters.append(chapter(cf))

    def show_chapters(self):
        ''' Print a listing of the chapters in book
        '''

        for chapter in self.chapters:
            print(chapter)
            print("  file: {filename}".format(filename=chapter.file))


if __name__ == "__main__":
    arguments = docopt(__doc__)
    Book = book()
    Book.show_chapters()
