import asyncio
from ai_engine.translation.fallback import DevelopmentFallback
def test_fallback_is_explicit_identity():
    out=asyncio.run(DevelopmentFallback().translate("hello","en","kn","general",[]))
    assert out=="hello"
