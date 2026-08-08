import pandas as pd
import plotly.express as px
import streamlit as st

from db_connection import engine

# ==============================
# Page Config
# ==============================
st.set_page_config(page_title="Economic Indicators", page_icon="📊", layout="wide")
st.markdown("""
<style>
/* Reduce vertical spacing around all dividers */
section[data-testid="stSidebar"] hr {
    margin-top: 0.3rem !important;
    margin-bottom: 0.3rem !important;
}
</style>
""", unsafe_allow_html=True)
st.title("Economic Indicators")


# ==============================
# Metadata Helper
# ==============================
@st.cache_data
def load_indicators():
    query = """
    SELECT
        i.indicator_id,
        i.indicator_name,
        i.table_name,
        i.publication_frequency,
        i.value_column,
        i.dimension_column,
        i.description
    FROM dbo.indicator_sources i
    WHERE EXISTS (
        SELECT 1
        FROM sys.tables t
        WHERE t.name = i.table_name
    )
    ORDER BY i.indicator_name
    """

    return pd.read_sql(query, engine)


def get_indicator_info(indicator_name):
    row = indicators_df[indicators_df["indicator_name"] == indicator_name].iloc[0]

    return row


@st.cache_data
def get_dimensions(table_name, dimension_column):
    query = f"""
    SELECT DISTINCT [{dimension_column}]
    FROM dbo.[{table_name}]
    WHERE [{dimension_column}] IS NOT NULL
    ORDER BY [{dimension_column}]
    """

    df = pd.read_sql(query, engine)

    return df[dimension_column].tolist()


@st.cache_data
def get_table_range(table_name):
    query = f"""
    SELECT
        MIN(date_g) AS MinDate,
        MAX(date_g) AS MaxDate
    FROM dbo.[{table_name}]
    """

    df = pd.read_sql(query, engine)

    return (df.loc[0, "MinDate"], df.loc[0, "MaxDate"])


@st.cache_data
def get_indicator_data(table_name, value_column, dimension_column, selected_dimension, start_date, end_date):
    params = [start_date, end_date]

    dimension_condition = ""

    if pd.notna(dimension_column):
        dimension_condition = f"""
        AND [{dimension_column}] = ?
        """
        params.append(selected_dimension)

    query = f"""
    SELECT
        date_g,
        [{value_column}] AS value
    FROM dbo.[{table_name}]
    WHERE date_g BETWEEN ? AND ?
    {dimension_condition}
    ORDER BY date_g
    """

    data = pd.read_sql(query, engine, params=tuple(params))

    if data.empty:
        return data

    data["date_g"] = pd.to_datetime(data["date_g"])

    data["value"] = pd.to_numeric(data["value"], errors="coerce")

    data = (data.dropna(subset=["date_g", "value"]).sort_values("date_g"))

    return data


indicators_df = load_indicators()

# ==============================
# Sidebar
# ==============================

with st.sidebar:
    st.header("Data Selection")

    # ------------------------------
    # Indicator Selection
    # ------------------------------
    selected_indicators = st.multiselect("Select indicators", options=indicators_df["indicator_name"].tolist())

    # ------------------------------
    # Display Mode
    # ------------------------------
    display_mode = st.radio("Data view", ["Full table", "Main value"], horizontal=True)

# ==============================
# Empty State
# ==============================

if len(selected_indicators) == 0:
    st.info(" Select at least one indicator.")
    st.stop()

# ==============================
# Get Selected Metadata
# ==============================

selected_meta = []

for indicator in selected_indicators:
    info = get_indicator_info(indicator)

    min_date, max_date = get_table_range(info["table_name"])

    selected_meta.append(
        {"Indicator": indicator, "Table": info["table_name"], "MinDate": min_date, "MaxDate": max_date})

metadata_df = pd.DataFrame(selected_meta)

# ==============================
# Global Date Range
# ==============================

metadata_df = metadata_df.dropna(subset=["MinDate", "MaxDate"])

global_min = pd.to_datetime(metadata_df["MinDate"].max()).date()

global_max = pd.to_datetime(metadata_df["MaxDate"].min()).date()

# ==============================
# Sidebar - Date Range
# ==============================

with st.sidebar:
    st.divider()
    st.markdown("#### Time range")

    start_col, end_col = st.columns(2)

    with start_col:
        start_date = st.date_input("From:", value=global_min, min_value=global_min, max_value=global_max)

    with end_col:
        end_date = st.date_input("To:", value=global_max, min_value=global_min, max_value=global_max)

    # ==============================
    # Dimensions
    # ==============================
    st.divider()
    st.markdown("#### Group Selection")

    selected_dimensions = {}

    for indicator in selected_indicators:
        info = get_indicator_info(indicator)

        if pd.notna(info["dimension_column"]):
            dimensions = get_dimensions(info["table_name"], info["dimension_column"])

            selected_dimensions[indicator] = st.selectbox(f"Select {indicator.split('-')[0]} group", options=dimensions)

# ==============================
# Tabs
# ==============================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [" Data tables ", " Charts ", " Comparison ", " Indicator Analysis ", " Source Information "])
# ==============================
# Tab 1
# ==============================
with tab1:
    for indicator in selected_indicators:
        info = get_indicator_info(indicator)
        table_name = info["table_name"]
        # st.markdown(f"### {indicator}")

        # ------------------------------
        # Parameters
        # ------------------------------
        params = [start_date, end_date]

        dimension_condition = ""

        if pd.notna(info["dimension_column"]):
            dimension_column = info["dimension_column"]
            selected_dimension = selected_dimensions[indicator]

            dimension_condition = f"""
            AND [{dimension_column}] = ?
            """
            params.append(selected_dimension)

        # ------------------------------
        # Query
        # ------------------------------
        if display_mode == "Full table":
            query = f"""
            SELECT *
            FROM dbo.[{table_name}]
            WHERE date_g BETWEEN ? AND ?
            {dimension_condition}
            """
        else:
            value_column = info["value_column"]
            query = f"""
            SELECT
                date_g,
                [{value_column}] AS value
            FROM dbo.[{table_name}]
            WHERE date_g BETWEEN ? AND ?
            {dimension_condition}
            """

        # ------------------------------
        # Load data
        # ------------------------------
        data = pd.read_sql(query, engine, params=tuple(params))

        # ------------------------------
        # Table title
        # ------------------------------
        if pd.notna(info["dimension_column"]):
            st.markdown(f"### {indicator.split('-')[0]} — {selected_dimension}")
        else:
            st.markdown(f"### {indicator}")

        # ------------------------------
        # Display
        # ------------------------------
        st.dataframe(data, use_container_width=True, hide_index=True)

# ==============================
# Tab 2 - Charts
# ==============================
with tab2:
    st.subheader("Indicator Trends")

    for indicator in selected_indicators:
        info = get_indicator_info(indicator)
        table_name = info["table_name"]
        value_column = info["value_column"]

        # ------------------------------
        # Parameters
        # ------------------------------
        params = [start_date, end_date]

        dimension_condition = ""

        if pd.notna(info["dimension_column"]):
            dimension_column = info["dimension_column"]
            selected_dimension = selected_dimensions[indicator]
            dimension_condition = f"""
            AND [{dimension_column}] = ?
            """
            params.append(selected_dimension)

        # ------------------------------
        # Query
        # ------------------------------
        query = f"""
        SELECT
            date_g,
            [{value_column}] AS value
        FROM dbo.[{table_name}]
        WHERE date_g BETWEEN ? AND ?
        {dimension_condition}
        ORDER BY date_g
        """
        data = pd.read_sql(query, engine, params=tuple(params))
        # ------------------------------
        # Empty data
        # ------------------------------
        if data.empty:
            st.warning(f"No data available for {indicator} in the selected range.")
            continue

        # ------------------------------
        # Prepare data
        # ------------------------------
        data["date_g"] = pd.to_datetime(data["date_g"])

        # ------------------------------
        # Chart title
        # ------------------------------
        if pd.notna(info["dimension_column"]):
            st.markdown(f"### {indicator} — {selected_dimension}")
        else:
            st.markdown(f"### {indicator}")
        # ------------------------------
        # Chart
        # ------------------------------

        st.line_chart(data, x="date_g", y="value")

# ==============================
# Tab 3 - Comparison
# ==============================
with tab3:
    st.subheader("Compare Indicators")
    comparison_indicators = st.multiselect("Select indicators to compare", options=selected_indicators)
    comparison_method = st.radio("Comparison method", ["Index 100", "Percentage Change"], horizontal=True)
    compare_button = st.button("Compare", type="primary")
    if compare_button:
        if len(comparison_indicators) < 2:
            st.warning("Please select at least two indicators.")
        else:
            comparison_data = []
            for indicator in comparison_indicators:
                info = get_indicator_info(indicator)
                table_name = info["table_name"]
                value_column = info["value_column"]
                # ------------------------------
                # Dimension filter
                # ------------------------------
                dimension_condition = ""
                params = [start_date, end_date]
                if pd.notna(info["dimension_column"]):
                    dimension_column = info["dimension_column"]
                    selected_dimension = selected_dimensions[indicator]

                    dimension_condition = f"""
                    AND [{dimension_column}] = ?
                    """

                    params.append(selected_dimension)
                # ------------------------------
                # Query
                # ------------------------------
                query = f"""
                SELECT
                    date_g,
                    [{value_column}] AS value
                FROM dbo.[{table_name}]
                WHERE date_g BETWEEN ? AND ?
                {dimension_condition}
                ORDER BY date_g
                """
                data = pd.read_sql(query, engine, params=tuple(params))

                if data.empty:
                    continue
                data["date_g"] = pd.to_datetime(data["date_g"])
                data["value"] = pd.to_numeric(data["value"], errors="coerce")
                data = data.dropna(subset=["date_g", "value"]).sort_values("date_g")

                if data.empty:
                    continue

                # ------------------------------
                # Index 100
                # ------------------------------
                if comparison_method == "Index 100":
                    first_value = data["value"].iloc[0]
                    if first_value == 0:
                        st.warning(f"{indicator}: "
                                   "first value is zero and cannot be normalized.")
                        continue
                    data["comparison_value"] = (data["value"] / first_value) * 100

                # ------------------------------
                # Percentage Change
                # ------------------------------
                else:
                    data["comparison_value"] = (data["value"].pct_change() * 100)
                data["Indicator"] = indicator
                comparison_data.append(data[["date_g", "Indicator", "comparison_value"]])

            # ------------------------------
            # Create comparison dataframe
            # ------------------------------
            if comparison_data:
                comparison_df = pd.concat(comparison_data, ignore_index=True)
                comparison_df = comparison_df.sort_values(["date_g", "Indicator"])
                """"""
                duplicates = (comparison_df.groupby(["date_g", "Indicator"]).size().reset_index(name="count"))
                # ------------------------------
                # Chart
                # ------------------------------
                chart_df = comparison_df.pivot(index="date_g", columns="Indicator", values="comparison_value")
                if comparison_method == "Index 100":
                    y_title = "Index (Base = 100)"
                else:
                    y_title = "Percentage Change (%)"

                fig = px.line(comparison_df, x="date_g", y="comparison_value", color="Indicator", markers=True,
                              color_discrete_sequence=px.colors.qualitative.Safe)

                fig.update_layout(xaxis_title="Date", yaxis_title=y_title)

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for comparison.")

# ==============================
# Tab 4 - Indicator Analysis
# ==============================

with tab4:
    st.subheader("Indicator Analysis")

    # ------------------------------
    # Available operations
    # ------------------------------
    single_indicator_operations = ["Percentage Change", "Index 100", "Moving Average"]

    pair_indicator_operations = ["Ratio", "Sum", "Difference"]

    # If fewer than 2 indicators are selected,
    # reset the operation to a single-indicator operation.
    if len(selected_indicators) < 2:
        if st.session_state.get("analysis_operation") in pair_indicator_operations:
            st.session_state["analysis_operation"] = "Percentage Change"

        available_operations = single_indicator_operations

    else:
        available_operations = (single_indicator_operations + pair_indicator_operations)

    operation = st.selectbox("Select operation", available_operations, key="analysis_operation")

    # ==============================
    # Percentage Change
    # ==============================
    if operation == "Percentage Change":

        indicator = st.selectbox("Select indicator", options=selected_indicators, key="percentage_change_indicator")

        info = get_indicator_info(indicator)

        selected_dimension = None

        if pd.notna(info["dimension_column"]):
            selected_dimension = selected_dimensions[indicator]

        data = get_indicator_data(info["table_name"], info["value_column"], info["dimension_column"],
                                  selected_dimension,
                                  start_date, end_date)

        if data.empty:
            st.warning(f"No data available for {indicator}.")

        else:
            data["percentage_change"] = (data["value"].pct_change() * 100)

            data = data.dropna(subset=["percentage_change"])

            # ------------------------------
            # Title
            # ------------------------------
            if pd.notna(info["dimension_column"]):
                st.markdown(f"### {indicator} — {selected_dimension}")
            else:
                st.markdown(f"### {indicator}")

            # ------------------------------
            # Data table
            # ------------------------------
            st.dataframe(data[["date_g", "value", "percentage_change"]], use_container_width=True, height=220,
                         hide_index=True)

            # ------------------------------
            # Chart
            # ------------------------------
            fig = px.line(data, x="date_g", y="percentage_change", markers=True)

            fig.update_layout(xaxis_title="Date", yaxis_title="Percentage Change (%)")

            st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Index 100
    # ==============================
    elif operation == "Index 100":

        indicator = st.selectbox("Select indicator", options=selected_indicators, key="index_100_indicator")

        info = get_indicator_info(indicator)

        selected_dimension = None

        if pd.notna(info["dimension_column"]):
            selected_dimension = selected_dimensions[indicator]

        data = get_indicator_data(info["table_name"], info["value_column"], info["dimension_column"],
                                  selected_dimension,
                                  start_date, end_date)

        if data.empty:
            st.warning(f"No data available for {indicator}.")

        else:
            first_value = data["value"].iloc[0]

            if first_value == 0:
                st.warning(f"{indicator}: first value is zero "
                           "and cannot be normalized.")

            else:
                data["index_100"] = (data["value"] / first_value) * 100

                # ------------------------------
                # Title
                # ------------------------------
                if pd.notna(info["dimension_column"]):
                    st.markdown(f"### {indicator} — {selected_dimension}")
                else:
                    st.markdown(f"### {indicator}")

                # ------------------------------
                # Data table
                # ------------------------------
                st.dataframe(data[["date_g", "value", "index_100"]], use_container_width=True, height=220,
                             hide_index=True)

                # ------------------------------
                # Chart
                # ------------------------------
                fig = px.line(data, x="date_g", y="index_100", markers=True)

                fig.update_layout(xaxis_title="Date", yaxis_title="Index (Base = 100)")

                st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Moving Average
    # ==============================
    elif operation == "Moving Average":

        indicator = st.selectbox("Select indicator", options=selected_indicators, key="moving_average_indicator")

        window = st.number_input("Moving average window", min_value=2, max_value=365, value=7, step=1)

        info = get_indicator_info(indicator)

        selected_dimension = None

        if pd.notna(info["dimension_column"]):
            selected_dimension = selected_dimensions[indicator]

        data = get_indicator_data(info["table_name"], info["value_column"], info["dimension_column"],
                                  selected_dimension,
                                  start_date, end_date)

        if data.empty:
            st.warning(f"No data available for {indicator}.")

        else:
            data["moving_average"] = (data["value"].rolling(window=int(window)).mean())

            # ------------------------------
            # Title
            # ------------------------------
            if pd.notna(info["dimension_column"]):
                st.markdown(f"### {indicator} — {selected_dimension}")
            else:
                st.markdown(f"### {indicator}")

            # ------------------------------
            # Data table
            # ------------------------------
            st.dataframe(data[["date_g", "value", "moving_average"]], use_container_width=True, height=220,
                         hide_index=True)

            # ------------------------------
            # Chart
            # ------------------------------
            fig = px.line(data, x="date_g", y="moving_average", markers=True)

            fig.update_layout(xaxis_title="Date", yaxis_title=f"Moving Average ({int(window)})")

            st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Ratio
    # ==============================
    elif operation == "Ratio":

        col1, col2 = st.columns(2)

        with col1:
            indicator_1 = st.selectbox("First indicator", options=selected_indicators, key="ratio_indicator_1")

        with col2:
            indicator_2 = st.selectbox("Second indicator", options=[indicator for indicator in selected_indicators if
                                                                    indicator != indicator_1], key="ratio_indicator_2")

        info_1 = get_indicator_info(indicator_1)
        info_2 = get_indicator_info(indicator_2)

        dimension_1 = None
        dimension_2 = None

        if pd.notna(info_1["dimension_column"]):
            dimension_1 = selected_dimensions[indicator_1]

        if pd.notna(info_2["dimension_column"]):
            dimension_2 = selected_dimensions[indicator_2]

        data_1 = get_indicator_data(info_1["table_name"], info_1["value_column"], info_1["dimension_column"],
                                    dimension_1,
                                    start_date, end_date)

        data_2 = get_indicator_data(info_2["table_name"], info_2["value_column"], info_2["dimension_column"],
                                    dimension_2,
                                    start_date, end_date)

        if data_1.empty or data_2.empty:
            st.warning("No data available for the selected indicators.")

        else:
            data_1 = data_1.rename(columns={"value": "value_1"})

            data_2 = data_2.rename(columns={"value": "value_2"})

            data = pd.merge(data_1[["date_g", "value_1"]], data_2[["date_g", "value_2"]], on="date_g", how="inner")

            data["result"] = (data["value_1"] / data["value_2"].replace(0, pd.NA))

            data = data.dropna(subset=["result"])

            st.markdown(f"### {indicator_1} / {indicator_2}")

            st.dataframe(data[["date_g", "value_1", "value_2", "result"]], use_container_width=True, hide_index=True,
                         height=220)

            fig = px.line(data, x="date_g", y="result", markers=True)

            fig.update_layout(xaxis_title="Date", yaxis_title="Ratio")

            st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Sum
    # ==============================
    elif operation == "Sum":

        col1, col2 = st.columns(2)

        with col1:
            indicator_1 = st.selectbox("First indicator", options=selected_indicators, key="sum_indicator_1")

        with col2:
            indicator_2 = st.selectbox("Second indicator", options=[indicator for indicator in selected_indicators if
                                                                    indicator != indicator_1], key="sum_indicator_2")

        info_1 = get_indicator_info(indicator_1)
        info_2 = get_indicator_info(indicator_2)

        dimension_1 = None
        dimension_2 = None

        if pd.notna(info_1["dimension_column"]):
            dimension_1 = selected_dimensions[indicator_1]

        if pd.notna(info_2["dimension_column"]):
            dimension_2 = selected_dimensions[indicator_2]

        data_1 = get_indicator_data(info_1["table_name"], info_1["value_column"], info_1["dimension_column"],
                                    dimension_1,
                                    start_date, end_date)

        data_2 = get_indicator_data(info_2["table_name"], info_2["value_column"], info_2["dimension_column"],
                                    dimension_2,
                                    start_date, end_date)

        if data_1.empty or data_2.empty:
            st.warning("No data available for the selected indicators.")

        else:
            data_1 = data_1.rename(columns={"value": "value_1"})

            data_2 = data_2.rename(columns={"value": "value_2"})

            data = pd.merge(data_1[["date_g", "value_1"]], data_2[["date_g", "value_2"]], on="date_g", how="inner")

            data["result"] = (data["value_1"] + data["value_2"])

            st.markdown(f"### {indicator_1} + {indicator_2}")

            st.dataframe(data[["date_g", "value_1", "value_2", "result"]], use_container_width=True, hide_index=True,
                         height=220)

            fig = px.line(data, x="date_g", y="result", markers=True)

            fig.update_layout(xaxis_title="Date", yaxis_title="Sum")

            st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Difference
    # ==============================
    elif operation == "Difference":

        col1, col2 = st.columns(2)

        with col1:
            indicator_1 = st.selectbox("First indicator", options=selected_indicators, key="difference_indicator_1")

        with col2:
            indicator_2 = st.selectbox("Second indicator", options=[indicator for indicator in selected_indicators if
                                                                    indicator != indicator_1],
                                       key="difference_indicator_2")

        info_1 = get_indicator_info(indicator_1)
        info_2 = get_indicator_info(indicator_2)

        dimension_1 = None
        dimension_2 = None

        if pd.notna(info_1["dimension_column"]):
            dimension_1 = selected_dimensions[indicator_1]

        if pd.notna(info_2["dimension_column"]):
            dimension_2 = selected_dimensions[indicator_2]

        data_1 = get_indicator_data(info_1["table_name"], info_1["value_column"], info_1["dimension_column"],
                                    dimension_1,
                                    start_date, end_date)

        data_2 = get_indicator_data(info_2["table_name"], info_2["value_column"], info_2["dimension_column"],
                                    dimension_2,
                                    start_date, end_date)

        if data_1.empty or data_2.empty:
            st.warning("No data available for the selected indicators.")

        else:
            data_1 = data_1.rename(columns={"value": "value_1"})

            data_2 = data_2.rename(columns={"value": "value_2"})

            data = pd.merge(data_1[["date_g", "value_1"]], data_2[["date_g", "value_2"]], on="date_g", how="inner")

            data["result"] = (data["value_1"] - data["value_2"])

            st.markdown(f"### {indicator_1} − {indicator_2}")

            st.dataframe(data[["date_g", "value_1", "value_2", "result"]], use_container_width=True, hide_index=True,
                         height=220)

            fig = px.line(data, x="date_g", y="result", markers=True)

            fig.update_layout(xaxis_title="Date", yaxis_title="Difference")

            st.plotly_chart(fig, use_container_width=True)

# ==============================
# Tab 5
# ==============================
with tab5:
    st.subheader("Data Source Information")
    st.dataframe(metadata_df, use_container_width=True, hide_index=True)
