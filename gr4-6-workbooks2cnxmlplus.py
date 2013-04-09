#!/usr/bin/env python

import sys

from lxml import etree

if __name__ == "__main__":
    inputxml = sys.argv[1]
    xml = etree.parse(inputxml)


    # remove /document/title
    title = xml.find('.//title')
    if title is not None:
        if title.getparent().tag == 'document':
            title.getparent().remove(title)

    # note type='teachersguide'
    #   convert to <teachers-guide>
    for notetg in xml.findall('.//note'):
        if notetg.attrib['type'] is not None:
            if 'teachersguide' in notetg.attrib['type']:
                notetg.tag = 'teachers-guide'
                del notetg.attrib['type']

    # //figure/media/image + //figure/caption
    for figure in xml.findall('.//figure'):
        if figure.find('media').tag == 'media':
            media = figure.find('media')
        else:
            media = None
            
        if figure.find('caption') is not None:
            caption = figure.find('caption')
        else:
            caption = None
        
        newfigure = etree.Element('figure')
        figuretype = etree.Element('type')
        figuretype.text = 'figure'
        newfigure.append(figuretype)
        newfigure.tail = '\n'

        if media is not None:
            if media.find('image') is not None:
                image = media.find('image')
                src = etree.Element('src')
                src.text = image.attrib['src']
                image.append(src)

        if image is not None:
            newfigure.append(image)
        if caption is not None:
            newfigure.append(caption)


        # check if figure is inside a <para>, if so, fix it.
        if figure.getparent().tag == 'para':
            para = figure.getparent()
            if (para.text is None) or (para.text.strip() == ''):
                para.getparent().replace(para, newfigure)
        else:
            figure.getparent().replace(figure, newfigure)

    # //note
    for note in xml.findall('.//note'):
        if (note.text is not None) or (note.text.strip()!=''):
            para = etree.Element('para')

    print etree.tostring(xml, encoding="utf-8", xml_declaration=True)

