import pandas as pd
import plotly.express as px
import streamlit as st

from db_connection import engine

# ==============================
# Page Config
# ==============================

st.set_page_config(page_title="Economic Indicators", page_icon="📊", layout="wide", )

st.title("Economic Indicators")


# ==============================
# Metadata Helpers
# ==============================

@st.cache_data
def load_indicators():
    query_text = """
    SELECT
        i.indicator_id,
        i.indicator_name,
        i.table_name,
        i.publication_frequency,
        i.value_column,
        i.dimension_column,
        i.description
    FROM dbo.indicator_sources AS i
    WHERE EXISTS (
        SELECT 1
        FROM sys.tables AS t
        WHERE t.name = i.table_name
    )
    ORDER BY i.indicator_name
    """

    return pd.read_sql(query_text, engine)


def get_indicator_info(indicators_metadata, indicator_name):
    indicator_metadata = indicators_metadata.loc[indicators_metadata["indicator_name"] == indicator_name].iloc[0]

    return indicator_metadata


@st.cache_data
def get_dimensions(table_name, dimension_column):
    query_text = f"""
    SELECT DISTINCT [{dimension_column}]
    FROM dbo.[{table_name}]
    WHERE [{dimension_column}] IS NOT NULL
    ORDER BY [{dimension_column}]
    """

    dimensions_df = pd.read_sql(query_text, engine)

    return dimensions_df[dimension_column].tolist()


@st.cache_data
def get_table_date_range(table_name):
    query_text = f"""
    SELECT
        MIN(date_g) AS min_date,
        MAX(date_g) AS max_date
    FROM dbo.[{table_name}]
    """

    date_range_df = pd.read_sql(query_text, engine)

    return (date_range_df.loc[0, "min_date"], date_range_df.loc[0, "max_date"],)


def get_selected_dimension(indicator_metadata, selected_dimensions, indicator_name, ):
    dimension_column = indicator_metadata["dimension_column"]

    if pd.notna(dimension_column):
        return selected_dimensions[indicator_name]

    return None


def build_dimension_condition(dimension_column, selected_dimension, ):
    if pd.isna(dimension_column):
        return "", []

    dimension_condition = f"""
        AND [{dimension_column}] = ?
    """

    return dimension_condition, [selected_dimension]


# ==============================
# Data Helpers
# ==============================

@st.cache_data
def load_indicator_data(table_name, value_column, dimension_column, selected_dimension, start_date, end_date, ):
    dimension_condition, dimension_params = build_dimension_condition(dimension_column, selected_dimension, )

    query_params = [start_date, end_date]
    query_params.extend(dimension_params)

    query_text = f"""
    SELECT
        date_g,
        [{value_column}] AS value
    FROM dbo.[{table_name}]
    WHERE date_g BETWEEN ? AND ?
    {dimension_condition}
    ORDER BY date_g
    """

    indicator_data = pd.read_sql(query_text, engine, params=tuple(query_params), )

    if indicator_data.empty:
        return indicator_data

    indicator_data["date_g"] = pd.to_datetime(indicator_data["date_g"], errors="coerce", )

    indicator_data["value"] = pd.to_numeric(indicator_data["value"], errors="coerce", )

    indicator_data = (indicator_data.dropna(subset=["date_g", "value"]).sort_values("date_g"))

    return indicator_data


@st.cache_data
def load_indicator_table(table_name, dimension_column, selected_dimension, start_date, end_date, ):
    dimension_condition, dimension_params = build_dimension_condition(dimension_column, selected_dimension, )

    query_params = [start_date, end_date]
    query_params.extend(dimension_params)

    query_text = f"""
    SELECT *
    FROM dbo.[{table_name}]
    WHERE date_g BETWEEN ? AND ?
    {dimension_condition}
    """

    return pd.read_sql(query_text, engine, params=tuple(query_params), )


def prepare_indicator_data(indicator_metadata, selected_dimensions, indicator_name, start_date, end_date, ):
    selected_dimension = get_selected_dimension(indicator_metadata, selected_dimensions, indicator_name, )

    indicator_data = load_indicator_data(table_name=indicator_metadata["table_name"],
        value_column=indicator_metadata["value_column"], dimension_column=indicator_metadata["dimension_column"],
        selected_dimension=selected_dimension, start_date=start_date, end_date=end_date, )

    return indicator_data, selected_dimension


def display_indicator_title(indicator_name, selected_dimension, ):
    if selected_dimension is not None:
        st.markdown(f"### {indicator_name} — {selected_dimension}")
    else:
        st.markdown(f"### {indicator_name}")


# ==============================
# Pair Indicator Helpers
# ==============================

def load_pair_indicator_data(first_indicator_name, second_indicator_name, indicators_metadata, selected_dimensions,
        start_date, end_date, ):
    first_metadata = get_indicator_info(indicators_metadata, first_indicator_name, )

    second_metadata = get_indicator_info(indicators_metadata, second_indicator_name, )

    first_data, first_dimension = prepare_indicator_data(first_metadata, selected_dimensions, first_indicator_name,
        start_date, end_date, )

    second_data, second_dimension = prepare_indicator_data(second_metadata, selected_dimensions, second_indicator_name,
        start_date, end_date, )

    if first_data.empty or second_data.empty:
        return None, first_dimension, second_dimension

    first_data = first_data.rename(columns={"value": "value_1"})

    second_data = second_data.rename(columns={"value": "value_2"})

    merged_data = pd.merge(first_data[["date_g", "value_1"]], second_data[["date_g", "value_2"]], on="date_g",
        how="inner", )

    return merged_data, first_dimension, second_dimension


def apply_pair_operation(pair_data, operation, ):
    if operation == "Ratio":
        pair_data["result"] = (pair_data["value_1"] / pair_data["value_2"].replace(0, pd.NA))

    elif operation == "Sum":
        pair_data["result"] = (pair_data["value_1"] + pair_data["value_2"])

    elif operation == "Difference":
        pair_data["result"] = (pair_data["value_1"] - pair_data["value_2"])

    return pair_data.dropna(subset=["result"])


def get_pair_operation_title(first_indicator_name, second_indicator_name, operation, ):
    operation_symbols = {"Ratio": "/", "Sum": "+", "Difference": "−", }

    return (f"{first_indicator_name} "
            f"{operation_symbols[operation]} "
            f"{second_indicator_name}")


def get_pair_y_axis_title(operation):
    return {"Ratio": "Ratio", "Sum": "Sum", "Difference": "Difference", }[operation]


def display_pair_result(pair_data, first_indicator_name, second_indicator_name, operation, ):
    pair_data = apply_pair_operation(pair_data, operation, )

    if pair_data.empty:
        st.warning("No valid data available for the selected indicators.")
        return

    st.markdown(f"### {get_pair_operation_title(first_indicator_name, second_indicator_name, operation, )}")

    st.dataframe(pair_data[["date_g", "value_1", "value_2", "result"]], use_container_width=True, hide_index=True,
        height=220, )

    figure = px.line(pair_data, x="date_g", y="result", markers=True, )

    figure.update_layout(xaxis_title="Date", yaxis_title=get_pair_y_axis_title(operation), )

    st.plotly_chart(figure, use_container_width=True, )


# ==============================
# Analysis Helpers
# ==============================

def apply_single_indicator_operation(indicator_data, operation, moving_average_window=None, ):
    if operation == "Percentage Change":
        indicator_data["percentage_change"] = (indicator_data["value"].pct_change() * 100)

        return (indicator_data.dropna(subset=["percentage_change"]))

    if operation == "Index 100":
        first_value = indicator_data["value"].iloc[0]

        if first_value == 0:
            return None

        indicator_data["index_100"] = (indicator_data["value"] / first_value * 100)

        return indicator_data

    if operation == "Moving Average":
        indicator_data["moving_average"] = (indicator_data["value"].rolling(window=int(moving_average_window)).mean())

        return indicator_data

    return indicator_data


def display_single_indicator_analysis(indicator_data, indicator_name, selected_dimension, operation,
        moving_average_window=None, ):
    if indicator_data.empty:
        st.warning(f"No data available for {indicator_name}.")
        return

    transformed_data = apply_single_indicator_operation(indicator_data, operation, moving_average_window, )

    if transformed_data is None:
        st.warning(f"{indicator_name}: first value is zero "
                   "and cannot be normalized.")
        return

    display_indicator_title(indicator_name, selected_dimension, )

    result_columns = {"Percentage Change": ["date_g", "value", "percentage_change", ],
        "Index 100": ["date_g", "value", "index_100", ], "Moving Average": ["date_g", "value", "moving_average", ], }

    result_y_columns = {"Percentage Change": "percentage_change", "Index 100": "index_100",
        "Moving Average": "moving_average", }

    result_y_titles = {"Percentage Change": "Percentage Change (%)", "Index 100": "Index (Base = 100)",
        "Moving Average": (f"Moving Average ({int(moving_average_window)})"), }

    st.dataframe(transformed_data[result_columns[operation]], use_container_width=True, height=220, hide_index=True, )

    figure = px.line(transformed_data, x="date_g", y=result_y_columns[operation], markers=True, )

    figure.update_layout(xaxis_title="Date", yaxis_title=result_y_titles[operation], )

    st.plotly_chart(figure, use_container_width=True, )


# ==============================
# Load Metadata
# ==============================

indicators_metadata = load_indicators()

# ==============================
# Sidebar
# ==============================

with st.sidebar:
    st.header("Data Selection")

    selected_indicators = st.multiselect("Select indicators", options=indicators_metadata["indicator_name"].tolist(), )

    display_mode = st.radio("Data view", ["Full table", "Main value"], horizontal=True, )

# ==============================
# Empty State
# ==============================

if not selected_indicators:
    st.info("Select at least one indicator.")
    st.stop()

# ==============================
# Selected Metadata
# ==============================

selected_metadata_records = []

for selected_indicator_name in selected_indicators:
    indicator_metadata = get_indicator_info(indicators_metadata, selected_indicator_name, )

    minimum_date, maximum_date = get_table_date_range(indicator_metadata["table_name"])

    selected_metadata_records.append(
        {"Indicator": selected_indicator_name, "Table": indicator_metadata["table_name"], "MinDate": minimum_date,
            "MaxDate": maximum_date, })

metadata_df = pd.DataFrame(selected_metadata_records)

# ==============================
# Global Date Range
# ==============================

metadata_df = metadata_df.dropna(subset=["MinDate", "MaxDate"])

global_min_date = (pd.to_datetime(metadata_df["MinDate"].max()).date())

global_max_date = (pd.to_datetime(metadata_df["MaxDate"].min()).date())

# ==============================
# Sidebar - Date Range
# ==============================

with st.sidebar:
    st.divider()
    st.markdown("#### Time range")

    start_column, end_column = st.columns(2)

    with start_column:
        start_date = st.date_input("From:", value=global_min_date, min_value=global_min_date,
            max_value=global_max_date, )

    with end_column:
        end_date = st.date_input("To:", value=global_max_date, min_value=global_min_date, max_value=global_max_date, )

    # ==============================
    # Dimensions
    # ==============================

    st.divider()
    st.markdown("#### Group Selection")

    selected_dimensions = {}

    for selected_indicator_name in selected_indicators:
        indicator_metadata = get_indicator_info(indicators_metadata, selected_indicator_name, )

        dimension_column = indicator_metadata["dimension_column"]

        if pd.notna(dimension_column):
            available_dimensions = get_dimensions(indicator_metadata["table_name"], dimension_column, )

            selected_dimensions[selected_indicator_name] = st.selectbox(f"Select {selected_indicator_name} group",
                options=available_dimensions, )

# ==============================
# Tabs
# ==============================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Data tables", "Charts", "Comparison", "Indicator Analysis", "Source Information", ])

# ==============================
# Tab 1 - Data Tables
# ==============================

with tab1:
    st.subheader("Selected Data")

    for selected_indicator_name in selected_indicators:
        indicator_metadata = get_indicator_info(indicators_metadata, selected_indicator_name, )

        selected_dimension = get_selected_dimension(indicator_metadata, selected_dimensions, selected_indicator_name, )

        if display_mode == "Full table":
            indicator_table = load_indicator_table(table_name=indicator_metadata["table_name"],
                dimension_column=indicator_metadata["dimension_column"], selected_dimension=selected_dimension,
                start_date=start_date, end_date=end_date, )

        else:
            indicator_table = load_indicator_data(table_name=indicator_metadata["table_name"],
                value_column=indicator_metadata["value_column"],
                dimension_column=indicator_metadata["dimension_column"], selected_dimension=selected_dimension,
                start_date=start_date, end_date=end_date, )

        display_indicator_title(selected_indicator_name, selected_dimension, )

        st.dataframe(indicator_table, use_container_width=True, hide_index=True, )

# ==============================
# Tab 2 - Charts
# ==============================

with tab2:
    st.subheader("Indicator Trends")

    for selected_indicator_name in selected_indicators:
        indicator_metadata = get_indicator_info(indicators_metadata, selected_indicator_name, )

        indicator_data, selected_dimension = (
            prepare_indicator_data(indicator_metadata, selected_dimensions, selected_indicator_name, start_date,
                end_date, ))

        if indicator_data.empty:
            st.warning(f"No data available for "
                       f"{selected_indicator_name} "
                       "in the selected range.")
            continue

        display_indicator_title(selected_indicator_name, selected_dimension, )

        st.line_chart(indicator_data, x="date_g", y="value", )

# ==============================
# Tab 3 - Comparison
# ==============================

with tab3:
    st.subheader("Compare Indicators")

    comparison_indicators = st.multiselect("Select indicators to compare", options=selected_indicators, )

    comparison_method = st.radio("Comparison method", ["Index 100", "Percentage Change"], horizontal=True, )

    compare_button_clicked = st.button("Compare", type="primary", )

    if compare_button_clicked:
        if len(comparison_indicators) < 2:
            st.warning("Please select at least two indicators.")

        else:
            comparison_records = []

            for selected_indicator_name in comparison_indicators:
                indicator_metadata = get_indicator_info(indicators_metadata, selected_indicator_name, )

                indicator_data, _ = prepare_indicator_data(indicator_metadata, selected_dimensions,
                    selected_indicator_name, start_date, end_date, )

                if indicator_data.empty:
                    continue

                if comparison_method == "Index 100":
                    first_value = (indicator_data["value"].iloc[0])

                    if first_value == 0:
                        st.warning(f"{selected_indicator_name}: "
                                   "first value is zero and "
                                   "cannot be normalized.")
                        continue

                    indicator_data["comparison_value"] = (indicator_data["value"] / first_value * 100)

                else:
                    indicator_data["comparison_value"] = (indicator_data["value"].pct_change() * 100)

                indicator_data["indicator"] = (selected_indicator_name)

                comparison_records.append(indicator_data[["date_g", "indicator", "comparison_value", ]])

            if comparison_records:
                comparison_result_df = pd.concat(comparison_records, ignore_index=True, )

                comparison_result_df = (comparison_result_df.sort_values(["date_g", "indicator"]))

                y_axis_title = ("Index (Base = 100)" if comparison_method == "Index 100" else "Percentage Change (%)")

                comparison_figure = px.line(comparison_result_df, x="date_g", y="comparison_value", color="indicator",
                    markers=True, color_discrete_sequence=(px.colors.qualitative.Safe), )

                comparison_figure.update_layout(xaxis_title="Date", yaxis_title=y_axis_title, )

                st.plotly_chart(comparison_figure, use_container_width=True, )

            else:
                st.warning("No data available for comparison.")

# ==============================
# Tab 4 - Indicator Analysis
# ==============================

with tab4:
    st.subheader("Indicator Analysis")

    single_indicator_operations = ["Percentage Change", "Index 100", "Moving Average", ]

    pair_indicator_operations = ["Ratio", "Sum", "Difference", ]

    if len(selected_indicators) < 2:
        if (st.session_state.get("analysis_operation") in pair_indicator_operations):
            st.session_state["analysis_operation"] = "Percentage Change"

        available_operations = (single_indicator_operations)

    else:
        available_operations = (single_indicator_operations + pair_indicator_operations)

    selected_operation = st.selectbox("Select operation", available_operations, key="analysis_operation", )

    # ==============================
    # Single Indicator Operations
    # ==============================

    if selected_operation in single_indicator_operations:

        operation_keys = {"Percentage Change": "percentage_change_indicator", "Index 100": "index_100_indicator",
            "Moving Average": "moving_average_indicator", }

        analysis_indicator_name = st.selectbox("Select indicator", options=selected_indicators,
            key=operation_keys[selected_operation], )

        moving_average_window = None

        if selected_operation == "Moving Average":
            moving_average_window = st.number_input("Moving average window", min_value=2, max_value=365, value=7,
                step=1, )

        analysis_metadata = get_indicator_info(indicators_metadata, analysis_indicator_name, )

        analysis_data, analysis_dimension = (
            prepare_indicator_data(analysis_metadata, selected_dimensions, analysis_indicator_name, start_date,
                end_date, ))

        display_single_indicator_analysis(indicator_data=analysis_data, indicator_name=analysis_indicator_name,
            selected_dimension=analysis_dimension, operation=selected_operation,
            moving_average_window=moving_average_window, )

    # ==============================
    # Pair Indicator Operations
    # ==============================

    elif selected_operation in pair_indicator_operations:

        first_indicator_column, second_indicator_column = (st.columns(2))

        with first_indicator_column:
            first_indicator_name = st.selectbox("First indicator", options=selected_indicators,
                key=f"{selected_operation.lower()}_indicator_1", )

        second_indicator_options = [selected_indicator_name for selected_indicator_name in selected_indicators if
            selected_indicator_name != first_indicator_name]

        with second_indicator_column:
            second_indicator_name = st.selectbox("Second indicator", options=second_indicator_options,
                key=f"{selected_operation.lower()}_indicator_2", )

        pair_data, _, _ = load_pair_indicator_data(first_indicator_name, second_indicator_name, indicators_metadata,
            selected_dimensions, start_date, end_date, )

        if pair_data is None or pair_data.empty:
            st.warning("No data available for the selected indicators.")

        else:
            display_pair_result(pair_data=pair_data, first_indicator_name=first_indicator_name,
                second_indicator_name=second_indicator_name, operation=selected_operation, )

# ==============================
# Tab 5 - Source Information
# ==============================

with tab5:
    st.subheader("Data Source Information")

    st.dataframe(metadata_df, use_container_width=True, hide_index=True, )
