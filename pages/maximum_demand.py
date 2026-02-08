import streamlit as st
from as_nzs_3000.c1_maximum_demand import (
    C1Manual,
    C1A1,
    C1A2,
    C1B1,
    C1B2,
    C1B3,
    C1C,
    C1D,
    C1E,
    C1F,
    C1H,
    C1I,
    C1J1,
    C1J2,
    C1J4,
    C1LoadGroup,
    IncorrectLoadGroupException,
    LoadGroupNotApplicableException,
)

_LOAD_GROUPS: list[type[C1LoadGroup]] = [
    C1Manual,
    C1A1,
    C1A2,
    C1B1,
    C1B2,
    C1B3,
    C1C,
    C1D,
    C1E,
    C1F,
    C1H,
    C1I,
    C1J1,
    C1J2,
    C1J4,
]

_LOAD_GROUPS_DICT: dict[str, type[C1LoadGroup]] = {}
for lg in _LOAD_GROUPS:
    # TODO: Hide load groups that are not applicable
    _LOAD_GROUPS_DICT[f"{repr(lg)} {lg.title}"] = lg

st.header("AS/NZS 3000 Maximum Demand")
st.caption("Table C1 — Domestic maximum demand calculation")

num_living_units = st.number_input(
    "Number of living units per phase",
    min_value=1,
    value=1,
    help="Use 1 for a single domestic installation.",
)

if "load_entries" not in st.session_state:
    st.session_state.load_entries = []

st.subheader("Add Load Group")

with st.container(border=True):
    selected_label = st.selectbox(
        "Load group",
        options=list(_LOAD_GROUPS_DICT.keys()),
        label_visibility="collapsed",
    )

    load_group_cls = _LOAD_GROUPS_DICT[selected_label]
    st.markdown(load_group_cls.description.replace("\n", " "))

    s: str = str(load_group_cls)
    if s:
        with st.expander("**Exceptions and Notes**"):
            st.markdown(s)

    if not st.session_state.get("num_loads"):
        st.session_state.num_loads = 1
    num_loads = st.session_state.num_loads

    # TODO: Add loads of different rating in one load group
    for i in range(num_loads):
        col1, col2, col3, col4 = st.columns([3, 3, 3, 1], vertical_alignment="bottom")
        with col1:
            num_load = st.number_input(
                "Number of loads", min_value=1, value=1, step=1, key=f"num_load_{i}"
            )
        with col2:
            rating = st.number_input(
                "Rating per load", min_value=1, value=10, step=1, key=f"rating_{i}"
            )
        with col3:
            rating_type = st.selectbox(
                "Unit",
                options=["A", "W"],
                format_func=lambda x: "Amperes" if x == "A" else "Watts",
                key=f"load_row_{i}",
                label_visibility="collapsed",
            )
        with col4:
            st.button(
                "",
                key=f"delete_{i}",
                icon=":material/delete:",
                width="stretch",
                disabled=not (num_loads - 1),
            )

    if st.button("More", key=f"more_loads_{i}", icon=":material/add:"):
        st.session_state["num_loads"] += 1
        st.rerun()

submitted = st.button(
    "Add load group", icon=":material/add:", type="primary", width="stretch"
)

if submitted:
    load_group_cls = _LOAD_GROUPS_DICT[selected_label]
    try:
        # TODO: Combine with existing entry if same load group
        instance = load_group_cls(
            rating=rating,
            num_load=num_load,
            rating_type=rating_type,
            num_living_units=num_living_units,
        )
        st.session_state.load_entries.append(
            {
                "label": selected_label,
                "rating": rating,
                "num_load": num_load,
                "rating_type": rating_type,
                "max_demand_a": instance.maximum_demand_a,
                "max_demand_w": instance.maximum_demand_w,
            }
        )
    except IncorrectLoadGroupException as e:
        st.error(str(e))
    except LoadGroupNotApplicableException as e:
        st.error(str(e))
    except (ValueError, NotImplementedError) as e:
        st.error(str(e))

st.subheader("Load Groups")

if st.session_state.load_entries:
    for i, entry in enumerate(st.session_state.load_entries):
        col_info, col_demand, col_remove = st.columns([4, 3, 1])
        with col_info:
            unit = "A" if entry["rating_type"] == "A" else "W"
            st.markdown(
                f"{entry['label']}  \n"
                f"**{entry['num_load']} × {entry['rating']} {unit}**"
            )
        with col_demand:
            st.metric(
                "Max demand",
                f"{entry['max_demand_a']:.2f} A",
                label_visibility="collapsed",
            )
        with col_remove:
            if st.button("✕", key=f"remove_{i}"):
                st.session_state.load_entries.pop(i)
                st.rerun()

    st.divider()
    total_a = sum(e["max_demand_a"] for e in st.session_state.load_entries)
    total_w = sum(e["max_demand_w"] for e in st.session_state.load_entries)
    st.metric("Total Maximum Demand", f"{total_a:.2f} A ({total_w:.0f} W)")

    if st.button("Clear all"):
        st.session_state.load_entries.clear()
        st.rerun()
else:
    st.info("No load groups added yet.")
