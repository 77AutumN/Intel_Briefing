"""
Import Smoke Test — 验证所有模块可独立导入，不触发 ModuleNotFoundError。
这是 Phase 1 的核心验证：pyproject.toml 包化后 sys.path hack 不再需要。
"""
import pytest
import importlib

MODULES = [
    "src.config",
    "src.intel_collector",
    "src.report_generator",
    "src.sensors.arxiv_ai",
    "src.sensors.hf_daily_papers",
    "src.sensors.product_hunt",
    "src.sensors.x_grok_sensor",
    "src.sensors.hn_blogs",
    "src.sensors.techcrunch_rss",
    "src.sensors.mit_tech_review",
    "src.external.fetch_news",
    "src.utils.verifier",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    """Every module in the engine must be importable via its src.xxx path."""
    importlib.import_module(module)
