import logging
from .security import input_guard_check

logger = logging.getLogger("CoastalAlpineCore.PromptGuard")

if __name__ == "__main__":
    test_prompt = "SELECT * FROM users;"
    safe = input_guard_check(test_prompt)
    if safe:
        logger.info("Prompt is safe.")
    else:
        logger.warning("Prompt is blocked.")
