import streamlit as st


pg = st.navigation([
            # add a rescue related icon like cross
            st.Page("victim_client_updated.py", title="RescueLLM", icon="🚑"),
            st.Page("rescue_client.py", title="Interactive Map", icon="🗺️")
        ])

pg.run()