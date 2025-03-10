"""
modules/visualizations.py
Reusable visualization components for the SEED dashboard
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import folium
from folium import plugins
from streamlit_folium import folium_static
import io
import base64

# Define a metadata dictionary to store visualization context for the chatbot
visualization_metadata = {}

def register_visualization(vis_id, title, description, insights=None, data_fields=None):
    """Register visualization metadata for chatbot context"""
    visualization_metadata[vis_id] = {
        "title": title,
        "description": description,
        "insights": insights or [],
        "data_fields": data_fields or []
    }
    return vis_id

def create_choropleth(df, location_col, value_col, title, color_scale='Viridis', scope='usa', 
                      hover_data=None, vis_id=None):
    """Create a choropleth map visualization"""
    fig = px.choropleth(
        df,
        locations=location_col,
        locationmode="USA-states",
        color=value_col,
        scope=scope,
        color_continuous_scale=color_scale,
        labels={value_col: title},
        hover_data=hover_data
    )
    fig.update_layout(
        title=title,
        geo=dict(lakecolor='rgb(255, 255, 255)'),
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_colorbar=dict(title=title)
    )
    
    # Register metadata if vis_id is provided
    if vis_id:
        # Extract insights
        if df[value_col].notna().any():
            top_3 = df.nlargest(3, value_col)
            bottom_3 = df.nsmallest(3, value_col)
            
            top_locations = ", ".join(top_3[location_col].astype(str).tolist())
            bottom_locations = ", ".join(bottom_3[location_col].astype(str).tolist())
            
            insights = [
                f"Top areas: {top_locations}",
                f"Bottom areas: {bottom_locations}",
                f"Average value: {df[value_col].mean():.2f}"
            ]
        else:
            insights = ["No data available for insights"]
            
        register_visualization(
            vis_id, 
            title,
            f"Choropleth map showing {value_col} by {location_col}",
            insights,
            [location_col, value_col] + (hover_data or [])
        )
    
    return fig

def create_bar_chart(df, x_col, y_col, color_col=None, orientation='v', title='', 
                     text_col=None, color_continuous_scale='Viridis', vis_id=None):
    """Create a bar chart visualization"""
    fig = px.bar(
        df,
        x=x_col if orientation == 'v' else y_col,
        y=y_col if orientation == 'v' else x_col,
        color=color_col,
        color_continuous_scale=color_continuous_scale if color_col else None,
        orientation=orientation,
        title=title,
        text=text_col
    )
    
    if text_col:
        fig.update_traces(textposition='outside')
    
    # Register metadata if vis_id is provided
    if vis_id:
        # Extract insights
        primary_col = y_col if orientation == 'v' else x_col
        category_col = x_col if orientation == 'v' else y_col
        
        if df[primary_col].notna().any():
            highest = df.nlargest(1, primary_col)
            lowest = df.nsmallest(1, primary_col)
            
            highest_category = highest[category_col].iloc[0]
            highest_value = highest[primary_col].iloc[0]
            lowest_category = lowest[category_col].iloc[0]
            lowest_value = lowest[primary_col].iloc[0]
            
            insights = [
                f"Highest: {highest_category} ({highest_value:.2f})",
                f"Lowest: {lowest_category} ({lowest_value:.2f})",
                f"Average: {df[primary_col].mean():.2f}"
            ]
        else:
            insights = ["No data available for insights"]
            
        register_visualization(
            vis_id, 
            title,
            f"Bar chart showing {primary_col} by {category_col}",
            insights,
            [x_col, y_col] + ([color_col] if color_col else []) + ([text_col] if text_col else [])
        )
        
    return fig

def create_scatter_plot(df, x_col, y_col, color_col=None, size_col=None, 
                        hover_data=None, title='', vis_id=None):
    """Create a scatter plot visualization"""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col,
        hover_data=hover_data,
        title=title
    )
    
    # Add trendline
    if df[x_col].notna().any() and df[y_col].notna().any():
        try:
            fig.update_layout(
                shapes=[
                    dict(
                        type='line',
                        yref='y', xref='x',
                        x0=df[x_col].min(),
                        y0=np.polyval(np.polyfit(df[x_col], df[y_col], 1), df[x_col].min()),
                        x1=df[x_col].max(),
                        y1=np.polyval(np.polyfit(df[x_col], df[y_col], 1), df[x_col].max()),
                        line=dict(color="red", width=2, dash="dash"),
                    )
                ]
            )
        except:
            # If trendline fails, just continue without it
            pass
    
    # Register metadata if vis_id is provided
    if vis_id:
        # Calculate correlation if both columns are numeric
        try:
            correlation = df[[x_col, y_col]].corr().iloc[0, 1]
            corr_strength = "strong positive" if correlation > 0.7 else \
                           "moderate positive" if correlation > 0.3 else \
                           "weak positive" if correlation > 0 else \
                           "weak negative" if correlation > -0.3 else \
                           "moderate negative" if correlation > -0.7 else \
                           "strong negative"
            
            insights = [f"Correlation: {correlation:.2f} ({corr_strength})"]
        except:
            insights = ["Correlation could not be calculated"]
            
        register_visualization(
            vis_id, 
            title,
            f"Scatter plot showing relationship between {x_col} and {y_col}",
            insights,
            [x_col, y_col] + ([color_col] if color_col else []) + 
            ([size_col] if size_col else []) + (hover_data or [])
        )
    
    return fig

def create_line_chart(df, x_col, y_col, color_col=None, title='', markers=True, vis_id=None):
    """Create a line chart visualization"""
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        markers=markers
    )
    
    # Register metadata if vis_id is provided
    if vis_id:
        if df[y_col].notna().any():
            # Calculate trend
            try:
                first_value = df.iloc[0][y_col] if df[x_col].is_monotonic_increasing else df.iloc[-1][y_col]
                last_value = df.iloc[-1][y_col] if df[x_col].is_monotonic_increasing else df.iloc[0][y_col]
                percent_change = ((last_value - first_value) / first_value) * 100
                
                trend_direction = "increased" if percent_change > 0 else "decreased"
                
                insights = [
                    f"Overall trend: {trend_direction} by {abs(percent_change):.1f}%",
                    f"Highest value: {df[y_col].max():.2f}",
                    f"Lowest value: {df[y_col].min():.2f}"
                ]
            except:
                insights = ["Trend analysis could not be calculated"]
        else:
            insights = ["No data available for trend analysis"]
            
        register_visualization(
            vis_id, 
            title,
            f"Line chart showing {y_col} over {x_col}",
            insights,
            [x_col, y_col] + ([color_col] if color_col else [])
        )
    
    return fig

def create_pie_chart(df, values_col, names_col, title='', hole=0.4, vis_id=None):
    """Create a pie/donut chart visualization"""
    fig = px.pie(
        df,
        values=values_col,
        names=names_col,
        title=title,
        hole=hole
    )
    
    # Improve text visibility
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    # Register metadata if vis_id is provided
    if vis_id:
        if df[values_col].notna().any():
            total = df[values_col].sum()
            largest_category = df.nlargest(1, values_col).iloc[0]
            largest_name = largest_category[names_col]
            largest_value = largest_category[values_col]
            largest_pct = (largest_value / total) * 100
            
            insights = [
                f"Largest segment: {largest_name} ({largest_pct:.1f}%)",
                f"Total value: {total:.2f}",
                f"Number of categories: {len(df)}"
            ]
        else:
            insights = ["No data available for insights"]
            
        register_visualization(
            vis_id, 
            title,
            f"Pie chart showing distribution of {values_col} by {names_col}",
            insights,
            [values_col, names_col]
        )
    
    return fig

def create_heatmap(df, x_cols, y_cols, values, title='', color_scale='Viridis', vis_id=None):
    """Create a heatmap visualization"""
    # Reshape the data for the heatmap if needed
    if isinstance(df, pd.DataFrame) and x_cols in df.columns and y_cols in df.columns and values in df.columns:
        # If data is in long format, pivot it
        pivot_df = df.pivot(index=y_cols, columns=x_cols, values=values)
        z_data = pivot_df.values
        x_data = pivot_df.columns.tolist()
        y_data = pivot_df.index.tolist()
    else:
        # Assume data is already in the right format
        z_data = df
        x_data = x_cols
        y_data = y_cols
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_data,
        y=y_data,
        colorscale=color_scale,
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_cols if isinstance(x_cols, str) else '',
        yaxis_title=y_cols if isinstance(y_cols, str) else ''
    )
    
    # Register metadata if vis_id is provided
    if vis_id:
        if isinstance(z_data, np.ndarray) and z_data.size > 0:
            max_val = np.nanmax(z_data)
            min_val = np.nanmin(z_data)
            
            insights = [
                f"Maximum value: {max_val:.2f}",
                f"Minimum value: {min_val:.2f}",
                f"Average value: {np.nanmean(z_data):.2f}"
            ]
        else:
            insights = ["No data available for insights"]
            
        register_visualization(
            vis_id, 
            title,
            f"Heatmap visualization of {values if isinstance(values, str) else 'data values'}",
            insights,
            [x_cols, y_cols, values] if all(isinstance(x, str) for x in [x_cols, y_cols, values]) else []
        )
    
    return fig

def create_dual_axis_chart(df, x_col, y1_col, y2_col, y1_title, y2_title, title='', vis_id=None):
    """Create a dual-axis chart with bar and line"""
    fig = go.Figure()
    
    # Add a bar chart for the first y-axis
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[y1_col],
        name=y1_title,
        marker_color='darkblue',
        yaxis='y'
    ))
    
    # Add a line chart for the second y-axis
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y2_col],
        name=y2_title,
        marker_color='red',
        mode='lines+markers',
        yaxis='y2'
    ))
    
    # Update the layout
    fig.update_layout(
        title=title,
        yaxis=dict(title=y1_title),
        yaxis2=dict(
            title=y2_title,
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    # Register metadata if vis_id is provided
    if vis_id:
        if df[y1_col].notna().any() and df[y2_col].notna().any():
            # Calculate correlation between y1 and y2
            correlation = df[[y1_col, y2_col]].corr().iloc[0, 1]
            
            y1_trend = "increasing" if df[y1_col].iloc[-1] > df[y1_col].iloc[0] else "decreasing"
            y2_trend = "increasing" if df[y2_col].iloc[-1] > df[y2_col].iloc[0] else "decreasing"
            
            insights = [
                f"Correlation between {y1_title} and {y2_title}: {correlation:.2f}",
                f"Trend for {y1_title}: {y1_trend}",
                f"Trend for {y2_title}: {y2_trend}"
            ]
        else:
            insights = ["No data available for insights"]
            
        register_visualization(
            vis_id, 
            title,
            f"Dual-axis chart showing {y1_title} (bars) and {y2_title} (line) by {x_col}",
            insights,
            [x_col, y1_col, y2_col]
        )
    
    return fig

def create_folium_map(df, lat_col, lon_col, popup_cols=None, title=None, cluster=True, vis_id=None):
    """Create an interactive Folium map"""
    # Initialize map centered on the mean of coordinates
    if df[lat_col].notna().any() and df[lon_col].notna().any():
        center_lat = df[lat_col].mean()
        center_lon = df[lon_col].mean()
    else:
        # Default to continental US if no valid coordinates
        center_lat, center_lon = 39.8283, -98.5795
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add title if provided
    if title:
        title_html = f'''
             <h3 align="center" style="font-size:16px"><b>{title}</b></h3>
             '''
        m.get_root().html.add_child(folium.Element(title_html))
    
    # Add markers
    if cluster:
        marker_cluster = plugins.MarkerCluster().add_to(m)
    
    # Count valid locations for insights
    valid_locations = 0
    
    for _, row in df.iterrows():
        if pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
            valid_locations += 1
            
            # Create popup content
            popup_content = ""
            if popup_cols:
                for col in popup_cols:
                    if col in row and pd.notna(row[col]):
                        popup_content += f"<b>{col}:</b> {row[col]}<br>"
            
            # Add marker
            if cluster:
                folium.Marker(
                    [row[lat_col], row[lon_col]], 
                    popup=folium.Popup(popup_content, max_width=300)
                ).add_to(marker_cluster)
            else:
                folium.Marker(
                    [row[lat_col], row[lon_col]], 
                    popup=folium.Popup(popup_content, max_width=300)
                ).add_to(m)
    
    # Register metadata if vis_id is provided
    if vis_id:
        insights = [
            f"Number of locations shown: {valid_locations}",
            f"Map centered at: {center_lat:.2f}, {center_lon:.2f}"
        ]
        
        register_visualization(
            vis_id, 
            title or "Interactive Map",
            f"Interactive map showing locations with {', '.join(popup_cols) if popup_cols else 'data'}",
            insights,
            [lat_col, lon_col] + (popup_cols or [])
        )
    
    return m

def display_folium_map(m):
    """Display a Folium map in Streamlit"""
    # Use streamlit_folium's folium_static to display the map
    try:
        folium_static(m)
    except:
        # Fallback to custom renderer if streamlit_folium is not available
        html_str = m._repr_html_()
        html_file = io.StringIO()
        html_file.write(html_str)
        html_file.seek(0)
        
        # Read the HTML file
        html_data = html_file.read()
        
        # Embed the HTML in an iframe
        st.components.v1.html(html_data, height=500)

def display_metric_comparison(value, benchmark, label, format_str="{:.2f}", is_percent=False, higher_is_better=True):
    """Display a metric with comparison to benchmark"""
    formatted_value = format_str.format(value)
    
    if is_percent:
        formatted_value = formatted_value + "%"
    
    delta = value - benchmark
    if not higher_is_better:
        delta = -delta
    
    if is_percent:
        delta_format = "{:.1f}%"
    else:
        delta_format = format_str
    
    st.metric(
        label=label,
        value=formatted_value,
        delta=delta_format.format(delta),
        delta_color="normal" if delta == 0 else "good" if delta > 0 else "bad"
    )

def create_filter_section(df, filter_cols, title="Filters", use_multiselect=True):
    """Create a standardized filter section"""
    st.subheader(title)
    
    filters = {}
    
    for col in filter_cols:
        if col in df.columns:
            unique_values = sorted(df[col].dropna().unique().tolist())
            if len(unique_values) > 0:
                if use_multiselect:
                    filters[col] = st.multiselect(
                        f"Select {col}:",
                        options=["All"] + unique_values,
                        default=["All"]
                    )
                else:
                    filters[col] = st.selectbox(
                        f"Select {col}:",
                        options=["All"] + unique_values
                    )
    
    # Filter the dataframe based on selections
    filtered_df = df.copy()
    
    for col, selected in filters.items():
        if selected and "All" not in selected:
            if isinstance(selected, list):
                filtered_df = filtered_df[filtered_df[col].isin(selected)]
            else:
                filtered_df = filtered_df[filtered_df[col] == selected]
    
    return filtered_df, filters

def display_insights_expander(title, insights):
    """Display insights in an expandable section"""
    with st.expander(f"{title} Insights"):
        for insight in insights:
            st.markdown(f"• {insight}")

def get_visualization_metadata():
    """Get all visualization metadata for chatbot context"""
    return visualization_metadata