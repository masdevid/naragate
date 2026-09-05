from app.core.llm_config import llm_endpoint, llm_model
from app.core.sectors_config import sectors_api_key


def missing_setup_items() -> list[str]:
    """Return the configuration items required for analysis that are missing.

    Possible values: "sectors_api_key", "llm_model".
    """
    missing: list[str] = []
    if not sectors_api_key():
        missing.append("sectors_api_key")
    if not llm_model():
        missing.append("llm_model")
    return missing