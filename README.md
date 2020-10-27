# sf-rfc-validate

This is a simple script to validate [Structured Fields](https://httpwg.org/http-extensions/draft-ietf-httpbis-header-structure.html) in [xml2rfcv3](https://tools.ietf.org/html/rfc7991) documents.

## Structured Fields in RFC XML

This script examines all `sourcecode` and `artwork` elements; when one has a `type` of
`http-structured-fields`, it assumes that the content is a HTTP field section; that is, one or more
lines, each in the format `field_name: field_value`. Line folding is supported, so that long lines
can be formatted appropriately. Multiple lines with the same name will be combined into one value.

Then, each value is parsed as a Structured Field type, if the header name is recognised as being a structured field.

For example,

~~~ xml
<sourcecode type="http-structured-fields">
Foo: bar; baz
Foo: one,
     two
</sourcecode>
~~~

... will be validated as having a single field, `foo`, with the value `bar; baz, one, two`.

Note that in your XML, there **must not be any whitespace** at the start of lines, unless they're continuation of previous lines (folding, as seen above).


## Configuring Structured Type Information

You can pass type information (i.e., List, Dictionary, or Item) for field names on the command line, or in a configuration file.

To pass a type on the command line, use the `--list`, `--dictionary` or `--item` arguments as appropriate, followed by the field name. For example:

> sf-rfc-validate.py --list Foo --list Bar --item Baz my_draft_.xml

Here, `Foo` and `Bar` will be validated as Structured Lists, while `Baz` will be validated as a Structured Item.

Alternatively, you can collect this information in a JSON file, with the top-level object keys being field names, and their values being `list`, `dict` or `item` as appropriate. Thus, the configuration in the example above could be expressed in a JSON file `sf.json` as:

~~~ json
{
  "Foo": "list",
  "Bar": "list",
  "Baz": "item"
}
~~~

... and passed to the script like this:

> sf-rfc-validate.py --map sf.json my_draft.xml


## Installation

The script requires Python 3, and can be installed with pip:

> pip3 install sf-rfc-validate

