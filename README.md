# PyCssMin

This is a CSS minification tool. It is a Python port of cssmin.js,
which is a JavaScript port of the Java CSS minifier distributed with
YUICompressor, which is itself a port of the PHP cssmin utility.

### Usage

```
from cssmin import cssmin

cssmin("""
body {
  color: #FFFFFF;
}
""")
> 'body{color:#fff}'
