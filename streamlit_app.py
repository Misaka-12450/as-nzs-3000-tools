import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def load_site_title() -> None:
    """
    Load the site title from session state or secrets, with a default fallback.
    """
    if not st.session_state.get("site_title"):
        title: str
        try:
            st.session_state["site_title"] = st.secrets.get("site", {}).get("title")
        except StreamlitSecretNotFoundError:
            # Can be raised even with .get() if .streamlit/secrets.toml does not exist
            st.session_state["site_title"] = "Australian Home Building Calculators"


load_site_title()


pages = {
    "": [
        st.Page("pages/home.py", title="Home", icon=":material/house:"),  # Home Page
    ],
    # "IEC60898-1 Circuit-breakers": [
    #     st.Page(
    #         "pages/iec60898.py",
    #         title="IEC 60898 Circuit Breaker",
    #         icon=":material/switch:",
    #     ),
    # ],
    "AS/NZS 3000 Wiring Rules": [
        st.Page(
            "pages/maximum_demand.py",
            title="C1 Domestic Maximum Demand",
            icon=":material/bolt:",
        ),
    ],
}


if __name__ == "__main__":
    st.navigation(pages).run()
