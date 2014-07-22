import os
import sys
import logging
import subprocess
import hashlib
import ast

import lxml
from lxml import etree

try:
    from termcolor import colored
except ImportError:
    logging.error("Please install termcolor:\n sudo pip install termcolor")


def mkdir_p(path):
    ''' mkdir -p functionality
    from http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    '''
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class chapter:

    ''' Class to represent a single chapter
    '''

    def __init__(self, cnxmlplusfile, **kwargs):
        ''' cnxmlplus file is the path of the file
        '''

        # set some default attributes.
        self.file = cnxmlplusfile
        self.chapter_number = None
        self.title = None
        self.hash = None
        self.valid = None

        # set attributes from keyword arguments
        # This can be used to set precomputed values e.g. read from a cache
        for key, value in kwargs.items():
            setattr(self, key, value)

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

        if (self.hash is None) or (self.valid is False):
            self.hash = self.calculate_hash(content)
            # if the hash is None, it has not been passed from Book class and
            # hence didn't exist in the cache. Need to validate this file
            self.validate()
        else:
            # If self.hash has been set and it differs from current hash, then
            # re-validate
            current_hash = self.calculate_hash(content)
            if self.hash != current_hash:
                self.validate()
                self.hash = current_hash
            else:
                # file is valid, no validation required.
                self.valid = True
                self.hash = current_hash

        try:
            xml = etree.XML(content)
        except lxml.etree.XMLSyntaxError:
            logging.error(
                colored("{file} is not valid XML!".format(
                    file=self.file), 'red'))
            return None

        # save the number
        try:
            self.chapter_number = int(self.file[0:self.file.index('-')])
        except:
            self.chapter_number = 'N/A'
            logging.warn(
                "{file} doesn't follow naming convention \
                    CC-title-here.cnxmlplus".format(file=self.file))

        # The title should be in in an element called <title>
        # inside a <section type="chapter"> and there should only be one in the
        # file. For now.
        chapters = xml.findall('.//section[@type="chapter"]')
        if len(chapters) > 1:
            logging.error(
                "{filename} contains more than 1 chapter!".format(
                    filename=self.file))
        elif len(chapters) < 1:
            logging.error(
                "{filename} contains no chapters!".format(filename=self.file))
        else:
            self.title = chapters[0].find('.//title').text

    def info(self):
        ''' Returns a formatted string with all the details of the chapter
        '''
        info = '{ch}'.format(ch=self.chapter_number)
        info += ' ' * (4 - len(info))
        if self.valid:
            info += colored('OK'.center(8), 'green')
        else:
            info += colored('Not OK'.center(8), 'red')
        info += ' ' * (24 - len(info))
        info += '{file}'.format(file=self.file)

        return info

    def validate(self):
        ''' Run the validator on this file

        Returns 0 if file is valid and 1 if it is not
        '''
        print("Validating {f}".format(f=self.file))
        FNULL = open(os.devnull, 'w')

        validator_dir = os.path.dirname(os.path.abspath(__file__))
        validator_path = os.path.join(validator_dir, 'validate.py')
        valid = subprocess.call(
            ["python", validator_path, self.file],
            stdout=FNULL,
            stderr=subprocess.STDOUT)
        self.valid = True if valid == 0 else False

    def __str__(self):
        chapno = str(self.chapter_number).ljust(4)
        return "{number} {title}".format(number=chapno, title=self.title)


class book:

    ''' Class to represent a whole book
    '''

    def __init__(self):
        self.repo_folder = os.path.abspath(os.curdir)
        self.chapters = []
        # Read the cache and update the cache_object
        self.cache_object = self.read_cache()

        # If the object is empty, then we need to go and discover the chapters
        self._discover_chapters(self.cache_object)

    def _discover_chapters(self, cache_object):
        ''' Add all the .cnxmlplus files in the current folder'''

        files = os.listdir(os.curdir)
        cnxmlplusfiles = [
            f for f in files if f.strip().endswith('.cnxmlplus')]
        if len(cnxmlplusfiles) < 1:
            logging.warn("No cnxmlplus files found in current folder")

        cnxmlplusfiles.sort()

        for cf in cnxmlplusfiles:
            # see if this chapter occurs in the cache_object
            if cf in cache_object['chapters'].keys():
                # pass the previous hash to the chapter initialisation method
                previous_hash = cache_object['chapters'][cf]['hash']
                previous_validation_status = cache_object[
                    'chapters'][cf]['previous_validation_status']
                thischapter = chapter(
                    cf, hash=previous_hash, valid=previous_validation_status)
            else:
                # pass the prev has has None so that validation is forced
                thischapter = chapter(cf, hash=None)

                # this chapter was not in the cache_object, add an empty dict
                # for it
                cache_object['chapters'][cf] = {}

            # now update the cache_object
            cache_object['chapters'][cf]['hash'] = thischapter.hash
            cache_object['chapters'][cf][
                'previous_validation_status'] = thischapter.valid
            self.chapters.append(thischapter)

        self.write_cache()

    def show_status(self):
        ''' Print a listing of the chapters in book
        '''
        print("\nCh.  Valid     File\n" + '-' * 79)
        for chapter in self.chapters:
            print(chapter.info())
        print('-' * 79)

    def read_cache(self):
        ''' Read cache object inside the .bookbuilder/cache_object.txt

        Returns:
            None if cache_object.txt doesn't exist
            cache_object of type dict if it does

        '''

        # check whether .bookbuilder folder exists
        # and initialise it if it doesn't
        if not os.path.exists('.bookbuilder'):
            print("Creating .bookbuilder folder")
            mkdir_p('.bookbuilder')

        cache_object_path = os.path.join('.bookbuilder', 'cache_object.txt')

        if not os.path.exists(cache_object_path):
            # create one if it doesn't exist
            cache_object = self.create_cache_object()

            return cache_object
        else:
            with open(cache_object_path, 'r') as cop:
                copcontent = cop.read()
                if len(copcontent) == 0:
                    cache_object = self.create_cache_object()
                else:
                    cache_object = ast.literal_eval(copcontent)

                return cache_object

    def write_cache(self):
        ''' write cache object to the .bookbuilder folder

        '''
        cache_object_path = os.path.join('.bookbuilder', 'cache_object.txt')

        with open(cache_object_path, 'w') as cop:
            cop.write(self.cache_object.__str__())

    def create_cache_object(self):
        ''' create an empty cache_object dictionary
        '''

        cache_object = {}

        # create a key for chapters
        cache_object['title'] = None
        cache_object['chapters'] = {}

        return cache_object
