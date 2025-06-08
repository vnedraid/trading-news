"""RSS worker templates for different feed formats."""

from .base_template import RSSTemplate
from .generic_template import GenericRSSTemplate
from .kommersant_template import KommersantRSSTemplate
from .reuters_template import ReutersRSSTemplate
from .bbc_template import BBCRSSTemplate

__all__ = [
    'RSSTemplate',
    'GenericRSSTemplate', 
    'KommersantRSSTemplate',
    'ReutersRSSTemplate',
    'BBCRSSTemplate'
]