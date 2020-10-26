# sf-rfc-validate

This is a simple script to validate [Structured Fields](https://httpwg.org/http-extensions/draft-ietf-httpbis-header-structure.html) in [xml2rfcv3](https://tools.ietf.org/html/rfc7991) documents.

It examines all `sourcecode` and `artwork` elements; when one has a `type` of `http-sf-item`, `http-sf-list` or `http-sf-dict`, it validates the contents.

When validating, it assumes that the content is a HTTP field section; that is, one or more lines, each in the format `field_name: field_value`. Line folding is supported, so that long lines can be formatted appropriately. Multiple lines with the same name will be combined into one value. Then, each value is parsed as the Structured Field type indicated by the `type` attribute.

For example,

~~~ xml
<sourcecode type="http-sf-list">
Foo: bar; baz
Foo: one,
     two
</sourcecode>
~~~

... will be validated as a Structured Field List with the value `bar; baz, one, two`.

Note that in your XML, there **must not be any whitespace** at the start of lines, unless they're continuation of previous lines (folding, as seen above).


## Installation

The script requires Python 3, and can be installed with pip:

> pip3 install sf-rfc-validate


## Use

> sf-rfc-validate.py rfcNNNN.xml

If there are errors, they will be listed, and the program will return 1.