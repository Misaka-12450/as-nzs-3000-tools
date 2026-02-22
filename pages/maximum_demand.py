import streamlit as st
import inspect
import as_nzs_3000_tools.c1_maximum_demand as c1

# Dynamically get all C1LoadGroup subclasses
_LOAD_GROUPS: list[type[c1.LoadGroup]] = [
    getattr(c1, name)
    for name in c1.__all__
    if inspect.isclass(getattr(c1, name))
    and issubclass(getattr(c1, name), c1.LoadGroup)
    and getattr(c1, name) is not c1.LoadGroup
]

_LOAD_GROUPS_DICT: dict[str, type[c1.LoadGroup]] = {}
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

# Load group selection and input
with st.container(border=True):
    # Select load group
    selected_label = st.selectbox(
        "Load group",
        options=list(_LOAD_GROUPS_DICT.keys()),
        label_visibility="collapsed",
    )

    # Display load group description
    load_group_cls = _LOAD_GROUPS_DICT[selected_label]
    st.markdown(load_group_cls.description.replace("\n", " "))

    # Display exceptions and notes
    s: str = str(load_group_cls)
    if s:
        with st.expander("**Exceptions and Notes**"):
            st.markdown(s)

    if not st.session_state.get("num_loads"):
        st.session_state.num_loads = 1
    num_loads = st.session_state.num_loads

    # Add number of load and rating
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

    # Add more loads button
    if st.button("More", key=f"more_loads_{i}", icon=":material/add:"):
        st.session_state["num_loads"] += 1
        st.rerun()

# Submit load group
is_applicable = load_group_cls.is_num_living_units_applicable(num_living_units)
submitted = st.button(
    "Add load group",
    help=(
        ""
        if is_applicable
        else f"This load group is not applicable for {num_living_units} living "
        f"unit{'' if num_living_units==1 else 's'}."
    ),
    type="primary",
    icon=":material/add:",
    disabled=not is_applicable,
    width="stretch",
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
                "total_rating": instance.total_rating_a,
                "max_demand_a": instance.maximum_demand_a,
                "max_demand_w": instance.maximum_demand_w,
            }
        )
    except c1.IncorrectLoadGroupException as e:
        st.error(str(e))
    except c1.LoadGroupNotApplicableException as e:
        st.error(str(e))
    except (ValueError, NotImplementedError) as e:
        st.error(str(e))

st.subheader("Load Groups")

# Display added load groups
if st.session_state.load_entries:
    # Display each load group entry
    for i, entry in enumerate(st.session_state.load_entries):
        col_info, col_demand, col_remove = st.columns([5, 2, 1])
        with col_info:
            unit = "A" if entry["rating_type"] == "A" else "W"
            st.markdown(
                f"**{entry['label']}**  \n"
                f"{entry['num_load']} × {entry['rating']} {unit} = "
                f"**{entry['total_rating']:.2f}".rstrip("0").rstrip(".") + " A**"
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

    # Display total maximum demand
    st.divider()
    total_a = sum(e["max_demand_a"] for e in st.session_state.load_entries)
    total_w = sum(e["max_demand_w"] for e in st.session_state.load_entries)
    st.metric("Total Maximum Demand", f"{total_a:.2f} A ({total_w:.0f} W)")

    # Clear all button
    if st.button("Clear all"):
        st.session_state.load_entries.clear()
        st.rerun()
else:
    st.info("No load groups added yet.")
