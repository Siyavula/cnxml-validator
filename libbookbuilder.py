import os
import errno
import logging
import hashlib
import ast
import subprocess
import shutil

import lxml
from lxml import etree

try:
    from termcolor import colored
except ImportError:
    logging.error("Please install termcolor:\n sudo pip install termcolor")

import XmlValidator

DEBUG = False


def print_debug_msg(msg):
    '''prints a debug message'''
    print(colored("DEBUG: {msg}".format(msg=msg), "yellow"))


def mkdir_p(path):
    ''' mkdir -p functionality
    from:
    http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
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
        self.has_changed = True
        self.valid = None
        self.output_formats = ['tex', 'html']

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
        with open(self.file, 'r') as f:
            content = f.read()

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
                self.has_changed = True
            else:
                # file is valid, no validation required.
                self.valid = True
                self.hash = current_hash
                self.has_changed = False

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

        sets self.valid to True or False depending on the outcome
        '''
        print("Validating {f}".format(f=self.file))

        # create an instance of the Validator
        specpath = os.path.join(os.path.dirname(__file__), 'spec.xml')
        xmlValidator = XmlValidator.XmlValidator(open(specpath, 'rt').read())
        with open(self.file, 'r') as xmlfile:
            xml = xmlfile.read()
            try:
                xmlValidator.validate(xml)
                self.valid = True
            except XmlValidator.XmlValidationError as Err:
                print(Err)
                self.valid = False

    def __cnxmlplus_preprocess(self):
        ''' This is an internal method for the chapter class that tweaks the
        cnxmlplus before it is converted to one of the output formats e.g.
        image links are changed to point one folder up so that the output files
        in the build folder points to where the current images are located.

        This method is called from the convert method.

        '''
        with open(self.file, 'r') as f:
            tweaked_cnxmlplus = etree.XML(f.read())

        # TODO add stuff here for tweaking

        return tweaked_cnxmlplus

    def __copy_images(self, build_folder, output_path, output_format):
        ''' Find all images referenced in the cnxmlplus document and copy them
        to their correct relative places in the build folder.

        '''
        with open(self.file) as f:
            xml = etree.XML(f.read())

        if output_format == 'tex':
            # if it is tex, we can copy the images referenced in the cnxmlplus
            # directly to the build/tex folder
            for image in xml.findall('.//image'):
                # find the src, it may be an attribute or a child element
                if 'src' in image.attrib:
                    src = image.attrib['src']
                else:
                    src = image.find('.//src').text.strip()
                dest = os.path.join(build_folder, output_format, src)
                if DEBUG:
                    print_debug_msg("Copying {src} --> {dest}"
                                    .format(src=src,
                                            dest=dest))
                if not os.path.exists(dest):
                    try:
                        mkdir_p(os.path.dirname(dest))
                    except OSError:
                        msg = colored("WARNING! {dest} is not allowed!"
                                      .format(dest=dest),
                                      "magenta")
                        print(msg)

                if os.path.exists(src):
                    shutil.copy(src, dest)
                else:
                    print(colored("WARNING! {src} cannot be found!"
                                  .format(src=src), "magenta"))

        elif output_format == 'html':
            # if it is html the converted html will contain more images than
            # the cnxmlplus references because pstricks and tikz figures are
            # converted to images. We need to calculate the hashes in the same
            # way that the tohtml.py script does and copy the files from the
            # _plone_ignore_ folder to build/html
            pass

    def __tolatex(self):
        ''' Convert this chapter to latex
        '''
        tolatexpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'tolatex.py')
        myprocess = subprocess.Popen(["python", tolatexpath, self.file],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        latex, err = myprocess.communicate()

        return latex

    def __tohtml(self):
        ''' Convert this chapter to latex
        '''
#       tohtmlpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                                 'tohtml.py')
#       myprocess = subprocess.Popen(["python", tohtmlpath, self.file],
#                                    stdout=subprocess.PIPE)
#       html, err = myprocess.communicate()

        html = ""
        return html

    def convert(self, build_folder, output_format):
        ''' Convert the chapter to the specified output format and write the
        the build folder: {build_folder}/{output_format}/self.file.{format}
        e.g. build/tex/chapter1.cnxmlplus.tex

        output_format: one  of 'tex', 'html'
        '''
        conversion_functions = {'tex': self.__tolatex, 'html': self.__tohtml}

        for outformat in output_format:
            # make sure we're not trying anything funny here
            try:
                assert(outformat in ['tex', 'html'])
            except AssertionError:
                logging.error("Output format must be one of {f}"
                              .format(f=','.join(self.output_formats)))

            # convert this chapter to the specified format
            # call the converted method
            output_path = os.path.join(build_folder, outformat,
                                       self.file +
                                       '.{f}'.format(f=outformat))
            # only try this on valid cnxmlplus files
            if self.valid:
                # run the conversion only if the file has changed OR if it
                # doesn't exist (it may have been deleted manually)
                if (self.has_changed) or (not os.path.exists(output_path)):
                    mkdir_p(os.path.dirname(output_path))
                    converted = conversion_functions[outformat]()
                    print("Converting {ch} to {form}".format(ch=self.file,
                                                             form=outformat))
                    # copy the images to the build folder
                    self.__copy_images(build_folder, output_path, outformat)

                    with open(output_path, 'w') as f:
                        f.write(converted)
                # file has not changed AND the file exists
                elif (not self.has_changed) and (os.path.exists(output_path)):
                    print("{f} {space} done".format(f=self.file,
                                                    space=' ' *
                                                    (40 - len(self.file))))

        return

    def __str__(self):
        chapno = str(self.chapter_number).ljust(4)
        return "{number} {title}".format(number=chapno, title=self.title)


class book:

    ''' Class to represent a whole book
    '''

    def __init__(self):
        self.repo_folder = os.path.abspath(os.curdir)
        self.build_folder = os.path.join(self.repo_folder, 'build')

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
        # make it a dict
        cache_object = {}

        # create a key for chapters
        cache_object['title'] = None
        cache_object['chapters'] = {}

        return cache_object

    def convert(self, formats=['tex', 'html']):
        ''' Convert all the chapters to the given output formats.

        Default output format is both tex and html
        '''

        for chapter in self.chapters:
            chapter.convert(self.build_folder, formats)
