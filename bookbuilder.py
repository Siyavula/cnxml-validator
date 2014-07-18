"""Usage: bookbuilder.py

"""

import os
import sys
import logging
import subprocess
import hashlib

from lxml import etree

try:
    from docopt import docopt
except ImportError:
    logging.error("Please install docopt:\n sudo pip install docopt")

try:
    from termcolor import colored
except ImportError:
    logging.error("Please install termcolo:\n sudo pip install termcolor")

class chapter:
    ''' Class to represent a single chapter
    '''
    def __init__(self, cnxmlplusfile):
        ''' cnxmlplus file is the path of the file
        '''
        self.file = cnxmlplusfile
        self.chapter_number = None
        self.title = None
        self.hash = None

        # Run validator
        self.validate()

        # Parse the xml
        self.parse_cnxmlplus()

    def calculate_hash(self, content):
        ''' Calculates the md5 hash of the file content and returns it
        '''
        m = hashlib.md5()
        m.update(content)

        return m.hexdigest()

    def parse_cnxmlplus(self):
        ''' Parse the xml file and save some information
        '''
        content = open(self.file, 'r').read()
        self.hash = self.calculate_hash(content)
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

    def info(self):
        ''' Returns a formatted string with all the details of the chapter
        '''
        info = '{file}\n'.format(file=self.file)

        for name, attribute in [('Chapter', self.chapter_number),
            ("Title", self.title),
            ("Valid", self.valid),
            ("Hash", self.hash)]:
            info += '{name}'.format(name=name).ljust(8) + '{attr}\n'.format(attr=attribute)

        return info


    def __str__(self):
        chapno = str(self.chapter_number).ljust(4)
        return "{number} {title}".format(number=chapno, title=self.title)

    def validate(self):
        ''' Run the validator on this file

        Returns 0 if file is valid and 1 if it is not
        '''
        FNULL = open(os.devnull, 'w')

        validator_dir = os.path.dirname(os.path.abspath(__file__))
        validator_path = os.path.join(validator_dir, 'validate.py')
        valid = subprocess.call(["python", validator_path, self.file], stdout=FNULL, stderr=subprocess.STDOUT)
        self.valid = colored("Valid", "green") if valid == 0 else colored("Not Valid", "red")


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
            thischapter = chapter(cf)
            self.chapters.append(thischapter)
            print(thischapter.info())

    def show_chapters(self):
        ''' Print a listing of the chapters in book
        '''
        print("")
        for chapter in self.chapters:
            print(chapter.info())
        

if __name__ == "__main__":
    arguments = docopt(__doc__)
    Book = book()
    #Book.show_chapters()

