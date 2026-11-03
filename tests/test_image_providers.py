import pytest
from desktop_api.image_providers import (
    BaseImageProvider,
    ImageProviderResult,
    ImageProviderChain,
)


class MockFailingProvider(BaseImageProvider):
    name = "Mock Failing Provider"

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        return ImageProviderResult(False, provider=self.name, error="Fallo intencional simulado")


class MockSuccessfulProvider(BaseImageProvider):
    name = "Mock Successful Provider"

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        return ImageProviderResult(True, image_base64="data:image/png;base64,mocked_image_bytes", provider=self.name)


def test_image_provider_chain_fallback():
    chain = ImageProviderChain()

    # Inyectar proveedores mockeados: primero falla, segundo tiene éxito
    chain.pollinations = MockFailingProvider()
    chain.sd_local = MockFailingProvider()
    chain.ai_horde = MockSuccessfulProvider()

    res = chain.generate(prompt="A dwarf paladin in full plate")
    assert res["success"] is True
    assert res["provider"] == "Mock Successful Provider"
    assert "mocked_image_bytes" in res["image_base64"]


def test_image_provider_chain_all_fail():
    chain = ImageProviderChain()

    # Todos los proveedores fallan
    chain.pollinations = MockFailingProvider()
    chain.sd_local = MockFailingProvider()
    chain.ai_horde = MockFailingProvider()

    res = chain.generate(prompt="A rogue in the shadows")
    assert res["success"] is False
    assert "Todos los proveedores de retratos fallaron" in res["error"]
