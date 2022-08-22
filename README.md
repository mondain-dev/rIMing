# 里明字體 rIMing
里瓣重組明體 Recombinant IPA Ming

This repo is for scripts and config files to generate rIMing font, which is based on modifications to [IPA mj Mincho 明朝](https://moji.or.jp/mojikiban/font/) ([IPA Font License](directory.fsf.org/wiki/License:IPA_Font_License)). Glyphs from the following fonts are also used:

- [I.Ming(Var) I.明體(異體)](https://github.com/ichitenfont/I.Ming) ([IPA Font License](directory.fsf.org/wiki/License:IPA_Font_License))
- [梦源宋体](https://github.com/Pal3love/dream-han-cjk) ([SIL Open Font License](https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL)): a weight-adjusted variant of [Noto CJK](https://github.com/googlefonts/noto-cjk). We use the W-3 which is close to weights of IPA/I.Ming fonts.
- [BabelStone Han](https://www.babelstone.co.uk/Fonts/Han.html) ([Arphic Public License](http://ftp.gnu.org/non-gnu/chinese-fonts-truetype/LICENSE)).
- [FreeSerif](https://www.gnu.org/software/freefont/) ([GNU FreeFont License ](https://www.gnu.org/software/freefont/license.html))

## Glyph Forms
This font implements the glyph forms known as 舊字形, and follows the exemplars set by the following publications
- 上海大美國聖經公會印官話和合譯本 Chinese Union Version Bible (1919)
- 辭源 (1915—1939)
  - 正編 (1915) 
  - 續編 (1931)
  - 正續編合訂本 (1939)
 
The choices of glyph forms are configured by the `replace.tsv` which is tab-separated values (TSV) file with comments enabled by the hash sign (#). The first column specifies the glyph in the output font, the second the source font the glyph, and the optional third column the glyph or the code point that should be used. 
 
## Usage
The script `recombine.py` runs under the [FontForge scripting](https://fontforge.org/docs/scripting/scripting.html) environment. To run the script, the source fonts, namely the paths to IPA mj Mincho, I.Ming, etc., by default located in the `source/` folder, should be specified in the `config.json`. The following command will create symbolic links of source fonts in the `source/` folder

```
ln -s /path/to/ipamjm.ttf source/ipamjm.ttf
ln -s /path/to/I.Ming-x.xx.ttf source/I.Ming-x.xx.ttf
ln -s /path/to/DreamHanSerif-W3.ttc source/DreamHanSerif-W3.ttc
ln -s /path/to/BabelStoneHan.ttf source/BabelStoneHan.ttf
ln -s /path/to/FreeSerif.ttf source/FreeSerif.ttf
```

Alternatively, one may modify the `config.json` to provide the locations of the source fonts.

To run the script, use the following command line

```
fontforge -script recombine.py
```

which will generate the result font file `rIMing.ttf` as specified by the `config.json`.
