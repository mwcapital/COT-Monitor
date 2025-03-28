import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime


def plot_cftc_data(data):
    """
    Create interactive plots for CFTC data with week-over-week changes and net positions

    Parameters:
    data (pd.DataFrame): The CFTC data to plot
    """
    st.subheader("Data Visualization")

    # Ensure data is sorted by date
    data = data.sort_values('date')

    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])

    # Fill missing values with previous values (for continuous visualization)
    data = data.fillna(method='ffill')

    # Add net position columns based on dataset type
    # For QDL/FON format (disaggregated)
    if ('producer_merchant_processor_user_longs' in data.columns and
            'producer_merchant_processor_user_shorts' in data.columns):

        # Add net position columns for FON format
        data['Commercial Net'] = data['producer_merchant_processor_user_longs'] - data[
            'producer_merchant_processor_user_shorts']

        if 'money_manager_longs' in data.columns and 'money_manager_shorts' in data.columns:
            data['Large Speculator Net'] = data['money_manager_longs'] - data['money_manager_shorts']

        if 'other_reportable_longs' in data.columns and 'other_reportable_shorts' in data.columns:
            data['Other Reportables Net'] = data['other_reportable_longs'] - data['other_reportable_shorts']

        if 'swap_dealer_longs' in data.columns and 'swap_dealer_shorts' in data.columns:
            data['Swap Dealer Net'] = data['swap_dealer_longs'] - data['swap_dealer_shorts']

    # For QDL/LFON format (legacy)
    elif ('commercial_longs' in data.columns and 'commercial_shorts' in data.columns):

        # Add net position columns for LFON format
        data['Commercial Net'] = data['commercial_longs'] - data['commercial_shorts']

        if 'non_commercial_longs' in data.columns and 'non_commercial_shorts' in data.columns:
            data['Large Speculator Net'] = data['non_commercial_longs'] - data['non_commercial_shorts']

        if 'non_reportable_longs' in data.columns and 'non_reportable_shorts' in data.columns:
            data['Small Speculator Net'] = data['non_reportable_longs'] - data['non_reportable_shorts']

    # If 'spreading' is available for either format, subtract it from the Large Speculator Net
    if 'spreading' in data.columns and 'Large Speculator Net' in data.columns:
        data['Large Speculator Net'] = data['Large Speculator Net'] - data['spreading']

    # Calculate change from previous week for all numerical columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

    # Create new DataFrame with changes
    data_change = data.copy()
    for col in numeric_cols:
        # Calculate absolute change
        data_change[f'{col}_change'] = data_change[col].diff()

        # Calculate percentage change
        data_change[f'{col}_change_pct'] = data_change[col].pct_change().multiply(100).round(1)

        # Calculate percentile ranks for different time periods
        if len(data) >= 260:  # If we have at least 5 years of data (52 weeks * 5)
            data_change[f'{col}_pct_5yr'] = data_change[col].rolling(260).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100).round(1)
        else:
            data_change[f'{col}_pct_5yr'] = np.nan

        if len(data) >= 104:  # If we have at least 2 years of data
            data_change[f'{col}_pct_2yr'] = data_change[col].rolling(104).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100).round(1)
        else:
            data_change[f'{col}_pct_2yr'] = np.nan

        if len(data) >= 52:  # If we have at least 1 year of data
            data_change[f'{col}_pct_1yr'] = data_change[col].rolling(52).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100).round(1)
        else:
            data_change[f'{col}_pct_1yr'] = np.nan

        # Year to date percentile (using first date of current year as reference)
        current_year = data['date'].max().year
        ytd_start = pd.to_datetime(f'{current_year}-01-01')
        ytd_data = data[data['date'] >= ytd_start]

        if not ytd_data.empty and len(ytd_data) > 1:
            # Create a temporary series for YTD values
            ytd_values = ytd_data[col]

            # Calculate percentile rank within YTD values
            data_change.loc[ytd_data.index, f'{col}_pct_ytd'] = ytd_values.rank(pct=True) * 100
        else:
            data_change[f'{col}_pct_ytd'] = np.nan

    # Create column selection options
    # Exclude 'None', 'contract_code', 'type', 'date' columns from plotting options
    plot_cols = [col for col in data.columns if col not in ['None', 'contract_code', 'type', 'date']]

    # Filter out market_participation from regular column options
    regular_plot_cols = [col for col in plot_cols if col != 'market_participation']

    # Let user select which columns to plot
    st.write("### Select Columns to Plot")

    # First, create a section specifically for net position columns
    st.write("#### Net Position Columns")
    net_position_cols = [col for col in regular_plot_cols if 'Net' in col]

    selected_cols = []

    if net_position_cols:
        cols_per_row = 3
        net_rows = [net_position_cols[i:i + cols_per_row] for i in range(0, len(net_position_cols), cols_per_row)]

        for row in net_rows:
            cols = st.columns(cols_per_row)
            for i, col in enumerate(row):
                if i < len(row):  # Ensure we don't go out of bounds
                    # Determine color for the checkbox label
                    label_color = ""
                    col_lower = row[i].lower()

                    if 'commercial net' in col_lower:
                        label_color = "red"
                    elif 'large speculator net' in col_lower:
                        label_color = "blue"
                    elif 'small speculator net' in col_lower or 'non_reportable net' in col_lower:
                        label_color = "orange"  # Using orange for burnt yellow in Streamlit
                    elif 'other reportables net' in col_lower:
                        label_color = "violet"
                    elif 'swap dealer net' in col_lower:
                        label_color = "orange"

                    # Add colored checkbox
                    if label_color:
                        if cols[i].checkbox(f":{label_color}[{row[i]}]", key=f"checkbox_{row[i]}"):
                            selected_cols.append(row[i])
                    else:
                        if cols[i].checkbox(row[i], key=f"checkbox_{row[i]}"):
                            selected_cols.append(row[i])
    else:
        st.info("No net position columns available. They may be calculated when necessary columns are present.")

    # Then show the original columns section
    st.write("#### Original Position Columns")
    # Remove net position columns from regular column options
    original_cols = [col for col in regular_plot_cols if 'Net' not in col]

    cols_per_row = 3
    original_rows = [original_cols[i:i + cols_per_row] for i in range(0, len(original_cols), cols_per_row)]

    for row in original_rows:
        cols = st.columns(cols_per_row)
        for i, col in enumerate(row):
            if i < len(row):  # Ensure we don't go out of bounds
                # Determine color for the checkbox label
                label_color = ""
                col_lower = row[i].lower()
                if 'non_commercial' in col_lower or 'money_manager' in col_lower:
                    label_color = "blue"
                elif 'commercial' in col_lower or 'producer' in col_lower:
                    label_color = "red"
                elif 'non_reportable' in col_lower:
                    label_color = "orange"  # Using orange for burnt yellow in Streamlit

                # Add colored checkbox
                if label_color:
                    if cols[i].checkbox(f":{label_color}[{row[i]}]", key=f"checkbox_{row[i]}"):
                        selected_cols.append(row[i])
                else:
                    if cols[i].checkbox(row[i], key=f"checkbox_{row[i]}"):
                        selected_cols.append(row[i])

    # Add a separate checkbox for market participation
    include_market_participation = False
    if 'market_participation' in plot_cols:
        include_market_participation = st.checkbox("Include Market Participation (with separate scale)", value=False)

    if not selected_cols and not include_market_participation:
        st.warning("Please select at least one column to plot.")
        return

    # Chart options
    st.write("### Chart Settings")

    # Plot type selection
    plot_type = st.radio("Plot Type", ["Line", "Bar"], horizontal=True)

    # Additional options
    separate_plots = st.checkbox("Create Separate Plots for Each Column", value=False)

    # Set fixed height for plots at 600px
    height_per_plot = 600

    # Create a date range selector instead of periods
    # Get min and max dates for the slider
    min_date = data['date'].min().date()
    max_date = data['date'].max().date()

    # Calculate the default start date (to show the last 89 periods by default)
    all_dates = sorted(data['date'].unique())
    default_start_date = all_dates[-min(89, len(all_dates))].date() if len(all_dates) > 1 else min_date
    default_end_date = max_date

    # Create a date range slider
    selected_start_date, selected_end_date = st.select_slider(
        "Select Date Range:",
        options=[d.date() for d in all_dates],
        value=(default_start_date, default_end_date)
    )

    # Convert to datetime for filtering
    selected_start_date = pd.to_datetime(selected_start_date)
    selected_end_date = pd.to_datetime(selected_end_date)

    # Filter data based on selected date range
    plot_data = data[(data['date'] >= selected_start_date) & (data['date'] <= selected_end_date)]
    plot_data_change = data_change[
        (data_change['date'] >= selected_start_date) & (data_change['date'] <= selected_end_date)]

    # Count the number of periods
    num_periods = len(plot_data)

    # Show info about the number of periods and the 90-period limit for showing changes
    if num_periods > 90:
        st.info(
            f"Note: Percentage changes will only be shown for 90 or fewer periods. Currently displaying {num_periods} periods.")

    # Start plotting
    st.write(
        f"## CFTC Data Visualization - {selected_start_date.strftime('%Y-%m-%d')} to {selected_end_date.strftime('%Y-%m-%d')}")

    # Define color mapping for various categories
    def get_color_for_column(column_name):
        column_lower = column_name.lower()

        # Net position colors - using a distinct color scheme
        if 'commercial net' in column_lower:
            return '#d62728'  # Red for Commercial Net
        elif 'large speculator net' in column_lower or 'money_manager net' in column_lower:
            return '#1f77b4'  # Blue for Large Speculator Net
        elif 'small speculator net' in column_lower or 'non_reportable net' in column_lower:
            return '#B8860B'  # Dark goldenrod (burnt yellow)
        elif 'other reportables net' in column_lower:
            return '#9467bd'  # Purple for Other Reportables Net
        elif 'swap dealer net' in column_lower:
            return '#ff7f0e'  # Orange for Swap Dealer Net

        # Original colors for standard columns
        elif 'non_commercial' in column_lower or 'money_manager' in column_lower:
            return '#1f77b4'  # Blue
        elif 'commercial' in column_lower or 'producer' in column_lower:
            return '#d62728'  # Red
        elif 'non_reportable' in column_lower:
            return '#B8860B'  # Dark goldenrod (burnt yellow)
        elif 'swap' in column_lower:
            return '#ff7f0e'  # Orange
        elif 'dealer' in column_lower:
            return '#2ca02c'  # Green
        elif 'other' in column_lower:
            return '#9467bd'  # Purple
        else:
            return None  # Use default Plotly colors

    # Create hover text with all the statistical information requested
    def create_hover_text(row, col):
        date_str = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
        value_str = f"{row[col]:,.0f}"

        # Change values
        change = row[f'{col}_change']
        change_pct = row[f'{col}_change_pct']
        change_str = f"Change: {change:+,.0f} ({change_pct:+.1f}%)" if not pd.isna(change) else "Change: N/A"

        # Percentile ranks
        pct_ytd = row[f'{col}_pct_ytd']
        pct_1yr = row[f'{col}_pct_1yr']
        pct_2yr = row[f'{col}_pct_2yr']
        pct_5yr = row[f'{col}_pct_5yr']

        pct_ytd_str = f"YTD Percentile: {pct_ytd:.1f}%" if not pd.isna(pct_ytd) else "YTD Percentile: N/A"
        pct_1yr_str = f"1Y Percentile: {pct_1yr:.1f}%" if not pd.isna(pct_1yr) else "1Y Percentile: N/A"
        pct_2yr_str = f"2Y Percentile: {pct_2yr:.1f}%" if not pd.isna(pct_2yr) else "2Y Percentile: N/A"
        pct_5yr_str = f"5Y Percentile: {pct_5yr:.1f}%" if not pd.isna(pct_5yr) else "5Y Percentile: N/A"

        hover_text = f"<b>{date_str}</b><br>{col}: {value_str}<br>{change_str}<br>{pct_ytd_str}<br>{pct_1yr_str}<br>{pct_2yr_str}<br>{pct_5yr_str}"
        return hover_text

    # Create hover texts for each data point
    for col in selected_cols:
        plot_data_change[f'{col}_hover'] = plot_data_change.apply(
            lambda row: create_hover_text(row, col), axis=1
        )

    # Create annotations for the change percentages
    annotations = []

    # Only create annotations if there are 90 or fewer periods
    if num_periods <= 90:
        for col in selected_cols:
            for i, (date, value, change_pct) in enumerate(zip(
                    plot_data_change['date'],
                    plot_data_change[col],
                    plot_data_change[f'{col}_change_pct']
            )):
                if not pd.isna(change_pct):
                    # Format the change percentage
                    change_text = f"{change_pct:+.1f}%"

                    # Create annotation with color based on value
                    annotation = dict(
                        x=date,
                        y=value,
                        text=change_text,
                        showarrow=False,
                        font=dict(
                            size=12,  # Increased font size
                            color="green" if change_pct > 0 else "red"  # Green for positive, red for negative
                        ),
                        xanchor="center",
                        yanchor="bottom",
                    )

                    if separate_plots:
                        # For separate plots, specify which subplot
                        subplot_idx = selected_cols.index(col) + 1
                        annotation["xref"] = f"x{subplot_idx}" if subplot_idx > 1 else "x"
                        annotation["yref"] = f"y{subplot_idx}" if subplot_idx > 1 else "y"

                    annotations.append(annotation)
    else:
        # If more than 90 periods are selected, create an annotation explaining why changes aren't shown
        explanation = dict(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text="Change percentages only available for 90 or fewer periods",
            showarrow=False,
            font=dict(size=14),
            visible=False  # Hidden by default, will only show when "Show Changes" is clicked
        )
        annotations.append(explanation)

    # Determine plot layout
    if separate_plots:
        # Create a separate subplot for each column
        fig = make_subplots(rows=len(selected_cols), cols=1,
                            subplot_titles=selected_cols,
                            shared_xaxes=True,
                            vertical_spacing=0.05)

        for i, col in enumerate(selected_cols):
            row = i + 1
            color = get_color_for_column(col)

            # Add appropriate trace based on plot type
            if plot_type == "Line":
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['date'],
                        y=plot_data[col],
                        mode='lines+markers',
                        name=col,
                        hoverinfo='text',
                        hovertext=plot_data_change[f'{col}_hover'],
                        line=dict(color=color) if color else dict(),
                    ),
                    row=row, col=1
                )
            else:  # Bar
                fig.add_trace(
                    go.Bar(
                        x=plot_data['date'],
                        y=plot_data[col],
                        name=col,
                        hoverinfo='text',
                        hovertext=plot_data_change[f'{col}_hover'],
                        marker=dict(color=color) if color else dict(),
                    ),
                    row=row, col=1
                )

            # Update y-axis title
            fig.update_yaxes(title_text=col, row=row, col=1)

        # Add market participation if requested (to each subplot)
        if include_market_participation and 'market_participation' in data.columns:
            for i in range(len(selected_cols)):
                row = i + 1
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['date'],
                        y=plot_data['market_participation'],
                        mode='lines',
                        name='Market Participation',
                        line=dict(color='gray', dash='dot'),
                        yaxis='y2'
                    ),
                    row=row, col=1
                )

                # Add secondary y-axis
                fig.update_layout(**{
                    f'yaxis{row * 2}': dict(
                        title='Market Participation',
                        titlefont=dict(color='gray'),
                        tickfont=dict(color='gray'),
                        overlaying=f'y{row * 2 - 1}',
                        side='right',
                        position=1.0
                    )
                })

        # Calculate total height based on number of plots with fixed height
        total_height = height_per_plot * len(selected_cols)

    else:
        # Create a single plot with all selected columns
        # For secondary y-axis, we'll use Plotly's built-in dual axis capabilities
        has_secondary_axis = include_market_participation and 'market_participation' in data.columns

        fig = go.Figure()

        for col in selected_cols:
            color = get_color_for_column(col)

            # Add appropriate trace based on plot type
            if plot_type == "Line":
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['date'],
                        y=plot_data[col],
                        mode='lines+markers',
                        name=col,
                        hoverinfo='text',
                        hovertext=plot_data_change[f'{col}_hover'],
                        line=dict(color=color) if color else dict(),
                    )
                )
            else:  # Bar
                fig.add_trace(
                    go.Bar(
                        x=plot_data['date'],
                        y=plot_data[col],
                        name=col,
                        hoverinfo='text',
                        hovertext=plot_data_change[f'{col}_hover'],
                        marker=dict(color=color) if color else dict(),
                    )
                )

        # Add market participation with secondary y-axis if requested
        if has_secondary_axis:
            # Create market participation hover text
            plot_data_change['market_participation_hover'] = plot_data_change.apply(
                lambda row: create_hover_text(row, 'market_participation'), axis=1
            )

            fig.add_trace(
                go.Scatter(
                    x=plot_data['date'],
                    y=plot_data['market_participation'],
                    mode='lines',
                    name='Market Participation',
                    line=dict(color='gray', dash='dot'),
                    yaxis='y2',
                    hoverinfo='text',
                    hovertext=plot_data_change['market_participation_hover']
                )
            )

            # Configure the secondary y-axis
            fig.update_layout(
                yaxis2=dict(
                    title='Market Participation',
                    titlefont=dict(color='gray'),
                    tickfont=dict(color='gray'),
                    anchor='x',
                    overlaying='y',
                    side='right',
                    position=1.02  # This moves it further to the right of the first y-axis
                )
            )

        total_height = height_per_plot

    # Create two versions of the layout - one with annotations and one without
    layout_with_annotations = {
        'annotations': annotations,
        'title': f"CFTC Data Visualization - {selected_start_date.strftime('%Y-%m-%d')} to {selected_end_date.strftime('%Y-%m-%d')} ({num_periods} periods)",
        'xaxis_title': "Date",
        'legend_title': "Data Series",
        'height': total_height,
        'hovermode': "closest",
        'legend': {
            'orientation': "h",
            'yanchor': "bottom",
            'y': 1.02,
            'xanchor': "center",
            'x': 0.5
        }
    }

    layout_without_annotations = {
        'annotations': [],
        'title': f"CFTC Data Visualization - {selected_start_date.strftime('%Y-%m-%d')} to {selected_end_date.strftime('%Y-%m-%d')} ({num_periods} periods)",
        'xaxis_title': "Date",
        'legend_title': "Data Series",
        'height': total_height,
        'hovermode': "closest",
        'legend': {
            'orientation': "h",
            'yanchor': "bottom",
            'y': 1.02,
            'xanchor': "center",
            'x': 0.5
        }
    }

    # Apply initial layout without annotations (changes hidden by default)
    fig.update_layout(layout_without_annotations)

    # Now add the buttons that will update the entire layout
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=[
                    dict(
                        args=[layout_with_annotations],
                        label="Show Changes",
                        method="relayout"
                    ),
                    dict(
                        args=[layout_without_annotations],
                        label="Hide Changes",
                        method="relayout"
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            )
        ]
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True)

    # Display some statistics about the selected columns
    st.write("### Data Statistics")

    # Show recent changes as a table
    st.write("#### Recent Week-over-Week Changes")
    show_cols = ['date']
    for col in selected_cols:
        if f'{col}_change_pct' in plot_data_change.columns:
            show_cols.append(f'{col}_change_pct')

    if len(show_cols) > 1:  # Only if we have at least one change column
        recent_changes = plot_data_change.iloc[-5:][show_cols]
        renamed_cols = {f'{col}_change_pct': f'{col} (% change)' for col in selected_cols if
                        f'{col}_change_pct' in plot_data_change.columns}
        recent_changes = recent_changes.rename(columns=renamed_cols)
        st.dataframe(recent_changes.style.format({col: "{:+.2f}%" for col in recent_changes.columns if col != 'date'}))

    # Add download button for the plotted data
    columns_to_download = ['date'] + selected_cols
    csv = plot_data[columns_to_download].to_csv(index=False)
    st.download_button(
        label="Download Plotted Data as CSV",
        data=csv,
        file_name="cftc_plotted_data.csv",
        mime="text/csv",
    )