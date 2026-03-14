import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import chat_backend
from chat_backend import get_qsdd_rules_prompt


def main():
    print("--- Resolved system_prompt ---")
    print(chat_backend.system_prompt)
    print("\n--- Resolved hybrid_system ---")
    print(chat_backend.hybrid_system.format(qsdd_context=get_qsdd_rules_prompt()))


if __name__ == "__main__":
    main()
