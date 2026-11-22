# SPDX-License-Identifier: Apache-2.0
"""Render GFM and Mkdocstrings references using a single project extension.

Regular pages use Comrak to render GitHub Flavored Markdown. Generated API
reference pages retain Python-Markdown processing so Mkdocstrings directives
are expanded into the documented Python signatures and docstrings.
"""

import comrak
import html5lib
from html5lib.constants import unadjustForeignAttributes
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor


def serialize_html(element):
    """Serialize the generated HTML fragment without discarding SVG attributes."""
    return html5lib.serialize(
        element,
        tree="etree",
        omit_optional_tags=False,
        quote_attr_values="always",
        escape_lt_in_attrs=True,
    )


class ApiAwareGfmSource(Preprocessor):
    """Keep API-reference directives in the Python-Markdown pipeline."""

    def run(self, lines):
        """Preserve API-reference source and capture Markdown for GFM rendering.

        Args:
            lines: Source Markdown lines.

        Returns:
            Original lines for API references or an empty list for GFM pages.
        """
        self.is_reference = any(
            line.lstrip().startswith("::: sbom.") or line.strip() == "::: sbom"
            for line in lines
        )
        self.lines = lines
        return lines if self.is_reference else []


class ApiAwareGfmTree(Treeprocessor):
    """Render GFM pages while delegating API references to Python-Markdown."""

    def __init__(self, md, original_inline):
        """Retain the standard inline processor for API reference pages.

        Args:
            md: Active Python-Markdown instance.
            original_inline: Original inline tree processor to delegate to.
        """
        super().__init__(md)
        self.original_inline = original_inline

    @property
    def stashed_nodes(self):
        """Expose the inline processor's HTML stash for Markdown compatibility."""
        return self.original_inline.stashed_nodes

    def run(self, root):
        """Process API-reference nodes normally or render a GFM document.

        Args:
            root: Parsed Markdown element tree.

        Returns:
            Processed element tree.
        """
        source = self.md.preprocessors["docs_gfm"]
        if source.is_reference:
            return self.original_inline.run(root)

        options = comrak.ExtensionOptions()
        options.table = True
        options.tasklist = True
        options.strikethrough = True
        options.autolink = True
        options.tagfilter = True
        options.alerts = True

        render = comrak.RenderOptions()
        render.alert_style = comrak.AlertStyle.Semantic
        # Preserve safe inline HTML such as <kbd> while applying the GFM tag filter.
        render.unsafe_ = True
        html = comrak.render_markdown(
            "\n".join(source.lines),
            extension_options=options,
            render_options=render,
        )

        # Preserve comments in the HTML stash for Zensical's TOC processor.
        stash = self.md.htmlStash

        class FragmentTree(html5lib.getTreeBuilder("etree")):
            """Parse HTML fragments while retaining comments for later output."""

            def insertComment(self, token, parent=None):
                """Stash an HTML comment for insertion during serialization."""
                self.insertText(stash.store("<!--" + token["data"] + "-->"), parent)

        parser = html5lib.HTMLParser(
            tree=FragmentTree, namespaceHTMLElements=False
        )
        fragment = parser.parseFragment(html)
        # Preserve namespaced SVG attributes during HTML serialization.
        for element in fragment.iter():
            for name in list(element.attrib):
                if name.startswith("{"):
                    namespace, local = name[1:].split("}", 1)
                    qualified = unadjustForeignAttributes[namespace, local]
                    element.set(qualified, element.attrib.pop(name))
        fragment.tag = root.tag
        return fragment


class GfmExtension(Extension):
    """Enable GFM for normal pages and Mkdocstrings for generated references."""

    def extendMarkdown(self, md):
        """Register the API-aware Markdown processors.

        Args:
            md: Active Python-Markdown instance to configure.
        """
        original_inline = md.treeprocessors["inline"]
        md.preprocessors.register(ApiAwareGfmSource(md), "docs_gfm", 1000)
        md.treeprocessors.register(
            ApiAwareGfmTree(md, original_inline), "inline", 20
        )
        md.treeprocessors.deregister("prettify")
        md.output_formats = dict.fromkeys(md.output_formats, serialize_html)


def makeExtension(**kwargs):
    """Return the configurable documentation Markdown extension."""
    return GfmExtension(**kwargs)
