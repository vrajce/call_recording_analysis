import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix Manager Layout
fix_mgr = '''        # Chat input
        if prompt := st.chat_input("e.g., Why are customers calling about blue screens?"):
            with mgr_container:
                with st.chat_message("user"):
                st.markdown(prompt)
            # Append user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get response from AI
            with st.chat_message("assistant"):
                
                    result = ask_hybrid(prompt)'''
                    
repl_mgr = '''        # Chat input
        if prompt := st.chat_input("e.g., Why are customers calling about blue screens?"):
            with mgr_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                # Append user message to history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get response from AI
                with st.chat_message("assistant"):
                    result = ask_hybrid(prompt)'''
                    
text = text.replace(fix_mgr, repl_mgr)

# Fix Copilot Layout
fix_copilot = '''        if prompt := st.chat_input("Type your question for the Auditor Copilot..."):\\
            with chat_container:\\
                with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.copilot_messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):'''

repl_copilot = '''        if prompt := st.chat_input("Type your question for the Auditor Copilot..."):
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.copilot_messages.append({"role": "user", "content": prompt})

                with st.chat_message("assistant"):'''

text = text.replace(fix_copilot, repl_copilot)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
