# rfc-http-validate

This is a simple script to validate HTTP messages (possibly containing [Structured Fields](https://httpwg.org/http-extensions/draft-ietf-httpbis-header-structure.html)) in [xml2rfcv3](https://tools.ietf.org/html/rfc7991) documents and [kramdown-rfc](https://github.com/cabo/kramdown-rfc) documents.

It checks that the content of an HTTP message:

* Optionally, starts with a valid HTTP/1.1 request or status line
* Has one or more HTTP/1.1 header field lines, possibly with line folding (so that long lines can be formatted within the constraints of the RFC format)
* Optionally, has a response body, separated from the header fields with a single empty line

The start line will be checked that the method or status code is reasonable, and that the version identifier `HTTP/1.1` is correct. The URL in requests will not be validated, however.

Header fields will be validated for general syntax. Additionally, header field names that are configured with structured type information (see below) will be validated according to that type.

The body, if present, is currently ignored (i.e., the `Content-Length` is not checked).

If an [RFC8792](https://www.rfc-editor.org/rfc/rfc8792.html) `\\` wrapping header is present, lines will be unwrapped first (i.e., before unfolding, as per above). This is useful for long lines with binary content (which cannot contain whitespace); e.g.,

~~~ xml
<sourcecode type="http-message">
# NOTE: '\' line wrapping per RFC 8792

Signature: sig1=:K2qGT5srn2OGbOIDzQ6kYT+ruaycnDAAUpKv+ePFfD0RAxn/1BUe\
    Zx/Kdrq32DrfakQ6bPsvB9aqZqognNT6be4olHROIkeV879RrsrObury8L9SCEibe\
    oHyqU/yCjphSmEdd7WD+zrchK57quskKwRefy2iEC5S2uAH0EPyOZKWlvbKmKu5q4\
    CaB8X/I5/+HLZLGvDiezqi6/7p2Gngf5hwZ0lSdy39vyNMaaAT0tKo6nuVw0S1MVg\
    1Q7MpWYZs0soHjttq0uLIA3DIbQfLiIvK6/l0BdWTU7+2uQj7lBkQAsFZHoA96ZZg\
    FquQrXRlmYOh+Hx5D9fJkXcXe5tmAg==:
</sourcecode>
~~~


## Validating HTTP Messages in Markdown

In Markdown, all you need to do is adorn your messages with `http-messsage`; for example:

~~~~
~~~ http-message
HTTP/1.1 200 OK
Foo: bar, baz
~~~
~~~~

Then, run:

> rfc-http-validate my-draft.md


## Validating HTTP Messages in RFC XML

In XML, this script examines all `sourcecode` and `artwork` elements; when one has a `type` of
`http-message`.

For example,

~~~ xml
<sourcecode type="http-message">
Foo: bar; baz
Foo: one,
     two
</sourcecode>
~~~

Then, run:

> rfc-http-validate my-draft.xml

Note that in your XML, there **must not be any whitespace** at the start of lines, unless they're continuation of previous lines (folding, as seen above).



## Configuring Structured Type Information for Fields

By default, the types of existing Structured Fields (including those that are compatible with Structured Fields; see [Retrofit Structured Fields for HTTP](https://datatracker.ietf.org/doc/draft-ietf-httpbis-retrofit/)) are known. Type information for other fields can be added on the command line or through a file.

To pass a type on the command line, use the `--list`, `--dictionary` or `--item` arguments as appropriate, followed by the field name. For example:

> rfc-http-validate --list Foo --list Bar --item Baz my_draft.xml

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

> rfc-http-validate --map sf.json my_draft.xml


## Installation

The script requires Python 3, and can be installed with pip:

> pip3 install rfc-http-validate

