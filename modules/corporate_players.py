"""
modules/corporate_players.py
Implements the first part of the narrative: "Who are the corporate players?"
More structured implementation based on the dashboard visualization suggestions
"""
import folium # type: ignore
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
import io
from streamlit_folium import folium_static
from datetime import datetime

# Import our visualization utilities if available
try:
    from modules.visualizations import (
        create_choropleth, create_bar_chart, create_dual_axis_chart, create_folium_map, 
        display_folium_map, display_insights_expander, create_filter_section
    )
except ImportError:
    # Define fallback functions if the module isn't available
    def create_choropleth(df, location_col, value_col, title, color_scale='Viridis', scope='usa', 
                        hover_data=None, vis_id=None):
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
            margin=dict(l=0, r=0, t=30, b=0)
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
    
    def create_dual_axis_chart(df, x_col, y1_col, y2_col, y1_title, y2_title, title='', vis_id=None):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df[x_col],
            y=df[y1_col],
            name=y1_title,
            marker_color='darkblue',
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y2_col],
            name=y2_title,
            marker_color='red',
            mode='lines+markers',
            yaxis='y2'
        ))
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

def display_corporate_players_tab(df, geo_df=None):
    """Display the Corporate Players tab visualizations"""
    st.header("Who are the corporate players?", help="This section provides an overview of the companies included in our analysis of environmental philanthropy.")
    
    # Brief introduction to this section
    st.markdown("""
    Explore the geographic distribution, industry breakdown, company sizes, and top contributors in corporate environmental philanthropy.
    """)
    
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Geographic Distribution", 
        "🏭 Industry Breakdown", 
        "📊 Company Size Analysis",
        "🥇 Top Companies"
    ])
    
    with tab1:
        # Geographic Distribution Visualization (#5)
        st.subheader("Geographic Distribution of Corporate Philanthropy")
        display_geographic_section(filtered_df, geo_df)
    
    with tab2:
        # Industry Breakdown
        st.subheader("Industry Breakdown")
        display_industry_section(filtered_df)
    
    with tab3:
        # Company Size Distribution (#2)
        st.subheader("Company Size & Environmental Giving")
        display_company_size_section(filtered_df)
    
    with tab4:
        # Top Companies (#14)
        st.subheader("Top Companies by Environmental Giving")
        display_top_companies_section(filtered_df)

def display_geographic_section(df, geo_df=None):
    """Display geographic distribution visualizations"""
    # Choose the appropriate dataframe for geographic analysis
    if geo_df is not None:
        # Use the dedicated geographic dataframe if provided
        
        # Create container with columns for visualizations
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Create a state-level choropleth map
            fig = create_choropleth(
                geo_df,
                location_col='state_abbr',
                value_col='env_giving_millions',
                title='Environmental Giving by State ($M)',
                hover_data=['num_companies', 'avg_giving_per_company', 'giving_pct_of_revenue'] 
                if 'giving_pct_of_revenue' in geo_df.columns else None
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Display top and bottom states
            st.markdown("### Top 5 States by Environmental Giving")
            
            # Sort and get top states
            top_states = geo_df.sort_values('env_giving_millions', ascending=False).head(5)
            
            # Create a formatted table
            top_states_display = pd.DataFrame({
                'State': top_states['state_name'],
                'Giving ($M)': top_states['env_giving_millions'].round(1),
                'Companies': top_states['num_companies']
            })
            
            st.dataframe(
                top_states_display,
                column_config={
                    'State': st.column_config.TextColumn('State'),
                    'Giving ($M)': st.column_config.NumberColumn('Giving ($M)', format="$%.1fM"),
                    'Companies': st.column_config.NumberColumn('Companies', format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.markdown("### Bottom 5 States by Environmental Giving")
            
            # Get bottom states (with companies > 0)
            bottom_states = geo_df[geo_df['num_companies'] > 0].sort_values('env_giving_millions').head(5)
            
            # Create a formatted table
            bottom_states_display = pd.DataFrame({
                'State': bottom_states['state_name'],
                'Giving ($M)': bottom_states['env_giving_millions'].round(1),
                'Companies': bottom_states['num_companies']
            })
            
            st.dataframe(
                bottom_states_display,
                column_config={
                    'State': st.column_config.TextColumn('State'),
                    'Giving ($M)': st.column_config.NumberColumn('Giving ($M)', format="$%.1fM"),
                    'Companies': st.column_config.NumberColumn('Companies', format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
        
        # Add regional analysis in expander
        with st.expander("Regional Analysis"):
            if 'region' in geo_df.columns:
                # Aggregate data by region
                region_data = geo_df.groupby('region').agg({
                    'env_giving_millions': 'sum',
                    'num_companies': 'sum'
                }).reset_index()
                
                # Calculate average giving per company by region
                region_data['avg_giving_per_company'] = region_data['env_giving_millions'] / region_data['num_companies']
                
                # Sort regions by giving
                region_data = region_data.sort_values('env_giving_millions', ascending=False)
                
                # Display region chart
                fig = px.bar(
                    region_data,
                    x='region',
                    y='env_giving_millions',
                    color='region',
                    text='num_companies',
                    labels={'env_giving_millions': 'Environmental Giving ($M)', 'region': 'Region'},
                    title='Environmental Giving by Region'
                )
                
                fig.update_traces(texttemplate='%{text} companies', textposition='outside')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display regional statistics
                st.markdown("### Regional Giving Statistics")
                
                # Calculate regional percentages
                total_giving = region_data['env_giving_millions'].sum()
                region_data['percentage'] = (region_data['env_giving_millions'] / total_giving) * 100
                
                # Create a formatted table
                region_display = pd.DataFrame({
                    'Region': region_data['region'],
                    'Giving ($M)': region_data['env_giving_millions'].round(1),
                    'Companies': region_data['num_companies'],
                    'Avg. per Company ($M)': region_data['avg_giving_per_company'].round(2),
                    'Percentage': region_data['percentage'].round(1)
                })
                
                st.dataframe(
                    region_display,
                    column_config={
                        'Region': st.column_config.TextColumn('Region'),
                        'Giving ($M)': st.column_config.NumberColumn('Giving ($M)', format="$%.1fM"),
                        'Companies': st.column_config.NumberColumn('Companies', format="%d"),
                        'Avg. per Company ($M)': st.column_config.NumberColumn('Avg. per Company', format="$%.2fM"),
                        'Percentage': st.column_config.NumberColumn('% of Total', format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Display insights
                west_giving = region_data[region_data['region'] == 'West']['env_giving_millions'].values[0] if 'West' in region_data['region'].values else 0
                west_companies = region_data[region_data['region'] == 'West']['num_companies'].values[0] if 'West' in region_data['region'].values else 0
                
                st.markdown("### Key Regional Insights")
                
                # Find the region with highest average giving per company
                highest_avg_region = region_data.loc[region_data['avg_giving_per_company'].idxmax()]
                
                st.markdown(f"• **{highest_avg_region['region']}** has the highest average giving per company (${highest_avg_region['avg_giving_per_company']:.2f}M)")
                st.markdown(f"• **{region_data.iloc[0]['region']}** leads in total environmental giving with ${region_data.iloc[0]['env_giving_millions']:.1f}M ({region_data.iloc[0]['percentage']:.1f}% of all giving)")
                
                if 'West' in region_data['region'].values:
                    st.markdown(f"• The **West** region has {west_companies} companies that contribute ${west_giving:.1f}M")
        
        # Add local vs. national giving analysis
        if 'local_giving_millions' in geo_df.columns and 'national_giving_millions' in geo_df.columns:
            with st.expander("Local vs. National Giving Analysis"):
                # Create a stacked bar chart showing local vs national giving by state
                top_n_states = geo_df.sort_values('env_giving_millions', ascending=False).head(10)
                
                # Prepare data for stacked bar chart
                local_national_data = pd.DataFrame({
                    'State': top_n_states['state_name'],
                    'Local Giving': top_n_states['local_giving_millions'],
                    'National/International Giving': top_n_states['national_giving_millions']
                })
                
                # Melt the dataframe for plotting
                local_national_melted = pd.melt(
                    local_national_data, 
                    id_vars=['State'], 
                    value_vars=['Local Giving', 'National/International Giving'],
                    var_name='Giving Type',
                    value_name='Amount ($M)'
                )
                
                # Create stacked bar chart
                fig = px.bar(
                    local_national_melted,
                    x='State',
                    y='Amount ($M)',
                    color='Giving Type',
                    title='Local vs. National/International Giving by Top 10 States',
                    barmode='stack'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display insights about local vs. national giving
                st.markdown("### Local vs. National Giving Insights")
                
                # Calculate overall percentages
                total_local = geo_df['local_giving_millions'].sum()
                total_national = geo_df['national_giving_millions'].sum()
                total_giving = total_local + total_national
                local_pct = (total_local / total_giving) * 100
                
                st.markdown(f"• Overall, **{local_pct:.1f}%** of corporate environmental giving stays local to the company's state")
                st.markdown(f"• **${total_local:.1f}M** goes to local environmental causes, while **${total_national:.1f}M** goes to national or international causes")
                
                # Find state with highest percentage of local giving
                top_n_states['local_pct'] = (top_n_states['local_giving_millions'] / top_n_states['env_giving_millions']) * 100
                highest_local_state = top_n_states.loc[top_n_states['local_pct'].idxmax()]
                lowest_local_state = top_n_states.loc[top_n_states['local_pct'].idxmin()]
                
                st.markdown(f"• **{highest_local_state['state_name']}** keeps the highest percentage of giving local ({highest_local_state['local_pct']:.1f}%)")
                st.markdown(f"• **{lowest_local_state['state_name']}** directs the most giving to national/international causes ({100-lowest_local_state['local_pct']:.1f}%)")
    
    elif 'latitude' in df.columns and 'longitude' in df.columns:
        # If we don't have geo_df but have coordinates, show a folium map
        
        # Get columns to display in popup
        popup_cols = ['company_name' if 'company_name' in df.columns else 'Name']
        
        # Add other useful columns if available
        for col in ['industry', 'state', 'city', 'env_giving_millions', 'size']:
            if col in df.columns:
                popup_cols.append(col)
        
        # Create a folium map with company headquarters
        m = create_folium_map(
            df,
            lat_col='latitude',
            lon_col='longitude',
            popup_cols=popup_cols,
            title='Corporate Headquarters Locations'
        )
        
        # Display the map
        st.subheader("Corporate Headquarters Locations")
        display_folium_map(m)
        
        # Add context
        st.markdown(f"""
        This map shows the locations of **{len(df)}** corporate headquarters included in our analysis. 
        The clustering of markers helps visualize geographic concentrations of corporate activity.
        """)
        
        # Add state-level statistics if state column is available
        if 'state' in df.columns:
            with st.expander("State-level Statistics"):
                # Aggregate by state
                state_counts = df['state'].value_counts().reset_index()
                state_counts.columns = ['State', 'Number of Companies']
                
                # Display top 10 states
                st.markdown("### Top 10 States by Number of Companies")
                
                st.dataframe(
                    state_counts.head(10),
                    column_config={
                        'State': st.column_config.TextColumn('State'),
                        'Number of Companies': st.column_config.NumberColumn('Companies', format="%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Create a bar chart
                fig = px.bar(
                    state_counts.head(10),
                    x='State',
                    y='Number of Companies',
                    title='Top 10 States by Number of Companies',
                    color='Number of Companies'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        # If we don't have geographic data, show a message
        st.info("Geographic data (state, latitude, longitude) not available in the dataset.")

def display_industry_section(df):
    """Display industry breakdown visualizations"""
    # Determine industry column
    industry_col = None
    for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
        if col in df.columns:
            industry_col = col
            break
    
    if industry_col is None:
        st.info("Industry information not found in the dataset.")
        return
    
    # Determine giving column
    giving_col = None
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_col = col
            break
    
    if giving_col is None:
        st.info("Environmental giving information not found in the dataset.")
        return
    
    # Create container with columns for visualizations
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Aggregate data by industry
        industry_data = df.groupby(industry_col).agg({
            'company_id' if 'company_id' in df.columns else df.index.name if df.index.name else 'Name' if 'Name' in df.columns else giving_col: 'count',
            giving_col: 'sum'
        }).reset_index()
        
        # Rename columns for consistency
        industry_data.columns = [industry_col, 'num_companies', 'total_giving']
        
        # Sort by giving amount and get top industries
        industry_data = industry_data.sort_values('total_giving', ascending=False)
        top_industries = industry_data.head(10).copy()
        
        # Create horizontal bar chart
        fig = px.bar(
            top_industries,
            y=industry_col,
            x='total_giving',
            color='total_giving',
            color_continuous_scale='Viridis',
            orientation='h',
            text='num_companies',
            labels={
                'total_giving': 'Environmental Giving' if 'env' in giving_col else 'Charitable Contributions',
                industry_col: industry_col.replace('_', ' ').title()
            },
            title=f"Top 10 Industries by {giving_col.replace('_', ' ').title()}"
        )
        
        # Improve text display
        fig.update_traces(
            texttemplate='%{text} companies',
            textposition='outside'
        )
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Calculate industry percentages
        total_giving = industry_data['total_giving'].sum()
        industry_data['percentage'] = (industry_data['total_giving'] / total_giving) * 100
        
        # Create a pie chart for top industries
        top_n = 6  # Top N industries plus "Other"
        
        # Prepare data for pie chart
        if len(industry_data) > top_n:
            pie_data = industry_data.head(top_n).copy()
            other_sum = industry_data.iloc[top_n:]['total_giving'].sum()
            other_count = industry_data.iloc[top_n:]['num_companies'].sum()
            other_row = pd.DataFrame({
                industry_col: ['Other Industries'],
                'num_companies': [other_count],
                'total_giving': [other_sum],
                'percentage': [(other_sum / total_giving) * 100]
            })
            pie_data = pd.concat([pie_data, other_row], ignore_index=True)
        else:
            pie_data = industry_data.copy()
        
        # Create pie chart
        fig = px.pie(
            pie_data,
            values='total_giving',
            names=industry_col,
            title=f"Industry Distribution of Environmental Giving",
            hover_data=['num_companies', 'percentage']
        )
        
        # Customize hover info
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Giving: $%{value:.1f}M<br>Companies: %{customdata[0]}<br>Percentage: %{customdata[1]:.1f}%'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    # Add detailed industry analysis in expander
    with st.expander("Detailed Industry Analysis"):
        # Calculate per-company metrics
        industry_data['giving_per_company'] = industry_data['total_giving'] / industry_data['num_companies']
        
        # Display sortable table
        st.markdown("### Complete Industry Metrics")
        
        # Allow choosing sort column
        sort_col = st.radio("Sort by:", ["Total Giving", "Number of Companies", "Giving per Company"], horizontal=True)
        sort_by = 'total_giving' if sort_col == "Total Giving" else 'num_companies' if sort_col == "Number of Companies" else 'giving_per_company'
        
        # Sort the dataframe
        display_df = industry_data.sort_values(sort_by, ascending=False).copy()
        
        # Format columns for display
        if 'num_companies' in display_df.columns:
            st.dataframe(
                display_df,
                column_config={
                    industry_col: industry_col.replace('_', ' ').title(),
                    'num_companies': st.column_config.NumberColumn('Number of Companies', format="%d"),
                    'total_giving': st.column_config.NumberColumn(
                        'Total Giving' if 'env' not in giving_col else 'Environmental Giving',
                        format="$%.2f M" if 'millions' in giving_col else "$%.2f"
                    ),
                    'giving_per_company': st.column_config.NumberColumn('Giving per Company', format="$%.2f M"),
                    'percentage': st.column_config.NumberColumn('% of Total', format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )
        
        # Add industry insights
        st.markdown("### Key Industry Insights")
        
        # Calculate industry metrics
        total_industries = len(industry_data)
        top_3_share = (industry_data.head(3)['total_giving'].sum() / total_giving) * 100
        
        st.markdown(f"• Total industries represented: **{total_industries}**")
        st.markdown(f"• Top 3 industries account for **{top_3_share:.1f}%** of all environmental giving")
        
        # Find highest giving per company
        highest_per_company = industry_data.loc[industry_data['giving_per_company'].idxmax()]
        st.markdown(f"• **{highest_per_company[industry_col]}** has the highest giving per company (${highest_per_company['giving_per_company']:.2f}M)")
        
        # Find highest total giving
        highest_total = industry_data.iloc[0]
        st.markdown(f"• **{highest_total[industry_col]}** leads in total giving with ${highest_total['total_giving']:.1f}M ({highest_total['percentage']:.1f}% of total)")
        
        # Compare high-impact vs. low-impact industries if impact data is available
        if 'environmental_impact_score' in df.columns:
            # Get average impact score by industry
            impact_by_industry = df.groupby(industry_col)['environmental_impact_score'].mean().reset_index()
            
            # Identify high and low impact industries
            high_impact = impact_by_industry.nlargest(3, 'environmental_impact_score')
            low_impact = impact_by_industry.nsmallest(3, 'environmental_impact_score')
            
            # Merge with giving data
            high_impact = pd.merge(high_impact, industry_data[[industry_col, 'total_giving', 'giving_per_company']], on=industry_col)
            low_impact = pd.merge(low_impact, industry_data[[industry_col, 'total_giving', 'giving_per_company']], on=industry_col)
            
            st.markdown("### Impact vs. Giving by Industry")
            st.markdown(f"• High-impact industries (e.g., **{', '.join(high_impact[industry_col].iloc[:2])}**) give an average of ${high_impact['giving_per_company'].mean():.2f}M per company")
            st.markdown(f"• Low-impact industries (e.g., **{', '.join(low_impact[industry_col].iloc[:2])}**) give an average of ${low_impact['giving_per_company'].mean():.2f}M per company")

def display_company_size_section(df):
    """Display company size distribution visualizations"""
    # Determine size column
    size_col = None
    for col in ['size', 'Size', 'company_size', 'CompanySize']:
        if col in df.columns:
            size_col = col
            break
    
    # If no explicit size column, try to create one based on revenue
    if size_col is None:
        revenue_col = None
        for col in ['revenue_millions', 'Revenue', 'annual_revenue', 'Gross Profit']:
            if col in df.columns:
                revenue_col = col
                break
        
        if revenue_col is not None:
            # Create size categories based on revenue
            df['size_category'] = pd.cut(
                df[revenue_col],
                bins=[0, 100, 1000, 10000, float('inf')],
                labels=['Small ($10M-$100M)', 'Medium ($100M-$1B)', 'Large ($1B-$10B)', 'Very Large (>$10B)']
            )
            size_col = 'size_category'
        else:
            st.info("Company size or revenue information not found in the dataset.")
            return
    
    # Determine giving column
    giving_col = None
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_col = col
            break
    
    if giving_col is None:
        st.info("Environmental giving information not found in the dataset.")
        return
    
    # Create container with columns for visualizations
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Aggregate data by size
        size_data = df.groupby(size_col).agg({
            'company_id' if 'company_id' in df.columns else df.index.name if df.index.name else 'Name' if 'Name' in df.columns else giving_col: 'count',
            giving_col: 'sum'
        }).reset_index()
        
        # Rename columns for consistency
        size_data.columns = [size_col, 'num_companies', 'total_giving']
        
        # Calculate giving per company
        size_data['giving_per_company'] = size_data['total_giving'] / size_data['num_companies']
        
        # Create dual-axis chart showing both company count and giving per company
        fig = go.Figure()
        
        # Add bars for company count
        fig.add_trace(go.Bar(
            x=size_data[size_col],
            y=size_data['num_companies'],
            name='Number of Companies',
            marker_color='darkblue',
            yaxis='y'
        ))
        
        # Add line for giving per company
        fig.add_trace(go.Scatter(
            x=size_data[size_col],
            y=size_data['giving_per_company'],
            name='Giving per Company ($M)',
            marker_color='red',
            mode='lines+markers',
            yaxis='y2'
        ))
        
        # Update layout
        fig.update_layout(
            title='Company Size Distribution and Giving per Company',
            yaxis=dict(title='Number of Companies'),
            yaxis2=dict(
                title='Giving per Company ($M)',
                overlaying='y',
                side='right'
            ),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis=dict(type='category')
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Calculate percentage of total giving by size
        total_giving = size_data['total_giving'].sum()
        size_data['percentage'] = (size_data['total_giving'] / total_giving) * 100
        
        # Create pie chart for giving by size
        fig = px.pie(
            size_data,
            values='total_giving',
            names=size_col,
            title=f"Distribution of Environmental Giving by Company Size",
            hover_data=['num_companies', 'percentage', 'giving_per_company']
        )
        
        # Customize hover info
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Giving: $%{value:.1f}M<br>Companies: %{customdata[0]}<br>Percentage: %{customdata[1]:.1f}%<br>Per Company: $%{customdata[2]:.2f}M'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    # Add detailed size analysis in expander
    with st.expander("Size Analysis Details"):
        # Display normalized giving table
        st.markdown("### Normalized Giving by Company Size")
        
        # Format the dataframe for display
        st.dataframe(
            size_data,
            column_config={
                size_col: "Company Size",
                'num_companies': st.column_config.NumberColumn('Number of Companies', format="%d"),
                'total_giving': st.column_config.NumberColumn('Total Giving ($M)', format="$%.2f M"),
                'giving_per_company': st.column_config.NumberColumn('Avg. Giving per Company ($M)', format="$%.2f M"),
                'percentage': st.column_config.NumberColumn('% of Total Giving', format="%.1f%%")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Check if we have percentage of revenue data
        pct_col = None
        for col in ['env_giving_pct', 'giving_percentage', 'giving_pct_of_revenue']:
            if col in df.columns:
                pct_col = col
                break
        
        if pct_col:
            # Calculate average giving percentage by size
            pct_by_size = df.groupby(size_col)[pct_col].mean().reset_index()
            
            # Create bar chart for giving percentage by size
            fig = px.bar(
                pct_by_size,
                x=size_col,
                y=pct_col,
                title='Environmental Giving as % of Revenue by Company Size',
                labels={pct_col: 'Giving as % of Revenue', size_col: 'Company Size'},
                color=pct_col
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Find size with highest percentage
            highest_pct_size = pct_by_size.loc[pct_by_size[pct_col].idxmax()]
            
            st.markdown("### Key Size Insights")
            st.markdown(f"• **{highest_pct_size[size_col]}** companies give the highest percentage of revenue ({highest_pct_size[pct_col]:.2f}%)")
            
            # Identify relationship pattern
            if pct_by_size[pct_col].iloc[0] > pct_by_size[pct_col].iloc[-1]:
                st.markdown("• Smaller companies give a **higher percentage** of their revenue compared to larger companies")
            else:
                st.markdown("• Larger companies give a **higher percentage** of their revenue compared to smaller companies")
        
        # Add size distribution insights
        st.markdown("### Size Distribution Insights")
        
        # Find dominant size category
        dominant_size = size_data.loc[size_data['num_companies'].idxmax()]
        dominant_giving = size_data.loc[size_data['total_giving'].idxmax()]
        dominant_per_company = size_data.loc[size_data['giving_per_company'].idxmax()]
        
        st.markdown(f"• **{dominant_size[size_col]}** is the most common company size category ({dominant_size['num_companies']} companies, {dominant_size['num_companies']/size_data['num_companies'].sum()*100:.1f}% of total)")
        st.markdown(f"• **{dominant_giving[size_col]}** companies contribute the most in total giving (${dominant_giving['total_giving']:.1f}M, {dominant_giving['percentage']:.1f}% of total)")
        st.markdown(f"• **{dominant_per_company[size_col]}** companies have the highest average giving per company (${dominant_per_company['giving_per_company']:.2f}M)")

def display_top_companies_section(df):
    """Display top companies visualizations"""
    # Determine company name column
    name_col = None
    for col in ['company_name', 'Name', 'CompanyName']:
        if col in df.columns:
            name_col = col
            break
    
    if name_col is None:
        st.info("Company name information not found in the dataset.")
        return
    
    # Determine giving column
    giving_col = None
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_col = col
            break
    
    if giving_col is None:
        st.info("Environmental giving information not found in the dataset.")
        return
    
    # Create toggle for absolute vs. normalized ranking
    ranking_type = st.radio(
        "Ranking Method:",
        ["Absolute Giving", "Giving as % of Revenue"],
        horizontal=True
    )
    
    # Gather additional columns for the table if they exist
    additional_cols = []
    column_mapping = {}
    
    for col_pair in [
        ('industry', 'Industry'), 
        ('Standard Industrial Classification (SIC)', 'Industry'),
        ('state', 'State'),
        ('State', 'State'),
        ('size', 'Size'),
        ('size_category', 'Size'),
        ('revenue_millions', 'Annual Revenue'),
        ('Revenue', 'Annual Revenue'),
        ('Gross Profit', 'Annual Revenue'),
        ('env_giving_pct', 'Giving % of Revenue'),
        ('giving_pct', 'Giving % of Revenue'),
        ('giving_pct_of_revenue', 'Giving % of Revenue')
    ]:
        if col_pair[0] in df.columns and col_pair[0] not in [name_col, giving_col]:
            additional_cols.append(col_pair[0])
            column_mapping[col_pair[0]] = col_pair[1]
    
    # Create container for top companies
    if ranking_type == "Absolute Giving":
        # Sort by total giving
        top_companies = df.sort_values(giving_col, ascending=False).head(15).copy()
        
        # Display header
        st.subheader(f"Top 15 Companies by Total Environmental Giving")
    else:
        # Check if we have percentage data
        pct_col = None
        for col_option in ['env_giving_pct', 'giving_percentage', 'giving_pct_of_revenue', 'giving_pct']:
            if col_option in df.columns:
                pct_col = col_option
                break
        
        if pct_col is None:
            st.warning("Giving as percentage of revenue data not available.")
            # Fall back to absolute giving
            top_companies = df.sort_values(giving_col, ascending=False).head(15).copy()
            st.subheader(f"Top 15 Companies by Total Environmental Giving")
        else:
            # Sort by percentage
            top_companies = df.sort_values(pct_col, ascending=False).head(15).copy()
            st.subheader(f"Top 15 Companies by Giving as % of Revenue")
    
    # Select columns for display
    display_columns = [name_col] + additional_cols + [giving_col]
    if ranking_type == "Giving as % of Revenue" and pct_col is not None:
        display_columns.append(pct_col)
    
    # Create a visualization
    if 'industry' in top_companies.columns:
        # Color by industry
        fig = px.bar(
            top_companies,
            x=giving_col,
            y=name_col,
            color='industry',
            orientation='h',
            title=f"Top Companies by {'Total Giving' if ranking_type == 'Absolute Giving' else 'Giving as % of Revenue'}"
        )
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Simple bar chart without industry coloring
        fig = px.bar(
            top_companies,
            x=giving_col,
            y=name_col,
            orientation='h',
            title=f"Top Companies by {'Total Giving' if ranking_type == 'Absolute Giving' else 'Giving as % of Revenue'}"
        )
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Create a copy of the dataframe with just the columns we want
    display_df = top_companies[display_columns].copy()
    
    # Rename columns for display
    display_df = display_df.rename(columns={
        name_col: 'Company',
        giving_col: 'Environmental Giving' if 'env' in giving_col else 'Charitable Contributions',
        **column_mapping
    })
    
    # Create column configuration for formatting
    column_config = {
        'Company': st.column_config.TextColumn('Company')
    }
    
    # Add configurations for additional columns
    for orig_col, display_col in column_mapping.items():
        if 'revenue' in orig_col.lower() or 'profit' in orig_col.lower():
            column_config[display_col] = st.column_config.NumberColumn(
                display_col, 
                format="$%.1f M" if 'millions' in orig_col.lower() else "$%.0f"
            )
        elif 'pct' in orig_col.lower() or '%' in orig_col.lower():
            column_config[display_col] = st.column_config.NumberColumn(display_col, format="%.2f%%")
        else:
            column_config[display_col] = st.column_config.TextColumn(display_col)
    
    # Add configuration for giving column
    column_config['Environmental Giving' if 'env' in giving_col else 'Charitable Contributions'] = \
        st.column_config.NumberColumn(
            'Environmental Giving' if 'env' in giving_col else 'Charitable Contributions',
            format="$%.2f M" if 'millions' in giving_col.lower() else "$%.2f"
        )
    
    # Add configuration for percentage column if present
    if ranking_type == "Giving as % of Revenue" and pct_col is not None:
        display_df = display_df.rename(columns={pct_col: 'Giving % of Revenue'})
        column_config['Giving % of Revenue'] = st.column_config.NumberColumn('Giving % of Revenue', format="%.2f%%")
    
    # Display the table
    st.dataframe(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )
    
    # Add company profile preview functionality
    with st.expander("Company Profile Preview"):
        # Let the user select a company to view
        selected_company = st.selectbox(
            "Select a company to view detailed profile:",
            options=top_companies[name_col].tolist()
        )
        
        if selected_company:
            # Get the selected company data
            company_data = df[df[name_col] == selected_company].iloc[0]
            
            # Display company profile
            st.markdown(f"### {company_data[name_col]} Profile")
            
            # Create two columns for profile layout
            profile_col1, profile_col2 = st.columns(2)
            
            with profile_col1:
                # Basic information
                st.markdown("#### Basic Information")
                
                # Display key metrics like industry, location, size
                for col, display_name in [
                    ('industry', 'Industry'),
                    ('Standard Industrial Classification (SIC)', 'Industry'),
                    ('state', 'State'),
                    ('State', 'State'),
                    ('size', 'Company Size'),
                    ('size_category', 'Company Size')
                ]:
                    if col in company_data.index and pd.notna(company_data[col]):
                        st.markdown(f"**{display_name}:** {company_data[col]}")
                
                # Display address if available
                address_cols = [col for col in ['address', 'Address', 'city', 'City', 'state', 'State', 'zip_code', 'ZipCode', 'Zip'] if col in company_data.index]
                if address_cols:
                    st.markdown("#### Address")
                    address_str = ", ".join(str(company_data[col]) for col in address_cols if pd.notna(company_data[col]))
                    st.markdown(address_str)
            
            with profile_col2:
                # Financial information
                st.markdown("#### Financial Information")
                
                for col, display_name, fmt in [
                    ('revenue_millions', 'Annual Revenue', '${:,.1f}M'),
                    ('Revenue', 'Annual Revenue', '${:,.0f}'),
                    ('Gross Profit', 'Gross Profit', '${:,.0f}'),
                    ('env_giving_millions', 'Environmental Giving', '${:,.2f}M'),
                    ('Charitable Contributions', 'Charitable Contributions', '${:,.2f}'),
                    ('env_giving_pct', 'Giving as % of Revenue', '{:.2f}%'),
                    ('giving_pct_of_revenue', 'Giving as % of Revenue', '{:.2f}%'),
                    ('giving_pct', 'Giving as % of Revenue', '{:.2f}%')
                ]:
                    if col in company_data.index and pd.notna(company_data[col]):
                        try:
                            formatted_value = fmt.format(company_data[col])
                            st.markdown(f"**{display_name}:** {formatted_value}")
                        except:
                            st.markdown(f"**{display_name}:** {company_data[col]}")
                
                # ESG score if available
                if 'esg_score' in company_data.index and pd.notna(company_data['esg_score']):
                    st.markdown(f"**ESG Score:** {company_data['esg_score']:.1f}/100")
            
            # Display environmental metrics if available
            if 'environmental_impact_score' in company_data.index or 'emissions_tons' in company_data.index:
                st.markdown("#### Environmental Metrics")
                
                metrics_col1, metrics_col2 = st.columns(2)
                
                with metrics_col1:
                    for col, display_name, fmt in [
                        ('environmental_impact_score', 'Environmental Impact Score', '{:.1f}/100'),
                        ('emissions_tons', 'CO₂ Emissions', '{:,.0f} tons'),
                        ('waste_tons', 'Waste Generated', '{:,.0f} tons')
                    ]:
                        if col in company_data.index and pd.notna(company_data[col]):
                            try:
                                formatted_value = fmt.format(company_data[col])
                                st.markdown(f"**{display_name}:** {formatted_value}")
                            except:
                                st.markdown(f"**{display_name}:** {company_data[col]}")
                
                with metrics_col2:
                    for col, display_name, fmt in [
                        ('water_usage_gallons', 'Water Usage', '{:,.0f} gallons'),
                        ('energy_consumption_mwh', 'Energy Consumption', '{:,.0f} MWh'),
                        ('incident_count', 'Environmental Incidents', '{:,.0f}')
                    ]:
                        if col in company_data.index and pd.notna(company_data[col]):
                            try:
                                formatted_value = fmt.format(company_data[col])
                                st.markdown(f"**{display_name}:** {formatted_value}")
                            except:
                                st.markdown(f"**{display_name}:** {company_data[col]}")
        
                