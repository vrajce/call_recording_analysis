import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix Manager
text = re.sub(
    r'(if prompt := st\.chat_input\("e\.g\., Why are customers calling about blue screens\?"\):)\s*# Display user message\s*with st\.chat_message\("user"\):',
    r'\1\n            with mgr_container:\n                with st.chat_message("user"):',
    text
)
# Ensure prompt logic is safely under mgr_container
text = re.sub(
    r'(with st\.spinner\("Searching transcripts via Nebius AI\.\.\."\):)',
    r'',
    text
)

# Fix Copilot
text = re.sub(
    r'if prompt := st\.chat_input\("Type your question for the Auditor Copilot\.\.\."\):\s*with chat_container:\s*with st\.chat_message\("user"\):',
    r'if prompt := st.chat_input("Type your question for the Auditor Copilot..."):\\\n            with chat_container:\\\n                with st.chat_message("user"):',
    text
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

