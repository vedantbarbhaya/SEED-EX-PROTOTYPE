"""
modules/impact_giving.py
Implements the third part of the narrative: "What's the relationship between environmental impact and giving?"
More structured implementation based on the dashboard visualization suggestions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import folium
from folium import plugins
import io
from streamlit_folium import folium_static

# Import our visualization utilities if available
try:
    from modules.visualizations import (
        create_scatter_plot, create_bar_chart, create_heatmap, create_folium_map, 
        display_folium_map, display_insights_expander, create_filter_section
    )
except ImportError:
    # Define fallback functions if the module isn't available
    def create_scatter_plot(df, x_col, y_col, color_col=None, size_col=None, 
                          hover_data=None, title='', vis_id=None):
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            size=size_col,
            hover_data=hover_data,
            title=title
        )
        return fig
    
    def create_bar_chart(df, x_col, y_col, color_col=None, orientation='v', title='', 
                        text_col=None, color_continuous_scale='Viridis', vis_id=None):
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
        return fig
    
    def create_heatmap(df, x_cols, y_cols, values, title='', color_scale='Viridis', vis_id=None):
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
        return fig
    
    def create_folium_map(df, lat_col, lon_col, popup_cols=None, title=None, cluster=True, vis_id=None):
        # Initialize map centered on the mean of coordinates
        if df[lat_col].notna().any() and df[lon_col].notna().any():
            center_lat = df[lat_col].mean()
            center_lon = df[lon_col].mean()
        else:
            # Default to continental US if no valid coordinates
            center_lat, center_lon = 39.8283, -98.5795
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
        
        # Add markers with clustering
        if cluster:
            marker_cluster = plugins.MarkerCluster().add_to(m)
        
        for _, row in df.iterrows():
            if pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
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
        
        return m
    
    def display_folium_map(m):
        # Use streamlit_folium if available
        try:
            folium_static(m)
        except:
            # Fallback to custom renderer
            html_str = m._repr_html_()
            html_file = io.StringIO()
            html_file.write(html_str)
            html_file.seek(0)
            
            # Read the HTML file
            html_data = html_file.read()
            
            # Embed the HTML in an iframe
            st.components.v1.html(html_data, height=500)
    
    def display_insights_expander(title, insights):
        with st.expander(f"{title} Insights"):
            for insight in insights:
                st.markdown(f"• {insight}")
    
    def create_filter_section(df, filter_cols, title="Filters", use_multiselect=True):
        st.subheader(title)
        
        filters = {}
        filtered_df = df.copy()
        
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
        for col, selected in filters.items():
            if selected and "All" not in selected:
                if isinstance(selected, list):
                    filtered_df = filtered_df[filtered_df[col].isin(selected)]
                else:
                    filtered_df = filtered_df[filtered_df[col] == selected]
        
        return filtered_df, filters

def display_impact_giving_tab(df):
    """Display the Impact vs. Giving tab visualizations"""
    st.header("What's the relationship between environmental impact and giving?", help="This section explores the relationship between a company's environmental impact and its philanthropy.")
    
    # Brief introduction to this section
    st.markdown("""
    This section examines whether companies with larger environmental footprints contribute proportionally more to environmental causes.
    Are high-impact industries offsetting their footprint through philanthropy?
    """)
    
    # Check if we need to generate environmental impact data
    if not has_impact_data(df):
        st.warning("Environmental impact data not found in the dataset. Some visualizations may not be available.")
    
    # Create filter section
    filter_cols = []
    for col in ['industry', 'state', 'region', 'size']:
        if col in df.columns:
            filter_cols.append(col)
    
    if filter_cols:
        with st.expander("Apply Filters", expanded=False):
            filtered_df, _ = create_filter_section(df, filter_cols, title="Filter Companies")
    else:
        filtered_df = df
    
    # Use tabs for organization
    tab1, tab2, tab3 = st.tabs([
        "📊 Impact vs. Giving", 
        "💰 Loss Contingencies", 
        "🚩 Environmental Incidents"
    ])
    
    with tab1:
        # Environmental impact vs. giving visualization (#3)
        st.subheader("Environmental Impact vs. Environmental Giving")
        display_impact_vs_giving_chart(filtered_df)
    
    with tab2:
        # Loss Contingencies vs. Philanthropy (#8)
        st.subheader("Environmental Loss Contingencies vs. Giving")
        display_loss_contingencies_chart(filtered_df)
    
    with tab3:
        # Environmental incidents map (#21)
        st.subheader("Environmental Incidents Map")
        display_environmental_incidents_map(filtered_df)
    
    # Add correlation analysis section
    st.subheader("Impact-Giving Correlation Analysis")
    display_impact_correlation_analysis(filtered_df)

def has_impact_data(df):
    """Check if the dataframe has environmental impact data"""
    impact_columns = [
        'environmental_impact_score', 'emissions_tons', 'waste_tons',
        'water_usage_gallons', 'energy_consumption_mwh', 'incident_count',
        'Environmental Remediation Expenses', 'Accrual for Environmental Loss Contingencies'
    ]
    
    # Check if at least some impact columns exist
    return any(col in df.columns for col in impact_columns)

def display_impact_vs_giving_chart(df):
    """Display environmental impact vs. giving visualization"""
    # Determine impact column
    impact_col = None
    for col_option in ['environmental_impact_score', 'emissions_tons', 'Environmental Remediation Expenses']:
        if col_option in df.columns:
            impact_col = col_option
            break
    
    if impact_col is None:
        st.info("Environmental impact data not found in the dataset.")
        return
    
    # Determine giving column
    giving_col = None
    for col_option in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col_option in df.columns:
            giving_col = col_option
            break
    
    if giving_col is None:
        st.info("Environmental giving data not found in the dataset.")
        return
    
    # Get industry column if available
    industry_col = None
    for col_option in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
        if col_option in df.columns:
            industry_col = col_option
            break
    
    # Get revenue column if available
    revenue_col = None
    for col_option in ['revenue_millions', 'Revenue', 'Gross Profit', 'annual_revenue']:
        if col_option in df.columns:
            revenue_col = col_option
            break
    
    # Create scatter plot with filtering options
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown("### Filter Data")
        
        # Allow filtering by industry
        if industry_col:
            industries = sorted(df[industry_col].dropna().unique())
            selected_industries = st.multiselect(
                "Filter by Industry:", 
                options=["All Industries"] + list(industries),
                default=["All Industries"]
            )
            
            if "All Industries" not in selected_industries and selected_industries:
                filtered_df = df[df[industry_col].isin(selected_industries)]
            else:
                filtered_df = df
        else:
            filtered_df = df
        
        # Add a filter for company size if available
        size_col = None
        for col in ['size', 'Size', 'company_size', 'size_category']:
            if col in df.columns:
                size_col = col
                break
        
        if size_col:
            sizes = sorted(df[size_col].dropna().unique())
            selected_sizes = st.multiselect(
                "Filter by Size:", 
                options=["All Sizes"] + list(sizes),
                default=["All Sizes"]
            )
            
            if "All Sizes" not in selected_sizes and selected_sizes:
                filtered_df = filtered_df[filtered_df[size_col].isin(selected_sizes)]
    
    with col1:
        # Create the scatter plot
        hover_data = []
        
        if industry_col:
            hover_data.append(industry_col)
        
        if revenue_col:
            hover_data.append(revenue_col)
        
        if size_col:
            hover_data.append(size_col)
        
        if 'company_name' in filtered_df.columns:
            hover_data.append('company_name')
        elif 'Name' in filtered_df.columns:
            hover_data.append('Name')
        
        # Plot with optional bubble size based on revenue
        if revenue_col:
            fig = create_scatter_plot(
                filtered_df,
                x_col=impact_col,
                y_col=giving_col,
                color_col=industry_col if industry_col else None,
                size_col=revenue_col,
                hover_data=hover_data,
                title='Environmental Impact vs. Giving'
            )
        else:
            fig = create_scatter_plot(
                filtered_df,
                x_col=impact_col,
                y_col=giving_col,
                color_col=industry_col if industry_col else None,
                hover_data=hover_data,
                title='Environmental Impact vs. Giving'
            )
        
        # Add quadrant lines (at median values)
        median_impact = filtered_df[impact_col].median()
        median_giving = filtered_df[giving_col].median()
        
        fig.add_vline(x=median_impact, line_dash="dash", line_color="gray")
        fig.add_hline(y=median_giving, line_dash="dash", line_color="gray")
        
        # Add quadrant labels
        fig.add_annotation(
            x=filtered_df[impact_col].min() * 1.05,
            y=filtered_df[giving_col].max() * 0.95,
            text="Low Impact, High Giving",
            showarrow=False,
            font=dict(size=10, color="green")
        )
        
        fig.add_annotation(
            x=filtered_df[impact_col].max() * 0.95,
            y=filtered_df[giving_col].max() * 0.95,
            text="High Impact, High Giving",
            showarrow=False,
            font=dict(size=10, color="blue")
        )
        
        fig.add_annotation(
            x=filtered_df[impact_col].min() * 1.05,
            y=filtered_df[giving_col].min() * 1.05,
            text="Low Impact, Low Giving",
            showarrow=False,
            font=dict(size=10, color="gray")
        )
        
        fig.add_annotation(
            x=filtered_df[impact_col].max() * 0.95,
            y=filtered_df[giving_col].min() * 1.05,
            text="High Impact, Low Giving",
            showarrow=False,
            font=dict(size=10, color="red")
        )
        
        # Add a trend line if possible
        if len(filtered_df) > 1:
            try:
                # Calculate trend line
                z = np.polyfit(filtered_df[impact_col], filtered_df[giving_col], 1)
                p = np.poly1d(z)
                
                # Add trend line to the plot
                x_range = np.linspace(filtered_df[impact_col].min(), filtered_df[impact_col].max(), 100)
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=p(x_range),
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', dash='dash')
                ))
            except:
                # Skip trend line if it fails
                pass
        
        # Update axis labels
        impact_label = 'Environmental Impact Score'
        if impact_col == 'emissions_tons':
            impact_label = 'Emissions (Tons CO2e)'
        elif impact_col == 'Environmental Remediation Expenses':
            impact_label = 'Environmental Remediation Expenses'
        
        giving_label = 'Environmental Giving'
        if 'millions' in giving_col:
            giving_label += ' ($ Millions)'
        elif giving_col == 'Charitable Contributions':
            giving_label = 'Charitable Contributions'
        
        fig.update_layout(
            xaxis_title=impact_label,
            yaxis_title=giving_label
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    # Display insights
    with st.expander("Impact vs. Giving Insights"):
        # Calculate correlation
        correlation = filtered_df[[impact_col, giving_col]].corr().iloc[0, 1]
        
        # Calculate quadrant counts
        high_impact_high_giving = filtered_df[(filtered_df[impact_col] > median_impact) & (filtered_df[giving_col] > median_giving)].shape[0]
        high_impact_low_giving = filtered_df[(filtered_df[impact_col] > median_impact) & (filtered_df[giving_col] <= median_giving)].shape[0]
        low_impact_high_giving = filtered_df[(filtered_df[impact_col] <= median_impact) & (filtered_df[giving_col] > median_giving)].shape[0]
        low_impact_low_giving = filtered_df[(filtered_df[impact_col] <= median_impact) & (filtered_df[giving_col] <= median_giving)].shape[0]
        
        total_companies = filtered_df.shape[0]
        
        st.markdown("### Key Insights")
        
        # Correlation insight
        if correlation > 0.6:
            corr_strength = "strong positive"
        elif correlation > 0.3:
            corr_strength = "moderate positive"
        elif correlation > 0:
            corr_strength = "weak positive"
        elif correlation > -0.3:
            corr_strength = "weak negative"
        elif correlation > -0.6:
            corr_strength = "moderate negative"
        else:
            corr_strength = "strong negative"
        
        st.markdown(f"• There is a **{corr_strength} correlation** ({correlation:.2f}) between environmental impact and giving")
        
        # Quadrant insights
        st.markdown("### Quadrant Analysis")
        
        # Create a pie chart of the quadrant distribution
        quadrant_labels = ["High Impact, High Giving", "High Impact, Low Giving", "Low Impact, High Giving", "Low Impact, Low Giving"]
        quadrant_values = [high_impact_high_giving, high_impact_low_giving, low_impact_high_giving, low_impact_low_giving]
        quadrant_colors = ["blue", "red", "green", "gray"]
        
        fig = px.pie(
            values=quadrant_values,
            names=quadrant_labels,
            title="Distribution of Companies by Impact-Giving Quadrants",
            color_discrete_sequence=quadrant_colors
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f"• **{high_impact_high_giving}** companies ({high_impact_high_giving/total_companies*100:.1f}%) have high impact and high giving - potentially offsetting their footprint")
        st.markdown(f"• **{high_impact_low_giving}** companies ({high_impact_low_giving/total_companies*100:.1f}%) have high impact but low giving - potential greenwashing concerns")
        st.markdown(f"• **{low_impact_high_giving}** companies ({low_impact_high_giving/total_companies*100:.1f}%) have low impact and high giving - environmental leaders")
        st.markdown(f"• **{low_impact_low_giving}** companies ({low_impact_low_giving/total_companies*100:.1f}%) have low impact and low giving - may not prioritize environmental issues")
        
        # If industry data is available, show industry-specific insights
        if industry_col and len(selected_industries) > 0 and "All Industries" not in selected_industries:
            st.markdown("### Industry-Specific Insights")
            
            for industry in selected_industries:
                industry_df = filtered_df[filtered_df[industry_col] == industry]
                if len(industry_df) > 0:
                    industry_correlation = industry_df[[impact_col, giving_col]].corr().iloc[0, 1]
                    industry_avg_impact = industry_df[impact_col].mean()
                    industry_avg_giving = industry_df[giving_col].mean()
                    
                    overall_avg_impact = filtered_df[impact_col].mean()
                    overall_avg_giving = filtered_df[giving_col].mean()
                    
                    impact_comparison = "higher" if industry_avg_impact > overall_avg_impact else "lower"
                    giving_comparison = "higher" if industry_avg_giving > overall_avg_giving else "lower"
                    
                    st.markdown(f"**{industry}**: Impact-giving correlation: {industry_correlation:.2f}")
                    st.markdown(f"- Average impact is {industry_avg_impact:.1f} ({impact_comparison} than overall average)")
                    st.markdown(f"- Average giving is {industry_avg_giving:.1f} ({giving_comparison} than overall average)")

def display_loss_contingencies_chart(df):
    """Display environmental loss contingencies vs. giving visualization"""
    # Determine loss contingencies column
    contingencies_col = None
    for col_option in ['Accrual for Environmental Loss Contingencies', 'env_loss_contingencies_millions', 'env_loss_contingencies']:
        if col_option in df.columns:
            contingencies_col = col_option
            break
    
    # As fallback, check if remediation column exists
    if contingencies_col is None:
        for col_option in ['Environmental Remediation Expenses', 'env_remediation_expenses_millions', 'env_remediation_expenses']:
            if col_option in df.columns:
                contingencies_col = col_option
                break
    
    if contingencies_col is None:
        st.info("Environmental loss contingencies or remediation data not found in the dataset.")
        return
    
    # Determine giving column
    giving_col = None
    for col_option in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col_option in df.columns:
            giving_col = col_option
            break
    
    if giving_col is None:
        st.info("Environmental giving data not found in the dataset.")
        return
    
    # Get industry column if available
    industry_col = None
    for col_option in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
        if col_option in df.columns:
            industry_col = col_option
            break
    
    # Create scatter plot with filtering options
    # Filter to only include companies with both metrics
    filtered_df = df[df[contingencies_col].notna() & df[giving_col].notna()].copy()
    
    if len(filtered_df) == 0:
        st.info("Not enough data available for this visualization.")
        return
    
    # Create filter section in expander
    with st.expander("Filter Data", expanded=False):
        # Allow filtering by industry
        if industry_col:
            industries = sorted(filtered_df[industry_col].dropna().unique())
            selected_industries = st.multiselect(
                "Filter by Industry:", 
                options=["All Industries"] + list(industries),
                default=["All Industries"]
            )
            
            if "All Industries" not in selected_industries and selected_industries:
                filtered_df = filtered_df[filtered_df[industry_col].isin(selected_industries)]
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create the scatter plot
        hover_data = []
        
        if industry_col:
            hover_data.append(industry_col)
        
        if 'company_name' in filtered_df.columns:
            hover_data.append('company_name')
        elif 'Name' in filtered_df.columns:
            hover_data.append('Name')
        
        fig = create_scatter_plot(
            filtered_df,
            x_col=contingencies_col,
            y_col=giving_col,
            color_col=industry_col if industry_col else None,
            hover_data=hover_data,
            title='Environmental Loss Contingencies vs. Philanthropic Giving'
        )
        
        # Add a trend line if possible
        if len(filtered_df) > 1:
            try:
                # Calculate trend line
                z = np.polyfit(filtered_df[contingencies_col], filtered_df[giving_col], 1)
                p = np.poly1d(z)
                
                # Add trend line to the plot
                x_range = np.linspace(filtered_df[contingencies_col].min(), filtered_df[contingencies_col].max(), 100)
                fig.add_trace(go.Scatter(
                    x=x_range,
                    y=p(x_range),
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', dash='dash')
                ))
            except:
                # Skip trend line if it fails
                pass
        
        # Update axis labels
        contingencies_label = 'Environmental Loss Contingencies'
        if 'millions' in contingencies_col:
            contingencies_label += ' ($ Millions)'
        elif contingencies_col == 'Environmental Remediation Expenses':
            contingencies_label = 'Environmental Remediation Expenses'
        
        giving_label = 'Environmental Giving'
        if 'millions' in giving_col:
            giving_label += ' ($ Millions)'
        elif giving_col == 'Charitable Contributions':
            giving_label = 'Charitable Contributions'
        
        fig.update_layout(
            xaxis_title=contingencies_label,
            yaxis_title=giving_label
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Calculate ratio statistics
        filtered_df['giving_to_contingencies_ratio'] = filtered_df[giving_col] / filtered_df[contingencies_col]
        
        median_ratio = filtered_df['giving_to_contingencies_ratio'].median()
        
        # Display basic stats
        st.metric(
            label="Median Giving to Contingencies Ratio",
            value=f"{median_ratio:.2f}x",
            help="Higher values indicate companies giving more relative to their environmental liabilities"
        )
        
        # Calculate correlation
        correlation = filtered_df[[contingencies_col, giving_col]].corr().iloc[0, 1]
        
        st.metric(
            label="Correlation",
            value=f"{correlation:.2f}",
            help="Measures the strength of the relationship between loss contingencies and giving"
        )
        
        # Calculate percentage with ratio > 1
        ratio_gt_1_pct = (filtered_df['giving_to_contingencies_ratio'] > 1).mean() * 100
        
        st.metric(
            label="% with Giving > Contingencies",
            value=f"{ratio_gt_1_pct:.1f}%",
            help="Percentage of companies that give more than their environmental liabilities"
        )
    
    # Display insights
    with st.expander("Loss Contingencies vs. Giving Insights"):
        # Identify companies with highest and lowest ratios
        highest_ratio_companies = filtered_df.nlargest(5, 'giving_to_contingencies_ratio')
        lowest_ratio_companies = filtered_df.nsmallest(5, 'giving_to_contingencies_ratio')
        
        st.markdown("### Key Insights")
        
        # Correlation insight
        st.markdown(f"• Correlation between loss contingencies and giving: **{correlation:.2f}**")
        
        # Ratio insights
        st.markdown(f"• Median ratio of giving to contingencies: **{median_ratio:.2f}**")
        
        if median_ratio > 1:
            st.markdown(f"• Companies typically spend **{median_ratio:.1f}x more** on environmental giving than they reserve for environmental liabilities")
        else:
            st.markdown(f"• Companies typically reserve **{1/median_ratio:.1f}x more** for environmental liabilities than they spend on environmental giving")
        
        # Create columns for high and low ratio companies
        col1, col2 = st.columns(2)
        
        with col1:
            # High ratio companies
            st.markdown("### Highest Giving to Contingencies Ratio")
            
            name_col = 'company_name' if 'company_name' in filtered_df.columns else 'Name'
            
            # Create a formatted table
            high_ratio_display = pd.DataFrame({
                'Company': highest_ratio_companies[name_col],
                'Ratio': highest_ratio_companies['giving_to_contingencies_ratio'],
                'Industry': highest_ratio_companies[industry_col] if industry_col else 'Unknown'
            })
            
            st.dataframe(
                high_ratio_display,
                column_config={
                    'Company': st.column_config.TextColumn('Company'),
                    'Ratio': st.column_config.NumberColumn('Ratio', format="%.1fx"),
                    'Industry': st.column_config.TextColumn('Industry')
                },
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            # Low ratio companies
            st.markdown("### Lowest Giving to Contingencies Ratio")
            
            # Create a formatted table
            low_ratio_display = pd.DataFrame({
                'Company': lowest_ratio_companies[name_col],
                'Ratio': lowest_ratio_companies['giving_to_contingencies_ratio'],
                'Industry': lowest_ratio_companies[industry_col] if industry_col else 'Unknown'
            })
            
            st.dataframe(
                low_ratio_display,
                column_config={
                    'Company': st.column_config.TextColumn('Company'),
                    'Ratio': st.column_config.NumberColumn('Ratio', format="%.2fx"),
                    'Industry': st.column_config.TextColumn('Industry')
                },
                hide_index=True,
                use_container_width=True
            )
        
        # Industry-specific insights
        if industry_col:
            st.markdown("### Industry-Specific Insights")
            
            industry_ratios = filtered_df.groupby(industry_col)['giving_to_contingencies_ratio'].agg(['mean', 'count']).reset_index()
            industry_ratios = industry_ratios[industry_ratios['count'] >= 3]  # Only show industries with at least 3 companies
            industry_ratios = industry_ratios.sort_values('mean', ascending=False)
            
            # Create a bar chart of industry ratios
            fig = px.bar(
                industry_ratios.head(10),
                x=industry_col,
                y='mean',
                title='Giving to Contingencies Ratio by Industry (Top 10)',
                labels={industry_col: 'Industry', 'mean': 'Average Ratio'},
                text='count'
            )
            
            fig.update_traces(texttemplate='%{text} companies', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            for _, row in industry_ratios.head(3).iterrows():
                st.markdown(f"• **{row[industry_col]}**: Average ratio of {row['mean']:.2f}x ({row['count']} companies)")
            
            st.markdown("---")
            
            for _, row in industry_ratios.tail(3).iterrows():
                st.markdown(f"• **{row[industry_col]}**: Average ratio of {row['mean']:.2f}x ({row['count']} companies)")

def display_environmental_incidents_map(df):
    """Display environmental incidents map visualization"""
    # Check if we have incident data
    has_incidents = hasattr(df, 'incident_df') and isinstance(df.incident_df, pd.DataFrame)
    
    if not has_incidents:
        # Check if we have incident count in the main dataframe
        if 'incident_count' not in df.columns:
            st.info("Environmental incident data not found in the dataset.")
            return
        
        # If we don't have a dedicated incident dataframe but have counts, create a simple visualization
        companies_with_incidents = df[df['incident_count'] > 0].copy()
        
        if len(companies_with_incidents) == 0:
            st.info("No environmental incidents recorded in the dataset.")
            return
        
        # Check if we have location data
        has_coords = all(col in companies_with_incidents.columns for col in ['latitude', 'longitude'])
        
        if not has_coords:
            # Create a simple bar chart of incident counts by industry
            industry_col = None
            for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
                if col in companies_with_incidents.columns:
                    industry_col = col
                    break
            
            if industry_col:
                incident_by_industry = companies_with_incidents.groupby(industry_col)['incident_count'].sum().reset_index()
                incident_by_industry = incident_by_industry.sort_values('incident_count', ascending=False)
                
                fig = create_bar_chart(
                    incident_by_industry.head(10),
                    x_col='incident_count',
                    y_col=industry_col,
                    title='Environmental Incidents by Industry',
                    orientation='h'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("Incident location data not available for mapping. Showing incident counts by industry instead.")
            else:
                st.metric("Total Environmental Incidents", f"{companies_with_incidents['incident_count'].sum():.0f}")
                st.info("Detailed incident location and industry data not available.")
            return
        
        # If we have coordinates, create a map
        name_col = 'company_name' if 'company_name' in companies_with_incidents.columns else 'Name'
        popup_cols = [name_col, 'incident_count']
        
        if industry_col:
            popup_cols.append(industry_col)
        
        # Create folium map
        m = create_folium_map(
            companies_with_incidents,
            lat_col='latitude',
            lon_col='longitude',
            popup_cols=popup_cols,
            title='Companies with Environmental Incidents'
        )
        
        # Display the map
        display_folium_map(m)
        
        # Add context
        st.markdown(f"Map showing **{len(companies_with_incidents)}** companies with recorded environmental incidents. The size of each marker indicates the number of incidents.")
        
        return
    
    # If we have a dedicated incident dataframe, create a detailed map
    incident_df = df.incident_df
    
    # Create filter section
    with st.expander("Filter Incidents", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Filter by incident type
            if 'incident_type' in incident_df.columns:
                incident_types = sorted(incident_df['incident_type'].unique())
                selected_types = st.multiselect(
                    "Filter by Incident Type:",
                    options=["All Types"] + incident_types,
                    default=["All Types"]
                )
                
                if "All Types" not in selected_types and selected_types:
                    filtered_incidents = incident_df[incident_df['incident_type'].isin(selected_types)]
                else:
                    filtered_incidents = incident_df
            else:
                filtered_incidents = incident_df
        
        with col2:
            # Filter by severity if available
            if 'severity' in filtered_incidents.columns:
                min_severity = int(filtered_incidents['severity'].min())
                max_severity = int(filtered_incidents['severity'].max())
                
                selected_severity = st.slider(
                    "Minimum Incident Severity:",
                    min_value=min_severity,
                    max_value=max_severity,
                    value=min_severity
                )
                
                filtered_incidents = filtered_incidents[filtered_incidents['severity'] >= selected_severity]
    
    if len(filtered_incidents) == 0:
        st.info("No incidents match the selected filters.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create popup columns for the map
        popup_cols = ['company_name', 'incident_type', 'severity', 'impact_description', 'year']
        popup_cols = [col for col in popup_cols if col in filtered_incidents.columns]
        
        # Add environmental justice community info if available
        if 'in_environmental_justice_community' in filtered_incidents.columns:
            popup_cols.append('in_environmental_justice_community')
        
        # Create folium map
        m = create_folium_map(
            filtered_incidents,
            lat_col='latitude',
            lon_col='longitude',
            popup_cols=popup_cols,
            title='Environmental Incidents Map'
        )
        
        # Display the map
        display_folium_map(m)
        
        # Add context
        incident_count = len(filtered_incidents)
        company_count = filtered_incidents['company_name'].nunique() if 'company_name' in filtered_incidents.columns else 'multiple'
        
        st.markdown(f"Map showing **{incident_count}** environmental incidents from **{company_count}** companies.")
    
    with col2:
        # Display incident statistics
        st.markdown("### Incident Statistics")
        
        # Count by type
        if 'incident_type' in filtered_incidents.columns:
            incident_by_type = filtered_incidents['incident_type'].value_counts()
            st.metric("Most Common Incident", f"{incident_by_type.index[0]} ({incident_by_type.iloc[0]})")
        
        # Count by severity
        if 'severity' in filtered_incidents.columns:
            avg_severity = filtered_incidents['severity'].mean()
            st.metric("Average Severity", f"{avg_severity:.1f}/5")
        
        # Count incidents in EJ communities
        if 'in_environmental_justice_community' in filtered_incidents.columns:
            ej_count = filtered_incidents['in_environmental_justice_community'].sum()
            ej_pct = (ej_count / len(filtered_incidents)) * 100
            st.metric("In Environmental Justice Communities", f"{ej_pct:.1f}%")
        
        # Remediation costs
        if 'remediation_cost_millions' in filtered_incidents.columns:
            total_cost = filtered_incidents['remediation_cost_millions'].sum()
            st.metric("Total Remediation Cost", f"${total_cost:.1f}M")
    
    # Add incident breakdown
    with st.expander("Detailed Incident Analysis"):
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            if 'incident_type' in filtered_incidents.columns:
                # Show incidents by type
                incident_by_type = filtered_incidents['incident_type'].value_counts().reset_index()
                incident_by_type.columns = ['Incident Type', 'Count']
                
                fig = px.pie(
                    incident_by_type,
                    values='Count',
                    names='Incident Type',
                    title='Incidents by Type'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'severity' in filtered_incidents.columns:
                # Show incidents by severity
                incident_by_severity = filtered_incidents['severity'].value_counts().reset_index()
                incident_by_severity.columns = ['Severity', 'Count']
                incident_by_severity = incident_by_severity.sort_values('Severity')
                
                fig = px.bar(
                    incident_by_severity,
                    x='Severity',
                    y='Count',
                    title='Incidents by Severity'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Show incidents by company
        if 'company_name' in filtered_incidents.columns:
            st.subheader("Companies with Most Incidents")
            
            top_companies = filtered_incidents['company_name'].value_counts().head(10).reset_index()
            top_companies.columns = ['Company', 'Incident Count']
            
            st.dataframe(
                top_companies,
                use_container_width=True
            )
        
        # Show incidents by year if available
        if 'year' in filtered_incidents.columns:
            st.subheader("Incidents by Year")
            
            incident_by_year = filtered_incidents['year'].value_counts().reset_index()
            incident_by_year.columns = ['Year', 'Count']
            incident_by_year = incident_by_year.sort_values('Year')
            
            fig = px.line(
                incident_by_year,
                x='Year',
                y='Count',
                title='Incident Trend by Year',
                markers=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Environmental justice analysis if available
        if 'in_environmental_justice_community' in filtered_incidents.columns:
            st.subheader("Environmental Justice Analysis")
            
            # Count incidents by EJ status and severity
            if 'severity' in filtered_incidents.columns:
                ej_by_severity = filtered_incidents.groupby(['severity', 'in_environmental_justice_community']).size().reset_index()
                ej_by_severity.columns = ['Severity', 'In EJ Community', 'Count']
                
                fig = px.bar(
                    ej_by_severity,
                    x='Severity',
                    y='Count',
                    color='In EJ Community',
                    barmode='group',
                    title='Incident Severity by Environmental Justice Community Status'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Industry breakdown of EJ incidents
            if 'industry' in filtered_incidents.columns:
                industry_ej = filtered_incidents.groupby(['industry', 'in_environmental_justice_community']).size().reset_index()
                industry_ej.columns = ['Industry', 'In EJ Community', 'Count']
                
                # Filter to top industries
                top_industries = industry_ej.groupby('Industry')['Count'].sum().nlargest(5).index
                industry_ej_filtered = industry_ej[industry_ej['Industry'].isin(top_industries)]
                
                fig = px.bar(
                    industry_ej_filtered,
                    x='Industry',
                    y='Count',
                    color='In EJ Community',
                    barmode='group',
                    title='Environmental Justice Incidents by Industry (Top 5)'
                )
                
                st.plotly_chart(fig, use_container_width=True)

def display_impact_correlation_analysis(df):
    """Display impact-giving correlation analysis"""
    # Check if we have all the necessary data
    has_impact = False
    has_giving = False
    has_financials = False
    
    # Check for impact metrics
    impact_cols = []
    for col in ['environmental_impact_score', 'emissions_tons', 'waste_tons', 'water_usage_gallons',
               'energy_consumption_mwh', 'incident_count', 'Environmental Remediation Expenses',
               'Accrual for Environmental Loss Contingencies', 'env_loss_contingencies_millions', 
               'env_remediation_expenses_millions']:
        if col in df.columns:
            impact_cols.append(col)
            has_impact = True
    
    # Check for giving metrics
    giving_cols = []
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_cols.append(col)
            has_giving = True
    
    # Check for financial metrics
    financial_cols = []
    for col in ['revenue_millions', 'Revenue', 'Gross Profit', 'annual_revenue', 'Public Float']:
        if col in df.columns:
            financial_cols.append(col)
            has_financials = True
    
    # If we don't have enough data, show a message
    if not (has_impact and has_giving):
        st.info("Not enough environmental impact and giving data for correlation analysis.")
        return
    
    # Create a correlation matrix with the available metrics
    correlation_cols = impact_cols + giving_cols + financial_cols
    
    # Filter to only include rows with all metrics
    filtered_df = df[correlation_cols].dropna()
    
    if len(filtered_df) < 5:
        st.info("Not enough complete data for correlation analysis. Try with less restrictive filters.")
        return
    
    # Calculate correlation matrix
    corr_matrix = filtered_df.corr()
    
    # Create a heatmap of the correlation matrix
    fig = px.imshow(
        corr_matrix,
        text_auto='.2f',
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        title='Correlation Matrix of Environmental Metrics'
    )
    
    # Improve heatmap layout
    fig.update_layout(
        xaxis={'tickangle': 45},
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display key correlation insights
    with st.expander("Correlation Insights"):
        st.markdown("### Key Correlation Insights")
        
        # Check correlation between giving and impact
        impact_giving_correlations = []
        
        # First giving column will be our primary
        primary_giving_col = giving_cols[0]
        
        for impact_col in impact_cols:
            corr_value = corr_matrix.loc[impact_col, primary_giving_col]
            impact_giving_correlations.append((impact_col, corr_value))
        
        # Sort by absolute correlation strength
        impact_giving_correlations.sort(key=lambda x: abs(x[1]), reverse=True)
        
        for impact_col, corr_value in impact_giving_correlations:
            # Format column name for display
            display_col = impact_col.replace('_', ' ').title()
            
            # Describe correlation strength
            if abs(corr_value) > 0.7:
                strength = "very strong"
            elif abs(corr_value) > 0.5:
                strength = "strong"
            elif abs(corr_value) > 0.3:
                strength = "moderate"
            elif abs(corr_value) > 0.1:
                strength = "weak"
            else:
                strength = "very weak"
            
            # Describe correlation direction
            direction = "positive" if corr_value > 0 else "negative"
            
            st.markdown(f"• {display_col} has a **{strength} {direction} correlation** ({corr_value:.2f}) with {primary_giving_col.replace('_', ' ').title()}")
        
        # If we have financial metrics, show correlation with giving
        if has_financials:
            st.markdown("### Financial Correlations")
            
            for financial_col in financial_cols:
                corr_value = corr_matrix.loc[financial_col, primary_giving_col]
                
                # Format column name for display
                display_col = financial_col.replace('_', ' ').title()
                
                # Describe correlation strength
                if abs(corr_value) > 0.7:
                    strength = "very strong"
                elif abs(corr_value) > 0.5:
                    strength = "strong"
                elif abs(corr_value) > 0.3:
                    strength = "moderate"
                elif abs(corr_value) > 0.1:
                    strength = "weak"
                else:
                    strength = "very weak"
                
                # Describe correlation direction
                direction = "positive" if corr_value > 0 else "negative"
                
                st.markdown(f"• {display_col} has a **{strength} {direction} correlation** ({corr_value:.2f}) with {primary_giving_col.replace('_', ' ').title()}")
        
        # Overall interpretation
        st.markdown("### Interpretation")
        
        # Check if most correlations are positive
        positive_correlations = sum(1 for _, corr in impact_giving_correlations if corr > 0)
        negative_correlations = len(impact_giving_correlations) - positive_correlations
        
        if positive_correlations > negative_correlations:
            st.markdown("• Overall, companies with **higher environmental impact tend to give more**, suggesting possible compensatory philanthropy")
        else:
            st.markdown("• Overall, companies with **higher environmental impact tend to give less**, suggesting a potential disconnect between impact and philanthropy")
        
        # Check strongest correlation
        strongest_metric, strongest_corr = impact_giving_correlations[0]
        
        st.markdown(f"• The strongest relationship is between **{strongest_metric.replace('_', ' ').title()}** and giving ({strongest_corr:.2f})")
        
        # If we have both remediation expenses and contingencies
        if 'Environmental Remediation Expenses' in impact_cols and 'Accrual for Environmental Loss Contingencies' in impact_cols:
            remediation_corr = corr_matrix.loc['Environmental Remediation Expenses', primary_giving_col]
            contingencies_corr = corr_matrix.loc['Accrual for Environmental Loss Contingencies', primary_giving_col]
            
            if abs(remediation_corr) > abs(contingencies_corr):
                st.markdown(f"• Giving shows a stronger relationship with **actual cleanup expenses** ({remediation_corr:.2f}) than with **potential future liabilities** ({contingencies_corr:.2f})")
            else:
                st.markdown(f"• Giving shows a stronger relationship with **potential future liabilities** ({contingencies_corr:.2f}) than with **actual cleanup expenses** ({remediation_corr:.2f})")
        
        # Alternative metrics if we have emissions or other specific impacts
        if 'emissions_tons' in impact_cols and 'environmental_impact_score' in impact_cols:
            emissions_corr = corr_matrix.loc['emissions_tons', primary_giving_col]
            score_corr = corr_matrix.loc['environmental_impact_score', primary_giving_col]
            
            if abs(emissions_corr) > abs(score_corr):
                st.markdown(f"• Carbon emissions ({emissions_corr:.2f}) are more strongly correlated with giving than overall environmental impact scores ({score_corr:.2f})")
            else:
                st.markdown(f"• Overall environmental impact scores ({score_corr:.2f}) are more strongly correlated with giving than specific carbon emissions ({emissions_corr:.2f})")