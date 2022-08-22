#!/usr/bin/env fontforge
import os
import sys
import json
import csv
from platform import freedesktop_os_release
import psMat

DIR_SCRIPT = os.path.dirname(os.path.realpath(__file__))
CONFIGFILE = os.path.join(DIR_SCRIPT, 'config.json')
REPLACELST = os.path.join(DIR_SCRIPT, 'replace.tsv')

def replaceGlyph(fontDst, glyphDst, fontSrc, glyphSrc=None):   
    if glyphSrc is None:
        glyphSrc = glyphDst 
    print(f"copying {glyphSrc} from {fontSrc.fontname} to {fontDst.fontname}")
    if len(glyphSrc) == 1:
        fontSrc.selection.select(ord(glyphSrc), ("unicode", None))
    elif glyphSrc.startswith('0x'):
        fontSrc.selection.select(int(glyphSrc, base=16))
    elif glyphSrc.startswith('u+') or glyphSrc.startswith('U+') or glyphSrc.startswith('0u') or glyphSrc.startswith('0U'):
        fontSrc.selection.select(int(glyphSrc[2:], base=16), ("unicode", None))
    fontSrc.copy()
    fontDst.selection.select(ord(glyphDst), ("unicode", None))
    fontDst.paste()
    if not fontDst.em == fontSrc.em:
        for g in fontDst.selection.byGlyphs:
            g.transform(psMat.scale(fontDst.em/fontSrc.em))
    
def main():
    with open(CONFIGFILE) as f:
        config = json.load(f)
    if 'base' not in config:
        print("missing base font!")
        sys.exit(2)
    if 'output' not in config:
        config['output'] = 'output.ttf'
    
    fonts = {}
    if 'inputs' in config:
        for f in config['inputs']:
            fonts[f] = fontforge.open(config['inputs'][f])
    if config['base'] not in fonts:
        print("missing base font!")
        sys.exit(2)
    
    with open(REPLACELST) as f:
        tsvreader = csv.reader(map(lambda line: line.split("#")[0].strip(), filter(lambda line: line[0]!='#', f)), delimiter="\t")
        for row in tsvreader:
            if len(row) == 2:
                replaceGlyph(fonts[config['base']], row[0], fonts[row[1]])
            elif len(row) == 3:
                replaceGlyph(fonts[config['base']], row[0], fonts[row[1]], row[2])
            else:
                print("error in row: " + "\t".join(row))

    if 'fontname' in config:
        fonts[config['base']].fontname = config['fontname']
    if 'familyname' in config:
        fonts[config['base']].familyname = config['familyname']
    if 'fullname' in config:
        fonts[config['base']].fullname = config['fullname']
    fonts[config['base']].generate(config['output'])

if __name__ == "__main__":
    main()
