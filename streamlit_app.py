import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

pages = {
    "": [
        st.Page("pages/home.py", title="Home", icon=":material/house:"),  # Home Page
    ],
    "Electrical": [
        # st.Page(
        #     "pages/iec60898.py",
        #     title="IEC 60898 Circuit Breaker",
        #     icon=":material/switch:",
        # ), # IEC 60898
        st.Page(
            "pages/maximum_demand.py",
            title="AS/NZS 3000 Maximum Demand",
            icon=":material/bolt:",
        ),  # C1 Maximum Demand
    ],
}

if not st.session_state.get("site_title"):
    site_title: str
    try:
        site_title_prefix = st.secrets.get("site", {}).get("title")
    except StreamlitSecretNotFoundError:
        # Can be raised even with .get() if .streamlit/secrets.toml does not exist
        site_title_prefix = None
    if site_title_prefix:
        site_title = f"{site_title_prefix} Tools"
    else:
        site_title = "Tools"
    st.session_state["site_title"] = site_title
else:
    site_title = st.session_state["site_title"]

pg = st.navigation(
    pages,
    # position="top",
)
pg.run()
