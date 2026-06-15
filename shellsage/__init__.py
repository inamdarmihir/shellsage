"""ShellSage — shell command translation layer backed by local Qdrant."""

__version__ = "0.2.0"
__all__ = ["translate", "store_outcome", "ShellContext"]

from shellsage.models import ShellContext
from shellsage.translator import store_outcome, translate
