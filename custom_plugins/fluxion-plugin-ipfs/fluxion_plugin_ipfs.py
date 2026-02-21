"""IPFS Protocol Plugin for Fluxion."""

from typing import Any, AsyncIterator
from pathlib import Path
import httpx

from fluxion.plugins.base import ProtocolPlugin
from fluxion.models import PluginMeta
from fluxion.exceptions import NetworkError


class IPFSProtocolPlugin(ProtocolPlugin):
    """Handles ipfs:// protocol URLs via public gateways."""
    
    GATEWAY = "https://ipfs.io/ipfs/"

    def metadata(self) -> PluginMeta:
        return PluginMeta(
            name="ipfs",
            version="0.1.0",
            description="Native Web3 IPFS gateway integration",
            protocols=["ipfs"],
        )
        
    def _to_gateway(self, url: str) -> str:
        """Convert ipfs://cid to a gateway HTTP URL."""
        if not url.startswith("ipfs://"):
            return url
        cid_path = url[len("ipfs://"):]
        return f"{self.GATEWAY}{cid_path}"

    async def download(self, url: str, output: Path, **kwargs: Any) -> int:
        """Fetch an IPFS resource and save it."""
        gateway_url = self._to_gateway(url)
        timeout = kwargs.get("timeout", 30.0)
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                response = await client.get(gateway_url)
                response.raise_for_status()
                with output.open("wb") as f:
                    f.write(response.content)
                return len(response.content)
            except httpx.HTTPError as exc:
                raise NetworkError(
                    f"IPFS Gateway fetch failed: {exc}",
                    suggestion="Verify the CID is pinned and the gateway is reachable.",
                ) from exc

    async def stream(self, url: str, **kwargs: Any) -> AsyncIterator[bytes]:
        """Stream an IPFS resource in chunks."""
        gateway_url = self._to_gateway(url)
        timeout = kwargs.get("timeout", 30.0)
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                async with client.stream("GET", gateway_url) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except httpx.HTTPError as exc:
                raise NetworkError(f"IPFS Stream Error: {exc}")


def create_plugin() -> IPFSProtocolPlugin:
    """Factory called by Fluxion to initialize the plugin."""
    return IPFSProtocolPlugin()
