# sf-rfc-validate

This is a simple script to validate [Structured Fields](https://httpwg.org/http-extensions/draft-ietf-httpbis-header-structure.html) in [xml2rfcv3](https://tools.ietf.org/html/rfc7991) documents.

It examines all `sourcecode` elements; when one has a `type` of `http-sf-item`, `http-sf-list` or `http-sf-dict`, it validates the contents.

Specifically, it examines each line in the content; if it contains a `:`, it is assumed to be a HTTP Structured Field, and everything after the first `:` will be parsed as the structured field type indicated by the `type` parameter.


## Installation

The script requires Python 3, and can be installed with pip:

> pip3 install sf-rfc-validate


## Use

> sf-rfc-validate.py rfcNNNN.xml

If there are errors, they will be listed, and the program will return 1.