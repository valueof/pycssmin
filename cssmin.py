# cssminify.py
#
# Author: Anton Kovalyov - http://anton.kovalyov.net/
# Copyright (c) 2011 DISQUS, Inc.
#
# This is a CSS minification tool. It is a Python port of cssmin.js,
# which is a JavaScript port of the Java CSS minifier distributed with
# YUICompressor, which is itself a port of the PHP cssmin utility.
#
# Implementations:
#   JavaScript (by Stoyan Stefanov) and
#   Java (by YUI team):
#     http://developer.yahoo.com/yui/compressor/css.html
#
#   PHP (by Isaac Shlueter):
#     http://code.google.com/p/cssmin/
#

import re

STRING_RE     = re.compile(r"""("([^\\"]|\\.|\\)*")|('([^\\']|\\.|\\)*')""")
ALPHAOP_RE    = re.compile(r"""progid:DXImageTransform\.Microsoft\.Alpha\(Opacity=""", re.IGNORECASE)
EMPTYSTR_RE   = re.compile(r"""\s+""")
FIRSTLTR_RE   = re.compile(r""":first-(line|letter)(\{|,)""")
COMSPACE_RE   = re.compile(r"""\*\/ """)
CHARSET_RE    = re.compile(r"""^(.*)(@charset "[^"]*";)""", re.IGNORECASE)
CHARSET2_RE   = re.compile(r"""(\s*@charset [^;]+;\s*)+""", re.IGNORECASE)
ANDSPACE_RE   = re.compile(r"""\band\(""", re.IGNORECASE)
SEMICOLON_RE  = re.compile(r""";+\}""")
ZEROPX_RE     = re.compile(r"""([\s:])(0)(px|em|%|in|cm|mm|pc|pt|ex)""", re.IGNORECASE)
RGBCOLOR_RE   = re.compile(r"""rgb\s*\(\s*([0-9,\s]+)\s*\)""", re.IGNORECASE)
HEXCOLOR_RE   = re.compile(r"""([^"'=\s])(\s*)#([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])""", re.IGNORECASE)
BORDER_RE     = re.compile(r"""(border|border-top|border-right|border-bottom|border-right|outline|background):none(;|\})""", re.IGNORECASE)
EMPTYRULE_RE  = re.compile(r"""[^\};\{\/]+\{\}""")
BACKGROUND_RE = re.compile(r"""(background-position|transform-origin|webkit-transform-origin|moz-transform-origin|o-transform-origin|ms-transform-origin):0(;|\})""", re.IGNORECASE)

PRE_COMMENT = '___YUICSSMIN_PRESERVE_CANDIDATE_COMMENT_'
PRE_TOKEN   = '___YUICSSMIN_PRESERVED_TOKEN_'
PRE_PSEUDOCOLON = '___YUICSSMIN_PSEUDOCLASSCOLON___'

def cssmin(css, linebreakpos=None):
    start_index = 0
    end_index   = 0
    preserved   = []
    comments    = []
    token       = ''
    total_len   = len(css)
    placeholder = ''

    # Collect all comment blocks
    start_index = css.find('/*', 0)
    while start_index >= 0:
        end_index = css.find('*/', start_index + 2)
        if end_index < 0:
            end_index = total_len

        token = css[start_index + 2:end_index]
        comments.append(token)
        css = css[0:start_index + 2] + PRE_COMMENT + str(len(comments) - 1) + '___' + css[end_index:]

        start_index = css.find('/*', start_index + 2)

    def repl(match):
        match = match.group(0)
        quote = match[0:1]
        match = match[1:-1]

        if match.find(PRE_COMMENT) >= 0:
            for i in range(len(comments)):
                match = match.replace("%s%d___" % (PRE_COMMENT, i), comments[i])

        # Minfiy alpha opacity in filter strings
        match = ALPHAOP_RE.sub("alpha(opacity=", match)
        preserved.append(match)
        return "%s%s%d___%s" % (quote, PRE_TOKEN, len(preserved) - 1, quote)

    # Preserve strings so their content doesn't get accidentally minified
    css = STRING_RE.sub(repl, css)

    # Strings are safe, now wrestle the comments
    for i in range(len(comments)):
        token = comments[i]
        placeholder = "%s%d___" % (PRE_COMMENT, i)

        # ! in the first position of the comment means preserve
        # so push the preserved tokens keeping the !
        if token.startswith('!'):
            preserved.append(token)
            css = css.replace(placeholder, "%s%d___" % (PRE_TOKEN, len(preserved) - 1))
            continue

        # \ in the last position looks like hack for Mac/IE5
        # so shorten that to /*\*/ and the next one to /**/
        if token.endswith("\\"):
            preserved.append("\\")
            css = css.replace(placeholder, "%s%d___" % (PRE_TOKEN, len(preserved) - 1))
            i = i + 1 # Advancing the loop
            preserved.append("")
            css = css.replace("%s%d___" % (PRE_COMMENT, i), "%s%d___" % (PRE_TOKEN, len(preserved) - 1))
            continue

        # Keep empty comments after child selectors (IE7 hack)
        # e.g. html >/**/ body
        if len(token) == 0:
            start_index = css.find(placeholder)
            if start_index > 2:
                if css[start_index - 3] == '>':
                    preserved.append("")
                    css = css.replace(placeholder, "%s%d___" % (PRE_TOKEN, len(preserved) - 1))

        # In all other cases, kill the comment
        css = css.replace("/*%s*/" % placeholder, "")

    # Normalize all whitespace strings to single spaces.
    # Easier to work that way.
    css = EMPTYSTR_RE.sub(" ", css)

    # Remove the spaces before the things that should not have spaces before
    # them. But, be careful not to turn "p :link {...}" into "p:link{...}"
    # Swap out any pseudo-class colons with the token, and then swap back.
    repl = lambda m: m.group(0).replace(":", PRE_PSEUDOCOLON)
    css = re.sub(r"""(^|\})(([^\{:])+:)+([^\{]*\{)""", repl, css)
    css = re.sub(r"""\s+([!{};:>+\(\)\],])""", '\\1', css)
    css = css.replace(PRE_PSEUDOCOLON, ":")

    # Retain space for special IE6 cases
    css = FIRSTLTR_RE.sub(":first-\\1 \\2", css)

    # No space after the end of a preserved comment
    css = COMSPACE_RE.sub("*/", css)

    # If there is a @charset, then only allow one, and push to the top of
    # the file
    css = CHARSET_RE.sub("\\2\\1", css)
    css = CHARSET2_RE.sub("\\1", css)

    # Put the space back in some cases, to support stuff like
    # @media screen and (-webkit-min-device-pixel-ratio:0){
    css = ANDSPACE_RE.sub("and (", css)

    # Remove the spaces after the things that should not have spaces after them
    css = re.sub(r"""([!{}:;>+\(\[,])\s+""", "\\1", css)

    # Remove unnecessary semicolons
    css = SEMICOLON_RE.sub("}", css)

    # Replace 0(px,em,%) with 0.
    css = ZEROPX_RE.sub("\\1\\2", css)

    # Replace 0 0 0 0; with 0.
    css = re.sub(r""":0 0 0 0(;|\})""", ":0\\1", css)
    css = re.sub(r""":0 0 0(;|\})""", ":0\\1", css)
    css = re.sub(r""":0 0(;|\})""", ":0\\1", css)

    # Replace background-position:0; with background-position:0 0;
    # Same for transform-origin
    repl = lambda m: m.group(1).lower() + ":0 0" + m.group(2)
    css = BACKGROUND_RE.sub(repl, css)

    # Replace 0.6 to .6 but only if preceded by : or a white-space
    css = re.sub(r"""(:|\s)0+\.(\d+)""", "\\1.\\2", css)

    # Shorten colors from rgb(51,102,153) to #336699
    # This makes it more likely that it'll get further compressed in the next step
    def rgbrepl(match):
        rgbcolors = match.group(1).split(',')
        for i in range(len(rgbcolors)):
            rgbcolors[i] = hex(int(rgbcolors[i]))[2:]
            if len(rgbcolors[i]) == 1:
                rgbcolors[i] = '0' + rgbcolors[i]
        return '#%s' % ''.join(rgbcolors)

    css = RGBCOLOR_RE.sub(rgbrepl, css)

    # Shorten colors from #AABBCC to #ABC. Note that we want to make sure the color
    # is not preceded by either ", " or =. Indeed, the property
    #     filter: chroma(color="#FFFFFF");
    # would become
    #     filter: chroma(color="#FFF");
    # which makes the filter break in IE.
    def hexrepl(match):
        if all([
                match.group(3).lower() == match.group(4).lower(),
                match.group(5).lower() == match.group(6).lower(),
                match.group(7).lower() == match.group(8).lower()
            ]):
            return (match.group(1) + match.group(2) + '#' +
                match.group(3) + match.group(5) + match.group(7)).lower()
        return match.group(0)

    css = HEXCOLOR_RE.sub(hexrepl, css)

    # border: none -> border:0
    repl = lambda m: m.group(1).lower() + ':0' + m.group(2)
    css = BORDER_RE.sub(repl, css)

    # Shorter opacity IE filter
    css = ALPHAOP_RE.sub("alpha(opacity=", css)

    # Remove empty rules
    css = EMPTYRULE_RE.sub("", css)

    if linebreakpos and linebreakpos >= 0:
        # Some source control tools don't like it when files containing lines longer
        # than, say 8000 characters, are checked in. The linebreak option is used in
        # that case to split long lines after a specific column.
        start_index = 0
        i = 0
        while i < len(css):
            i += 1
            if css[i - 1] == '}' and i - start_index > linebreakpos:
                css = css[0, i] + '\n' + css[i]
                start_index = i

    # Replace multiple semi-colons in a row by a single one
    # See SF bug #1980989
    css = re.sub(r";;+", ";", css)

    # Restore preserved comments and strings
    for i in range(len(preserved)):
        css = css.replace("%s%d___" % (PRE_TOKEN, i), preserved[i])

    # Trim the final string
    return css.strip()
