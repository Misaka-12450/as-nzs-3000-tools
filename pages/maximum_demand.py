import streamlit as st
import inspect
import as_nzs_3000_tools.as_nzs_3000_c_load_groups as c1
from pages.common import HELP_RATING_IRRELEVANT

st.header("Domestic Maximum Demand")
st.caption("AS/NZS 3000 Table C1")

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


# Input fields


# Number of living units

single_living_unit = st.segmented_control(
    "Number of living units per phase",
    options=[":material/house: 1", ":material/apartment: 2 or more"],
    default=":material/house: 1",
    width="stretch",
)
if single_living_unit == ":material/house: 1":
    num_living_units = 1
    st.session_state["as_nzs_3000_c1_num_living_units"] = 1
else:
    num_living_units = st.number_input(
        "Number of living units per phase",
        min_value=2,
        value=2,
        key="as_nzs_3000_c1_num_living_units",
        label_visibility="collapsed",
    )


# Load group selection and input
st.subheader("Add Load Group")

if "as_nzs_3000_c1_load_entries" not in st.session_state:
    st.session_state["as_nzs_3000_c1_load_entries"] = []

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
    is_point_based: bool = issubclass(load_group_cls, c1.LoadGroupPointBased)

    # Display exceptions and notes
    s: str = str(load_group_cls)
    if s:
        with st.expander("**Exceptions and Notes**"):
            st.markdown(s)

    if not st.session_state.get("as_nzs_3000_c1_num_loads"):
        st.session_state["as_nzs_3000_c1_num_loads"] = 1
    num_loads = st.session_state["as_nzs_3000_c1_num_loads"]

    # Add number of load and rating
    # TODO: Add loads of different rating in one load group
    for i in range(num_loads):
        col1, col2, col3, col4 = st.columns([3, 3, 3, 1], vertical_alignment="bottom")

        # Number of loads
        with col1:
            num_loads = st.number_input(
                "Number of loads",
                min_value=1,
                value=1,
                step=1,
                key=f"as_nzs_3000_c1_num_load_{i}",
            )

        # Rating per load
        with col2:
            if is_point_based:
                rating = st.number_input(
                    "Rating per load",
                    min_value=1,
                    value=load_group_cls.max_rating,
                    step=1,
                    key=f"as_nzs_3000_c1_rating_{selected_label}_{i}",
                    help=HELP_RATING_IRRELEVANT,
                    disabled=True,
                )
            else:
                rating = st.number_input(
                    "Rating per load",
                    min_value=1,
                    value=10,
                    step=1,
                    key=f"as_nzs_3000_c1_rating_{selected_label}_{i}",
                )

        # Unit
        with col3:
            rating_unit = st.selectbox(
                "Unit",
                options=["A", "W"],
                format_func=lambda x: "Amperes" if x == "A" else "Watts",
                key=f"as_nzs_3000_c1_load_row_{selected_label}_{i}",
                help=HELP_RATING_IRRELEVANT if is_point_based else "",
                disabled=is_point_based,
                label_visibility="collapsed",
            )

        # Delete
        with col4:
            st.button(
                "",
                key=f"as_nzs_3000_c1_delete_{selected_label}_{i}",
                icon=":material/delete:",
                width="stretch",
                disabled=not (num_loads - 1),
            )

    # Add more loads button
    if st.button("More", key=f"as_nzs_3000_c1_more_loads_{i}", icon=":material/add:"):
        st.session_state["as_nzs_3000_c1_num_loads"] += 1
        st.rerun()

# Submit button
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
        if is_point_based:
            instance = load_group_cls(
                num_loads=num_loads,
                num_living_units=num_living_units,
            )
        else:
            instance = load_group_cls(
                rating=rating,
                # num_loads=num_loads,
                rating_unit=rating_unit,
                num_living_units=num_living_units,
            )
        st.session_state["as_nzs_3000_c1_load_entries"].append(
            {
                "label": selected_label,
                "rating": rating,
                "num_loads": num_loads,
                "rating_unit": rating_unit,
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
if st.session_state["as_nzs_3000_c1_load_entries"]:
    # Display each load group entry
    for i, entry in enumerate(st.session_state["as_nzs_3000_c1_load_entries"]):
        header_cols = st.columns([3, 2, 2, 1], vertical_alignment="bottom")

        # Header
        with header_cols[0]:
            st.markdown("**Load**")
        with header_cols[1]:
            st.markdown("**Maximum Demand**")
        with header_cols[2]:
            st.markdown("**Connected Load**")

        # Load groups
        cols = st.columns([3, 2, 2, 1])
        with cols[0]:
            unit = "A" if entry["rating_unit"] == "A" else "W"
            st.markdown(
                f"**{entry['label']}**  \n"
                f"{entry['num_loads']} × {entry['rating']} {unit}"
                # f" = **{entry['total_rating']:.2f}".rstrip("0").rstrip(".") + " A**"
            )
        with cols[1]:
            st.metric(
                "Max demand",
                f"{entry['max_demand_a']:.2f} A",
                label_visibility="collapsed",
            )
        with cols[3]:
            if st.button("✕", key=f"as_nzs_3000_c1_remove_{i}"):
                st.session_state["as_nzs_3000_c1_load_entries"].pop(i)

    # Totals
    st.divider()
    total_cols = st.columns([3, 2, 2, 1], vertical_alignment="bottom")
    with total_cols[0]:
        st.markdown("**Total**")
    with total_cols[1]:
        total_max_a = sum(
            e["max_demand_a"] for e in st.session_state["as_nzs_3000_c1_load_entries"]
        )
        st.metric(
            "Total max demand",
            f"{total_max_a:.2f} A",
            label_visibility="collapsed",
        )
        total_max_w = sum(
            e["max_demand_w"] for e in st.session_state["as_nzs_3000_c1_load_entries"]
        )
        st.metric(
            "Total connected load",
            f"{total_max_w:.0f} W",
            label_visibility="collapsed",
        )
    with total_cols[2]:
        st.markdown(
            f"= **{total_max_w:.2f}".rstrip("0").rstrip(".") + " W**"
        )  # Total connected load in watts

    # Clear all button
    if st.button("Clear all"):
        st.session_state["as_nzs_3000_c1_load_entries"].clear()
        st.rerun()
else:
    st.info("No load groups added yet.")
