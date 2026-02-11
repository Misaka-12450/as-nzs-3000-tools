import streamlit as st
from streamlit.navigation.page import StreamlitPage


HOME_PAGE: StreamlitPage = st.Page(
    "pages/home.py", title="Home", icon=":material/house:"
)
# IEC60898: StreamlitPage = st.Page(
#     "pages/iec60898_1_circuit_breakers.py",
#     title="IEC 60898 Circuit Breaker Calculator",
#     icon=":material/switch:",
# )
MAXIMUM_DEMAND: StreamlitPage = st.Page(
    "pages/maximum_demand.py",
    title="AS/NZS 3000 Maximum Demand",
    icon=":material/bolt:",
)

pages = {
    "": [HOME_PAGE],
    "Electrical": [
        # IEC60898,
        MAXIMUM_DEMAND,
    ],
}
# pages = [HOME_PAGE, IEC60898]

if not st.session_state.get("site_title"):
    site_title: str
    if site_title_prefix := st.secrets.get("site", {}).get("title"):
        site_title = f"{site_title_prefix} Tools"
    else:
        site_title = "Tools"
    st.session_state["site_title"] = site_title
else:
    site_title = st.session_state["site_title"]

pg = st.navigation(pages, position="top")
pg.run()
