import re

import tinycss2


#: Regexp matching a uri scheme (e.g. "https:") per RFC 3986
URI_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def is_local_url(url):
    """Returns True if the url is a fragment ("#...") or a relative uri"""
    url = url.strip()
    if not url:
        return True

    if url.startswith("#"):
        return True

    # Protocol-relative uris point at a remote host
    if url.startswith("//"):
        return False

    # Anything with a scheme is not local
    return not URI_SCHEME_RE.match(url)


def tokens_have_only_local_urls(tokens):
    """Returns True if all url() tokens are local urls"""
    for token in tokens:
        if token.type == "url":
            if not is_local_url(token.value):
                return False

        elif token.type == "function":
            if token.lower_name == "url":
                # url("...") with a quoted value parses as a function
                for arg in token.arguments:
                    if arg.type == "string" and not is_local_url(arg.value):
                        return False

            if not tokens_have_only_local_urls(token.arguments):
                return False

        elif token.type in ("() block", "[] block", "{} block"):
            if not tokens_have_only_local_urls(token.content):
                return False

        elif token.type == "error" and token.kind == "bad-url":
            return False

    return True


ALLOWED_CSS_PROPERTIES = frozenset(
    (
        "azimuth",
        "background-color",
        "border-bottom-color",
        "border-collapse",
        "border-color",
        "border-left-color",
        "border-right-color",
        "border-top-color",
        "clear",
        "color",
        "cursor",
        "direction",
        "display",
        "elevation",
        "float",
        "font",
        "font-family",
        "font-size",
        "font-style",
        "font-variant",
        "font-weight",
        "height",
        "letter-spacing",
        "line-height",
        "overflow",
        "pause",
        "pause-after",
        "pause-before",
        "pitch",
        "pitch-range",
        "richness",
        "speak",
        "speak-header",
        "speak-numeral",
        "speak-punctuation",
        "speech-rate",
        "stress",
        "text-align",
        "text-decoration",
        "text-indent",
        "unicode-bidi",
        "vertical-align",
        "voice-family",
        "volume",
        "white-space",
        "width",
    )
)


ALLOWED_SVG_PROPERTIES = frozenset(
    (
        "fill",
        "fill-opacity",
        "fill-rule",
        "stroke",
        "stroke-width",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-opacity",
    )
)


class CSSSanitizer:
    def __init__(
        self,
        allowed_css_properties=ALLOWED_CSS_PROPERTIES,
        allowed_svg_properties=ALLOWED_SVG_PROPERTIES,
    ):
        self.allowed_css_properties = allowed_css_properties
        self.allowed_svg_properties = allowed_svg_properties

    def sanitize_css(self, style):
        """Sanitizes css in style tags"""
        parsed = tinycss2.parse_declaration_list(style)

        if not parsed:
            return ""

        new_tokens = []
        for token in parsed:
            if token.type == "declaration":
                if (
                    token.lower_name in self.allowed_css_properties
                    or token.lower_name in self.allowed_svg_properties
                ) and tokens_have_only_local_urls(token.value):
                    new_tokens.append(token)
            elif token.type in ("comment", "whitespace"):
                if new_tokens and new_tokens[-1].type != token.type:
                    new_tokens.append(token)

            # NOTE(willkg): We currently don't handle AtRule or ParseError and
            # so both get silently thrown out

        if not new_tokens:
            return ""

        return tinycss2.serialize(new_tokens).strip()
