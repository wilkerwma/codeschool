from .media import Media
from .core import *
from .ace import *
from wagtail.wagtailcore.blocks import *
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailsnippets.blocks import SnippetChooserBlock
from wagtail.wagtaildocs.blocks import DocumentChooserBlock
from wagtail.wagtailembeds.blocks import EmbedBlock
from wagtail.contrib.table_block.blocks import TableBlock
from wagtailmarkdown.blocks import MarkdownBlock
#TODO: update commonblocks source to wagtail 1.4
# from commonblocks.blocks import (
#     CommonPageChooserBlock,
#     SimpleRichTextBlock,
#     CommonImageBlock,
#     CommonQuoteBlock,
#     CommonHeadingBlock,
#     CommonVideoBlock,
#     CommonInternalLink,
#     CommonExternalLink,
#     CommonLinksBlock,
#)


def register_block(block_cls):
    """
    Register block classes to be available at codeschool.blocks module.
    """

    name = block_cls.__name__
    if name in globals():
        raise RuntimeError('a block named %s aready exists' % name)
    globals()[name] = block_cls
    return block_cls
