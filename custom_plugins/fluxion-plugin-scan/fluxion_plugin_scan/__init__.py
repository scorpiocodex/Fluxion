import sys

if sys.version_info < (3, 10):
    raise RuntimeError("fluxion-plugin-scan requires Python 3.10+")

from .plugin import PortScanPlugin, create_plugin

__version__ = "1.0.0"
__all__ = ["PortScanPlugin", "create_plugin"]
