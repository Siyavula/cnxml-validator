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

    for tg in xml.findall('.//teachersguide'):
        tg.tag = 'teachers-guide'

    # note type='teachersguide'
    #   convert to <teachers-guide>
    for notetg in xml.findall('.//note'):
        if notetg.attrib['type'] is not None:
            if 'teachersguide' in notetg.attrib['type']:
                notetg.tag = 'teachers-guide'
                del notetg.attrib['type']

    # //figure/media/image + //figure/caption
    for figure in xml.findall('.//figure'):
        if figure.find('media') is not None:
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
                newfigure.append(image)

        if caption is not None:
            newfigure.append(caption)


        # check if figure is inside a <para>, if so, fix it.
        if figure.getparent().tag == 'para':
            para = figure.getparent()
            if (para.text is None) or (para.text.strip() == ''):
                para.getparent().replace(para, newfigure)
            else:
                para.addnext(newfigure)
                para.remove(figure)
        else:
            figure.getparent().replace(figure, newfigure)

    # //note
    # the notes contain basically text, can place everything in para if not already
    for note in xml.findall('.//note'):
        para = etree.Element('para')
        if (note.text is None) or (note.text.strip() == ''):
            children = [child for child in note]
            if children is not None:
                para.text = children[0].tail
                children[0].tail = ''
                if len(children) > 1:
                    for c in children[1:]:
                        para.append(c)

                note.insert(1, para)
        else:
            for n in note:
                para.append(n)
            para.text = note.text
            notetype = note.attrib['type']
            note.clear()
            note.attrib['type'] = notetype
            note.append(para)

    # //media
    for media in xml.findall('.//media'):
        parent = media.getparent()
        children = [child for child in media]
        if parent.tag == 'para':
            parachildren = [child for child in parent]
            if len(parachildren) == 1:
                parent.tag = 'figure'
                if parent.text is not None:
                    newpara = etree.Element('para')
                    newpara.text = parent.text
                    parent.addprevious(newpara)
                    parent.text = None
                figuretype = etree.Element('type')
                figuretype.text = 'figure'
                parent.insert(0, figuretype)

            if (len(children) == 1) and (children[0].tag == 'image'):
                media.addnext(children[0])
                parent.remove(media)
    
    # //table
    for table in xml.findall('.//table'):
        del table.attrib['summary']
        del table.attrib['pgwide']

    for activity in xml.findall('.//activity'):
        # //activity type='questions'
        title = activity.find('title')
        if title is None:
            title = etree.Element('title')
            activity.insert(0, title)
        
        for exercise in activity.findall('.//exercise'):
            exercise.tag = 'exercises'
            problems = [child for child in exercise if child.tag == 'problem']
            solutions = [child for child in exercise if child.tag == 'solution']
            assert(len(problems) == len(solutions))
            ps = etree.Element('problem-set')
            for i,p in enumerate(problems):
                entry = etree.Element('entry')
                entry.append(problems[i])
                entry.append(solutions[i])
                ps.append(entry)

            exercise.clear()
            #exercise.append(header)
            exercise.append(ps)


    # exercises in lists, change to problem-set
    for lst in xml.findall('.//list'):
        exercises = lst.findall('.//item/exercise')
        if len(exercises) > 0:
            ps = etree.Element('problem-set')
            header = etree.Element('header')
            ps.append(header)
            problems = [child for child in exercises if child.tag == 'problem']
            solutions = [child for child in exercises if child.tag == 'solution']

            for i,p in enumerate(problems):
                entry = etree.Element('entry')
                entry.append(problems[i])
                entry.append(solutions[i])
                ps.append(entry)
            ex = etree.Element('exercises')
            ex.append(ps)
            lst.getparent().replace(lst, ex)

    #<solutions> must contain correct tags
    for sol in xml.findall('.//solution'):
        correct = etree.Element('correct')
        for s in sol:
            correct.append(s)
        correct.text = sol.text
        sol.clear()
        sol.append(correct)

    # fix exercises in <para>
    for ex in xml.findall('.//exercises'):
        p = ex.getparent()
        if p.tag == 'para':
            p.addprevious(ex)
            p.getparent().remove(p)
        
    # put activity/emphasis in activity/para/emphasis
    for emph in xml.findall('.//activity/emphasis'):
        p = etree.Element('para')
        p.append(emph.__copy__())
        emph.addprevious(p)
        emph.getparent().remove(emph)

    # some doc attributes we don't need
    for att in xml.getroot().attrib:
        del xml.getroot().attrib[att]
    
    print etree.tostring(xml, encoding="utf-8", xml_declaration=True)

