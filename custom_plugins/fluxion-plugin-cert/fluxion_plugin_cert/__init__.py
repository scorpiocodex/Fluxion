import sys

if sys.version_info < (3, 10):
    raise RuntimeError("fluxion-plugin-cert requires Python 3.10+")

from .plugin import CertInspectorPlugin, create_plugin

__version__ = "1.0.0"
__all__ = ["CertInspectorPlugin", "create_plugin"]
