import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def get_site_title() -> str:
    """
    Get the site title from session state or secrets, with a default fallback.

    :return: The site title to be displayed in the app.
    """
    if not st.session_state.get("site_title"):
        site_title: str
        try:
            site_title = st.secrets.get("site", {}).get("title")
        except StreamlitSecretNotFoundError:
            # Can be raised even with .get() if .streamlit/secrets.toml does not exist
            site_title = "Australian Home Building Calculators"
        st.session_state["site_title"] = site_title
    else:
        site_title = st.session_state["site_title"]
    return site_title


site_title: str = get_site_title()


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


if __name__ == "__main__":
    st.navigation(pages).run()
