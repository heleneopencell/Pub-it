"""
Routes package for the Pub-it API.
"""

from .publications import router as publications_router
from .scripts import router as scripts_router
from .researchers import router as researchers_router

__all__ = ['publications_router', 'scripts_router', 'researchers_router'] 