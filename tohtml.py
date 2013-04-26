from lxml import etree
import sys, os
import argparse

from xml.sax.saxutils import unescape
from XmlValidator import XmlValidator
import utils


MY_PATH = os.path.realpath(os.path.dirname(__file__))

# Parse command line arguments
argumentParser = argparse.ArgumentParser(description='Convert a CNXML+ document to a LaTeX document.')
argumentParser.add_argument(
    '--spec', dest='specFilename',
    default="spec.xml",
    help='Filename of the XML specification document.')
argumentParser.add_argument(
    '--audience', dest='audience',
    default="learner",
    help='Target audience of the transform ( learner | teacher | correct ).')
argumentParser.add_argument(
    '-o', dest='outputFilename',
    help='Write output to given filename rather than stdout.')
argumentParser.add_argument(
    'filename', nargs='+',
    help='One or more filenames to process.')
commandlineArguments = argumentParser.parse_args()

if commandlineArguments.outputFilename is None:
    outputFile = sys.stdout
else:
    outputFile = open(commandlineArguments.outputFilename, 'wt')

validator = XmlValidator(open(os.path.join(MY_PATH, commandlineArguments.specFilename),'rt').read())

mathml_transform = utils.MmlTex()

conversionFunctions = {} # Cache
def cache_conversion_function(iSpec):
    global conversionFunctions, validator, utils, commandlineArguments

    if isinstance(iSpec, basestring):
        # xpath given rather than node
        specEntry = None
        for child in validator.spec:
            xpathNode = child.find('xpath')
            if xpathNode is None:
                continue
            if xpathNode.text == iSpec:
                specEntry = child
                break
    else:
        specEntry = iSpec

    conversionFunction = conversionFunctions.get(specEntry)

    if conversionFunction is None:
        # Cache conversion function
        conversionFunctionNodes = specEntry.xpath('.//conversion-callback[contains(@name, "html") and contains(@name, "%s")]'%commandlineArguments.audience)
        if len(conversionFunctionNodes) == 0:
            utils.warning_message('No conversion entry for ' + specEntry.find('xpath').text)
            conversionFunctionSource = 'conversionFunction = lambda self: None'
        else:
            if len(conversionFunctionNodes) != 1:
                utils.error_message('More than 1 conversion entry for ' + specEntry.find('xpath').text)
            conversionFunctionSource = conversionFunctionNodes[0].text.strip()
            if conversionFunctionSource == '':
                conversionFunctionSource = 'conversionFunction = lambda self: None'
            else:
                conversionFunctionSource = 'def conversionFunction(self):\n' + '\n'.join(['\t' + line for line in conversionFunctionSource.split('\n')]) + '\n'

        from lxml import etree
        import utils
        from siyavula.transforms import pspicture2png, tikzpicture2png, LatexPictureError
        localVars = {
            'etree': etree,
            'utils': utils,
            'convert_using': convert_using,
            'warning_message': utils.warning_message,
            'error_message': utils.error_message,
            'mathml_transform': mathml_transform,
            'escape_latex': utils.escape_latex,
            'latex_math_function_check': utils.latex_math_function_check,
            'convert_image': convert_image,
            'pspicture2png': pspicture2png,
            'tikzpicture2png': tikzpicture2png,
        }
        exec(conversionFunctionSource, localVars)
        conversionFunction = localVars['conversionFunction']
        conversionFunctions[specEntry] = conversionFunction

    return conversionFunction

def convert_using(iNode, iPath):
    f = cache_conversion_function(iPath)
    return f(iNode)

def convert_image(iSourceFilename, iDestinationFilename):
    import subprocess
    p = subprocess.Popen(['convert', iSourceFilename, iDestinationFilename])
    p.wait()

def traverse(iNode, iValidator):
    global conversionFunctions
    
    children = iNode.getchildren()
    for child in children:
        traverse(child, iValidator)

    # Get associated conversion function
    specEntry = iValidator.documentSpecEntries.get(iNode)
    if specEntry is None:
        utils.error_message('Unhandled element at ' + utils.get_full_dom_path(iNode, iValidator.spec))
    conversionFunction = cache_conversion_function(specEntry)
    parent = iNode.getparent()
    try:
        converted = conversionFunction(iNode)
    except TypeError as TE:
        print TE, iNode.tag, parent.tag, iNode.sourceline

    if isinstance(converted, basestring):
        if parent is None:
            return unescape(converted)
        else:
            from lxml import etree
            dummyNode = etree.Element('dummy')
            dummyNode.text = unescape(converted)
            utils.etree_replace_with_node_list(parent, iNode, dummyNode)
    elif converted is not None:
        if parent is None:
            return unescape(converted)
        else:
            utils.etree_replace_with_node_list(iNode.getparent(), iNode, converted)


for filename in commandlineArguments.filename:
    if filename == '-':
        fp = sys.stdin
    else:
        fp = open(filename,'rt')
    validator.validate(
        fp.read(),
        iCleanUp=True)
    document = validator.dom

    #print etree.tostring(traverse(document, spec), encoding="utf-8", xml_declaration=True)
    print '''<!DOCTYPE html>
<html>
  <head>
    <title>Hello HTML</title>
    <script type="text/javascript"
        src="mathjax/MathJax.js?config=TeX-AMS_HTML">
    </script>
    <style type="text/css" >
p {
font-family:Arial,Helvetica,sans-serif;
}

span.smallcaps {font-variant: small-caps;}
span.normal {font-variant: normal;}
span.underline {text-decoration:underline;} 
    </style>
  </head>
  <body>
    %s
  </body>
</html>'''% traverse(document, validator).encode('utf-8')
    outputFile.flush()
