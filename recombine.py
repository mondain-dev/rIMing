import os
import sys
import json

import fontTools.ttLib
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables import ttProgram

DIR_SCRIPT = os.path.dirname(os.path.realpath(__file__))
CONFIGFILE = os.path.join(DIR_SCRIPT, 'config.json')
REPLACELST = os.path.join(DIR_SCRIPT, 'modifications.json')

def getLangIDPlatEncID(platformID, lang='en'):
    if platformID == 3:
        if lang == 'en':
            return 0x0409, 1
        elif lang == 'zh':
            return 0x1004, 1
    elif platformID == 1:
        if lang == 'en':
            return 0, 0
        elif lang == 'zh':
            return 19, 2

def ch2Unicode(ch):
    if len(ch) == 1:
        return ord(ch)
    elif ch.startswith("0x"):
        return int(glyphDst,base=16)
    elif ch.startswith("0u") or ch.startswith("0U") or ch.startswith("u+") or ch.startswith("U+"):
        return int(ch[2:], base=16)
    return None

def ch2GlyphName(ch, font):
    if len(ch) == 1:
        return font.getBestCmap()[ord(ch)]
    elif ch.startswith("0u") or ch.startswith("0U") or ch.startswith("u+") or ch.startswith("U+"):
        return font.getBestCmap()[int(ch[2:], base=16)]
    return ch

def getIndices(contourId, endPts):
    if contourId == 0:
        return range(endPts[contourId]+1)
    elif contourId > 0:
        return range(endPts[contourId-1]+1, endPts[contourId]+1)


def scaleCoordinates(coordinates, factor):
    def transformCoord(coord, s):
        return (coord[0]*s, (coord[1])*s)
    return [transformCoord(c, factor) for c in coordinates]
  
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
            assert 'filename' in config['inputs'][f]
            fnameFont = config['inputs'][f]['filename']
            if fnameFont.endswith(".ttf"):
                fonts[f] = fontTools.ttLib.ttFont.TTFont(fnameFont)
            if fnameFont.endswith(".ttc"):
                fontCollection = fontTools.ttLib.ttCollection.TTCollection(fnameFont)
                if 'fontname' in config['inputs'][f]:
                    fonts[f] = next(filter(lambda x: x['name'].getBestFullName() == config['inputs'][f]['fontname'], fontCollection.fonts))
                else:
                    fonts[f] = fontCollection.fonts[0]

    if config['base'] not in fonts:
        print("missing base font!")
        sys.exit(2)
    
    fontBase = fonts[config['base']]

    with open(REPLACELST, 'r') as f:
        replaceList = json.load(f)
    for kwargs in replaceList:
        glyphDst = kwargs.get("character")
        glyphNameDst = kwargs.get("glyphName")
        uvsOrig	 = kwargs.get("uvsOrig")
        if uvsOrig is not None and isinstance(uvsOrig, str):
            uvsOrig = int(uvsOrig[2:], base=16)
        
        # for replacing glyphs
        glyphSrc = kwargs.get("glyphSrc")
        fontSrc = kwargs.get("fontSrc")
        if fontSrc is not None:
            fontSrc = fonts[fontSrc]

        # for recompose glyphs
        glyphSrcList = kwargs.get("glyphSrcList")
        contourList  = kwargs.get("contourList")
        fontSrcList = kwargs.get("fontSrcList")
        if fontSrcList is not None:
            fontSrcList = [fonts[ft] for ft in fontSrcList]
        
        if glyphSrc is None and glyphSrcList is None:
            glyphSrc = glyphDst

        # identify the dest code point (unicode) and glyphName if encoded
        unicodeDst = ch2Unicode(glyphDst)
        
        # if dest code point already in the fontBase
        glyphNameDstOrig = None
        if unicodeDst in fontBase.getBestCmap():
            glyphNameDstOrig = fontBase.getBestCmap()[unicodeDst]
        
        # locate the source glyph
        if glyphSrc is not None:
            glyphNameSrc = ch2GlyphName(glyphSrc, fontSrc)        
            if glyphNameDst is None:
                glyphNameDst = glyphNameSrc

            if fontBase != fontSrc:
                # add new glyph
                glyfSrc = fontSrc["glyf"][glyphNameSrc]
                glyf = Glyph()

                s = 1.0
                if fontBase['head'].unitsPerEm != fontSrc['head'].unitsPerEm:
                    s = fontBase['head'].unitsPerEm/fontSrc['head'].unitsPerEm
                    glyf.coordinates = GlyphCoordinates(scaleCoordinates(glyfSrc.coordinates, s))
                else:
                    glyf.coordinates = glyfSrc.coordinates
                glyf.flags = glyfSrc.flags
                glyf.endPtsOfContours = glyfSrc.endPtsOfContours
                glyf.numberOfContours = glyfSrc.numberOfContours
                glyf.program = ttProgram.Program()

                # add to glyph order
                fontBase.setGlyphOrder(fontBase.getGlyphOrder() + [glyphNameDst])
                # add to glyf table 
                fontBase['glyf'][glyphNameDst] = glyf
                # add hmtx
                fontBase['hmtx'][glyphNameDst] = tuple(map(lambda x: int(x*s+0.5), fontSrc['hmtx'][glyphNameSrc]))
        
        elif glyphSrcList is not None:
            glyphNameSrcList = []
            indicesList = []
            glyfSrcList = []
            for i, ch in enumerate(glyphSrcList):
                gName = ch2GlyphName(ch, fontSrcList[i])
                g  = fontSrcList[i]["glyf"][gName]
                indices = [idx for c in contourList[i] for idx in getIndices(c, g.endPtsOfContours) ]
                glyphNameSrcList.append(gName)
                glyfSrcList.append(g)
                indicesList.append(indices)
            glyf = Glyph()
            
            coord_list = []
            flags  = []
            endPointsOfContours = []
            endPt = -1
            for i, g in enumerate(glyfSrcList):
                coord = [g.coordinates[i] for i in indicesList[i]]
                if fontSrcList[i] == fontBase:
                    coord_list += coord
                else:
                    s = fontBase['head'].unitsPerEm/fontSrcList[i]['head'].unitsPerEm
                    coord_list += scaleCoordinates(coord, s)
                flags +=  [g.flags[idx] for idx in indicesList[i]]
                for c in contourList[i]:
                    if c == 0:
                        endPt += g.endPtsOfContours[c] + 1
                    elif c > 0:
                        endPt += (g.endPtsOfContours[c] - g.endPtsOfContours[c-1])
                    endPointsOfContours.append(endPt)
            glyf.coordinates = GlyphCoordinates(coord_list)
            glyf.flags = flags
            glyf.endPtsOfContours = endPointsOfContours
            glyf.numberOfContours = sum(map(len, contourList))
            glyf.program = ttProgram.Program()
            
            # add to glyph order
            fontBase.setGlyphOrder(fontBase.getGlyphOrder() + [glyphNameDst])
            # add to glyf table 
            fontBase['glyf'][glyphNameDst] = glyf
            # add hmtx
            if fontBase['head'].unitsPerEm != fontSrcList[0]['head'].unitsPerEm:
                fontBase['hmtx'][glyphNameDst] = (
                    int(fontSrcList[0]['hmtx'][glyphNameSrcList[0]][0] * fontBase['head'].unitsPerEm/fontSrcList[0]['head']+0.5), 
                    min(map(lambda x: x[0], coord_list)))
            else:
                fontBase['hmtx'][glyphNameDst] = (
                    fontSrcList[0]['hmtx'][glyphNameSrcList[0]][0], 
                    min(map(lambda x: x[0], coord_list)))
        
        # if glyphNameDstOrig: add the glyph to uvs
        if glyphNameDstOrig is not None:
            if uvsOrig is not None:
                for table in fontBase['cmap'].tables:
                    if table.format == 14:
                        if (unicodeDst, None) in table.uvsDict[uvsOrig]:
                            table.uvsDict[uvsOrig] = [(unicodeDst, glyphNameDstOrig) if e[0]==unicodeDst and e[1] is None else e for e in table.uvsDict[uvsOrig]]
                        else:
                            table.uvsDict[uvsOrig].append((unicodeDst, glyphNameDstOrig))
            else:
                for table in fontBase['cmap'].tables:
                    if table.format == 14:
                        for vs in table.uvsDict:
                            if (unicodeDst, None) in table.uvsDict[vs]:
                                table.uvsDict[vs] = [(unicodeDst, glyphNameDstOrig) if e[0]==unicodeDst and e[1] is None else e for e in table.uvsDict[vs]]

        # update cmap
        for table in fontBase['cmap'].tables:
            if table.cmap:
                table.cmap[unicodeDst] = glyphNameDst

    if "name" in config: # rename
        # nameLangList = ['en']
        # if "familyNameZh" in config['name'] or "fullNameZh" in config['name']:
        #     nameLangList.append('zh')
        nameIDListBase = list(set([n.nameID for n in fontBase['name'].names]))
        for nID in nameIDListBase:
            fontBase['name'].removeNames(nameID=nID)
        for platformID in [1,3]: # [mac, windows]
            # for lang in nameLangList:
                platEncID, langID = getLangIDPlatEncID(platformID)
                if "copyright" in config['name']:
                    fontBase['name'].setName(config['name']["copyright"], nameID=0, platformID = platformID, platEncID = platEncID, langID=langID)
                if "familyName" in config['name']:
                    fontBase['name'].setName(config['name']["familyName"], nameID=1, platformID = platformID, platEncID = platEncID, langID=langID)
                if "subfamilyName" in config['name']:
                    fontBase['name'].setName(config['name']["subfamilyName"], nameID=2, platformID = platformID, platEncID = platEncID, langID=langID)
                if "identifier" in config['name']:
                    fontBase['name'].setName(config['name']["identifier"], nameID=3, platformID = platformID, platEncID = platEncID, langID=langID)
                if "fullName" in config['name']:
                    fontBase['name'].setName(config['name']["familyName"], nameID=4, platformID = platformID, platEncID = platEncID, langID=langID)
                if "version" in config['name']:
                    fontBase['name'].setName(config['name']["version"], nameID=5, platformID = platformID, platEncID = platEncID, langID=langID)
                if "psName" in config['name']:
                    fontBase['name'].setName(config['name']["psName"], nameID=6, platformID = platformID, platEncID = platEncID, langID=langID)
                if "license" in config['name']:
                    fontBase['name'].setName(config['name']["license"], nameID=13, platformID = platformID, platEncID = platEncID, langID=langID)
                if "licenseUrl" in config['name']:
                    fontBase['name'].setName(config['name']["licenseUrl"], nameID=14, platformID = platformID, platEncID = platEncID, langID=langID)
                
                # if lang == 'zh' and "familyNameZh" in config['name']:
                #     fontBase['name'].setName(config['name']["familyNameZh"], nameID=1, platformID = platformID, platEncID = platEncID, langID=langID)
                # if lang == 'zh' and "fullNameZh" in config['name']:
                #     fontBase['name'].setName(config['name']["fullNameZh"], nameID=4, platformID = platformID, platEncID = platEncID, langID=langID)
    fontBase.save(config['output'])


if __name__ == "__main__":
    main()
