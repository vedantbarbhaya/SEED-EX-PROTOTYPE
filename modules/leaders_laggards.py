"""
modules/leaders_laggards.py
Implements the fourth part of the narrative: "Who's leading and who's lagging?"
More structured implementation based on the dashboard visualization suggestions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import our visualization utilities if available
try:
    from modules.visualizations import (
        create_scatter_plot, create_bar_chart, create_dual_axis_chart, 
        display_insights_expander, create_filter_section
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
        if text_col:
            fig.update_traces(textposition='outside')
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

def display_leaders_laggards_tab(df):
    """Display the Leaders & Laggards tab visualizations"""
    st.header("Who's leading and who's lagging?", help="This section identifies environmental philanthropy leaders and laggards.")
    
    # Brief introduction to this section
    st.markdown("""
    This section identifies which companies and industries are leading the way in environmental philanthropy and which are falling behind.
    Explore the relationship between ESG scores, giving, and transparency.
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
    tab1, tab2, tab3 = st.tabs([
        "🏆 Leaders vs. Laggards", 
        "📊 Industry Benchmarking", 
        "🔍 ESG Analysis"
    ])
    
    with tab1:
        # Leaders vs. Laggards Analysis
        st.subheader("Leaders vs. Laggards Analysis")
        display_leaders_laggards_section(filtered_df)
    
    with tab2:
        # Industry Benchmarking (#4)
        st.subheader("Industry Benchmarking")
        display_industry_benchmarking_section(filtered_df)
    
    with tab3:
        # ESG Analysis (#9)
        st.subheader("ESG Score Analysis")
        display_esg_analysis_section(filtered_df)

def display_leaders_laggards_section(df):
    """Display leaders vs. laggards analysis"""
    # Check if we have necessary columns
    required_cols = []
    
    # Get company name column
    name_col = None
    for col in ['company_name', 'Name', 'CompanyName']:
        if col in df.columns:
            name_col = col
            required_cols.append(col)
            break
    
    # Get environmental giving column
    giving_col = None
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_col = col
            required_cols.append(col)
            break
    
    # Get transparency column
    transparency_col = None
    for col in ['transparency_score', 'reporting_level', 'Detail']:
        if col in df.columns:
            transparency_col = col
            required_cols.append(col)
            break
    
    # Check if we have all required columns
    if len(required_cols) < 3:
        missing = []
        if not name_col:
            missing.append("company name")
        if not giving_col:
            missing.append("environmental giving")
        if not transparency_col:
            missing.append("transparency score")
        
        st.info(f"Missing required data: {', '.join(missing)}. Some visualizations may not be available.")
    
    # Create scoring system for ranking companies
    if name_col and giving_col:
        # Start with a base score
        df['leader_score'] = 50.0  # Base score of 50
        
       # Factor 1: Environmental Giving (normalized by company size if possible)
        if 'revenue_millions' in df.columns and giving_col in df.columns:
            # Calculate giving as percentage of revenue
            df['giving_pct'] = (df[giving_col] / df['revenue_millions']) * 100
            
            # Award points based on percentile rank of giving percentage
            df['giving_score'] = df['giving_pct'].rank(pct=True) * 40  # Up to 40 points from giving
            df['leader_score'] += df['giving_score']
        elif giving_col in df.columns:
            # If no revenue data, just use absolute giving
            df['giving_score'] = df[giving_col].rank(pct=True) * 40  # Up to 40 points from giving
            df['leader_score'] += df['giving_score']
        
        # Factor 2: Transparency
        if transparency_col in df.columns:
            if transparency_col == 'transparency_score':
                # Direct transparency score (assumed 0-100)
                df['transparency_score_norm'] = df[transparency_col] * 0.3  # Up to 30 points from transparency
            elif transparency_col == 'Detail':
                # Binary detail level (0 or 1)
                df['transparency_score_norm'] = df[transparency_col] * 30  # 30 points if detailed, 0 if not
            elif transparency_col == 'reporting_level':
                # Categorical reporting level
                level_scores = {
                    'Minimal': 6,
                    'Basic': 12,
                    'Standard': 18,
                    'Detailed': 24,
                    'Comprehensive': 30
                }
                df['transparency_score_norm'] = df[transparency_col].map(lambda x: level_scores.get(x, 0))
            
            df['leader_score'] += df['transparency_score_norm']
        
        # Factor 3: Environmental Impact (if available, impact should lower the score)
        if 'environmental_impact_score' in df.columns:
            # Reverse the impact score (higher impact = lower points)
            df['impact_score_norm'] = (1 - df['environmental_impact_score'].rank(pct=True)) * 20  # Up to 20 points for low impact
            df['leader_score'] += df['impact_score_norm']
        
        # Factor 4: Incident count (if available, incidents should lower the score)
        if 'incident_count' in df.columns:
            # Reverse the incident count (more incidents = lower points)
            df['incident_score_norm'] = (1 - df['incident_count'].rank(pct=True)) * 10  # Up to 10 points for low incidents
            df['leader_score'] += df['incident_score_norm']
        
        # Create leader/laggard designation
        df['performance_category'] = pd.cut(
            df['leader_score'],
            bins=[0, 40, 60, 80, float('inf')],
            labels=['Laggard', 'Below Average', 'Above Average', 'Leader']
        )
        
        # Sort by leader score
        ranked_df = df.sort_values('leader_score', ascending=False).copy()
        
        # Identify leaders and laggards
        leaders = ranked_df.head(10).copy()
        laggards = ranked_df.tail(10).copy()
        
        # Display leaders and laggards in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Top 10 Environmental Leaders")
            
            # Create a formatted table for leaders
            leaders_display = pd.DataFrame({
                'Company': leaders[name_col],
                'Score': leaders['leader_score'],
                'Category': leaders['performance_category']
            })
            
            # Add industry if available
            if 'industry' in leaders.columns:
                leaders_display['Industry'] = leaders['industry']
            
            # Format the dataframe for display
            st.dataframe(
                leaders_display,
                column_config={
                    'Company': st.column_config.TextColumn('Company'),
                    'Score': st.column_config.NumberColumn('Leadership Score', format="%.1f"),
                    'Category': st.column_config.TextColumn('Category'),
                    'Industry': st.column_config.TextColumn('Industry') if 'Industry' in leaders_display.columns else None
                },
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.markdown("### Bottom 10 Environmental Laggards")
            
            # Create a formatted table for laggards
            laggards_display = pd.DataFrame({
                'Company': laggards[name_col],
                'Score': laggards['leader_score'],
                'Category': laggards['performance_category']
            })
            
            # Add industry if available
            if 'industry' in laggards.columns:
                laggards_display['Industry'] = laggards['industry']
            
            # Format the dataframe for display
            st.dataframe(
                laggards_display,
                column_config={
                    'Company': st.column_config.TextColumn('Company'),
                    'Score': st.column_config.NumberColumn('Leadership Score', format="%.1f"),
                    'Category': st.column_config.TextColumn('Category'),
                    'Industry': st.column_config.TextColumn('Industry') if 'Industry' in laggards_display.columns else None
                },
                hide_index=True,
                use_container_width=True
            )
        
        # Create a distribution chart of leader scores
        st.markdown("### Distribution of Leadership Scores")
        
        # Create histogram with category coloring
        fig = px.histogram(
            df,
            x='leader_score',
            color='performance_category',
            nbins=50,
            title='Distribution of Leadership Scores',
            category_orders={'performance_category': ['Laggard', 'Below Average', 'Above Average', 'Leader']}
        )
        
        # Add vertical lines for category boundaries
        for boundary in [40, 60, 80]:
            fig.add_vline(x=boundary, line_dash="dash", line_color="gray")
        
        # Update layout
        fig.update_layout(
            xaxis_title='Leadership Score',
            yaxis_title='Number of Companies',
            legend_title='Performance Category'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display score breakdown
        with st.expander("Leadership Score Breakdown"):
            st.markdown("""
            ### How Leadership Scores Are Calculated
            
            The leadership score (0-100) is calculated based on multiple factors:
            
            - **Base Score**: Every company starts with 50 points
            - **Environmental Giving**: Up to 40 points based on giving relative to company size
            - **Transparency**: Up to 30 points based on reporting quality
            - **Environmental Impact**: Up to 20 points for low environmental impact (if data available)
            - **Environmental Incidents**: Up to 10 points for few/no incidents (if data available)
            
            Categories are assigned as follows:
            - **Leader**: 80-100 points
            - **Above Average**: 60-80 points
            - **Below Average**: 40-60 points
            - **Laggard**: 0-40 points
            """)
            
            # Create a scatter plot showing giving vs. transparency with leadership score as color
            if giving_col and transparency_col:
                st.markdown("### Relationship Between Components and Overall Score")
                
                # Scatter plot of giving vs. transparency
                x_col = 'giving_score' if 'giving_score' in df.columns else giving_col
                y_col = 'transparency_score_norm' if 'transparency_score_norm' in df.columns else transparency_col
                
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color='leader_score',
                    hover_name=name_col,
                    title='Giving vs. Transparency',
                    color_continuous_scale='viridis'
                )
                
                # Update axis labels
                fig.update_layout(
                    xaxis_title='Giving Score',
                    yaxis_title='Transparency Score'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a bar chart showing the average scores by performance category
                category_avg = df.groupby('performance_category')[
                    ['giving_score', 'transparency_score_norm', 'impact_score_norm' if 'impact_score_norm' in df.columns else 'leader_score']
                ].mean().reset_index()
                
                # Melt for stacked bar chart
                category_avg_melted = pd.melt(
                    category_avg,
                    id_vars=['performance_category'],
                    value_vars=[
                        'giving_score', 
                        'transparency_score_norm', 
                        'impact_score_norm' if 'impact_score_norm' in df.columns else 'leader_score'
                    ],
                    var_name='Score Component',
                    value_name='Average Score'
                )
                
                # Map column names to display names
                component_names = {
                    'giving_score': 'Giving Score',
                    'transparency_score_norm': 'Transparency Score',
                    'impact_score_norm': 'Environmental Impact Score',
                    'leader_score': 'Overall Score'
                }
                
                category_avg_melted['Score Component'] = category_avg_melted['Score Component'].map(lambda x: component_names.get(x, x))
                
                # Create stacked bar chart
                fig = px.bar(
                    category_avg_melted,
                    x='performance_category',
                    y='Average Score',
                    color='Score Component',
                    title='Average Score Components by Performance Category',
                    barmode='group',
                    category_orders={'performance_category': ['Laggard', 'Below Average', 'Above Average', 'Leader']}
                )
                
                st.plotly_chart(fig, use_container_width=True)

def display_industry_benchmarking_section(df):
    """Display industry benchmarking visualizations"""
    # Check if we have industry column
    industry_col = None
    for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
        if col in df.columns:
            industry_col = col
            break
    
    if industry_col is None:
        st.info("Industry information not found in the dataset.")
        return
    
    # Get giving column
    giving_col = None
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_col = col
            break
    
    if giving_col is None:
        st.info("Environmental giving information not found in the dataset.")
        return
    
    # Create giving percentage column if possible
    if 'revenue_millions' in df.columns:
        df['giving_pct'] = (df[giving_col] / df['revenue_millions']) * 100
    
    # Group by industry
    industry_metrics = df.groupby(industry_col).agg({
        giving_col: ['mean', 'median', 'std', 'count'],
        'giving_pct': ['mean', 'median', 'std'] if 'giving_pct' in df.columns else ['mean'],
        'transparency_score': ['mean', 'median'] if 'transparency_score' in df.columns else ['mean'],
        'leader_score': ['mean', 'median'] if 'leader_score' in df.columns else ['mean']
    }).reset_index()
    
    # Flatten multi-level columns
    industry_metrics.columns = [
        f"{col[0]}_{col[1]}" if col[1] != '' else col[0] 
        for col in industry_metrics.columns
    ]
    
    # Rename for clarity
    rename_dict = {}
    for col in industry_metrics.columns:
        if col == industry_col:
            continue
        
        if giving_col in col:
            if 'mean' in col:
                rename_dict[col] = 'avg_giving'
            elif 'median' in col:
                rename_dict[col] = 'median_giving'
            elif 'std' in col:
                rename_dict[col] = 'std_giving'
            elif 'count' in col:
                rename_dict[col] = 'company_count'
        
        if 'giving_pct' in col:
            if 'mean' in col:
                rename_dict[col] = 'avg_giving_pct'
            elif 'median' in col:
                rename_dict[col] = 'median_giving_pct'
        
        if 'transparency' in col:
            if 'mean' in col:
                rename_dict[col] = 'avg_transparency'
            elif 'median' in col:
                rename_dict[col] = 'median_transparency'
        
        if 'leader_score' in col:
            if 'mean' in col:
                rename_dict[col] = 'avg_leader_score'
            elif 'median' in col:
                rename_dict[col] = 'median_leader_score'
    
    industry_metrics = industry_metrics.rename(columns=rename_dict)
    
    # Allow user to choose metric for comparison
    st.markdown("### Industry Benchmarking")
    
    comparison_options = [
        ('Average Giving', 'avg_giving'),
        ('Median Giving', 'median_giving') if 'median_giving' in industry_metrics.columns else None,
        ('Average Giving % of Revenue', 'avg_giving_pct') if 'avg_giving_pct' in industry_metrics.columns else None,
        ('Average Transparency Score', 'avg_transparency') if 'avg_transparency' in industry_metrics.columns else None,
        ('Average Leadership Score', 'avg_leader_score') if 'avg_leader_score' in industry_metrics.columns else None
    ]
    
    # Filter out None values
    comparison_options = [option for option in comparison_options if option is not None]
    
    selected_metric = st.selectbox(
        "Select metric for comparison:",
        options=[option[0] for option in comparison_options],
        index=0
    )
    
    # Get the column name for the selected metric
    selected_col = next(option[1] for option in comparison_options if option[0] == selected_metric)
    
    # Sort by the selected metric
    sorted_industries = industry_metrics.sort_values(selected_col, ascending=False)
    
    # Show top and bottom industries
    col1, col2 = st.columns(2)
    
    with col1:
        # Top industries chart
        fig = create_bar_chart(
            sorted_industries.head(10),
            x_col=selected_col,
            y_col=industry_col,
            orientation='h',
            title=f'Top 10 Industries by {selected_metric}',
            text_col='company_count' if 'company_count' in sorted_industries.columns else None
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Bottom industries chart
        fig = create_bar_chart(
            sorted_industries.tail(10).sort_values(selected_col),
            x_col=selected_col,
            y_col=industry_col,
            orientation='h',
            title=f'Bottom 10 Industries by {selected_metric}',
            text_col='company_count' if 'company_count' in sorted_industries.columns else None
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display industry benchmark data table
    with st.expander("Complete Industry Benchmark Data"):
        # Calculate overall averages
        overall_avg = {
            'avg_giving': df[giving_col].mean(),
            'median_giving': df[giving_col].median() if 'median_giving' in industry_metrics.columns else None,
            'avg_giving_pct': df['giving_pct'].mean() if 'giving_pct' in df.columns else None,
            'avg_transparency': df['transparency_score'].mean() if 'transparency_score' in df.columns else None,
            'avg_leader_score': df['leader_score'].mean() if 'leader_score' in df.columns else None
        }
        
        # Add comparison to overall average
        for metric, avg in overall_avg.items():
            if avg is not None and metric in industry_metrics.columns:
                industry_metrics[f'{metric}_vs_avg'] = ((industry_metrics[metric] / avg) - 1) * 100
        
        # Sort by selected metric
        display_df = industry_metrics.sort_values(selected_col, ascending=False)
        
        # Create column configuration
        column_config = {
            industry_col: st.column_config.TextColumn("Industry")
        }
        
        if 'company_count' in display_df.columns:
            column_config['company_count'] = st.column_config.NumberColumn("Companies", format="%d")
        
        # Giving metrics
        if 'avg_giving' in display_df.columns:
            column_config['avg_giving'] = st.column_config.NumberColumn("Avg. Giving", format="$%.2f M" if 'millions' in giving_col else "$%.2f")
        
        if 'median_giving' in display_df.columns:
            column_config['median_giving'] = st.column_config.NumberColumn("Median Giving", format="$%.2f M" if 'millions' in giving_col else "$%.2f")
        
        # Giving percentage metrics
        if 'avg_giving_pct' in display_df.columns:
            column_config['avg_giving_pct'] = st.column_config.NumberColumn("Giving % of Revenue", format="%.3f%%")
        
        # Transparency metrics
        if 'avg_transparency' in display_df.columns:
            column_config['avg_transparency'] = st.column_config.NumberColumn("Transparency Score", format="%.1f")
        
        # Leader score metrics
        if 'avg_leader_score' in display_df.columns:
            column_config['avg_leader_score'] = st.column_config.NumberColumn("Leadership Score", format="%.1f")
        
        # Comparison to average metrics
        if f'{selected_col}_vs_avg' in display_df.columns:
            column_config[f'{selected_col}_vs_avg'] = st.column_config.ProgressColumn(
                "vs. Average",
                help=f"Percentage difference from overall average {selected_metric.lower()}",
                format="%.1f%%",
                min_value=-50,
                max_value=50
            )
        
        # Display the table
        st.dataframe(
            display_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True
        )
    
    # Add company comparison within industry
    st.markdown("### Company Comparison Within Industry")
    
    # Allow user to select an industry
    selected_industry = st.selectbox(
        "Select an industry to compare companies:",
        options=sorted(df[industry_col].unique())
    )
    
    if selected_industry:
        # Filter companies in the selected industry
        industry_companies = df[df[industry_col] == selected_industry].copy()
        
        if len(industry_companies) > 0:
            # Sort by giving or leader score
            sort_by = st.radio(
                "Sort companies by:",
                ["Environmental Giving", "Leadership Score"] if "leader_score" in industry_companies.columns else ["Environmental Giving"],
                horizontal=True
            )
            
            sort_col = giving_col if sort_by == "Environmental Giving" else "leader_score"
            
            # Sort companies
            sorted_companies = industry_companies.sort_values(sort_col, ascending=False)
            
            # Get company name column
            name_col = None
            for col in ['company_name', 'Name', 'CompanyName']:
                if col in sorted_companies.columns:
                    name_col = col
                    break
            
            if name_col:
                # Create visualization of companies within the industry
                st.markdown(f"#### Company Comparison in {selected_industry} Industry")
                
                # Only show top 15 companies to avoid cluttering
                top_companies = sorted_companies.head(15)
                
                # Create bar chart
                fig = create_bar_chart(
                    top_companies,
                    x_col=sort_col,
                    y_col=name_col,
                    orientation='h',
                    title=f'Top 15 {selected_industry} Companies by {sort_by}',
                    text_col='leader_score' if sort_by == "Environmental Giving" and 'leader_score' in top_companies.columns else None
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate industry statistics
                industry_avg = sorted_companies[sort_col].mean()
                industry_median = sorted_companies[sort_col].median()
                industry_top_quartile = sorted_companies[sort_col].quantile(0.75)
                
                # Display statistics
                st.markdown(f"#### {selected_industry} Industry Statistics")
                
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                
                with stats_col1:
                    st.metric(
                        label=f"Industry Average {sort_by}",
                        value=f"${industry_avg:.2f}M" if 'millions' in sort_col and sort_by == "Environmental Giving" else f"{industry_avg:.1f}"
                    )
                
                with stats_col2:
                    st.metric(
                        label=f"Industry Median {sort_by}",
                        value=f"${industry_median:.2f}M" if 'millions' in sort_col and sort_by == "Environmental Giving" else f"{industry_median:.1f}"
                    )
                
                with stats_col3:
                    st.metric(
                        label=f"Industry Top Quartile {sort_by}",
                        value=f"${industry_top_quartile:.2f}M" if 'millions' in sort_col and sort_by == "Environmental Giving" else f"{industry_top_quartile:.1f}"
                    )

def display_esg_analysis_section(df):
    """Display ESG score analysis"""
    # Check if we have ESG scores
    has_esg = 'esg_score' in df.columns
    
    if not has_esg:
        st.info("ESG score data not found in the dataset.")
        return
    
    # Get company name and industry columns
    name_col = None
    for col in ['company_name', 'Name', 'CompanyName']:
        if col in df.columns:
            name_col = col
            break
    
    industry_col = None
    for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
        if col in df.columns:
            industry_col = col
            break
    
    # Get giving column
    giving_col = None
    for col in ['env_giving_millions', 'Charitable Contributions', 'environmental_giving', 'giving']:
        if col in df.columns:
            giving_col = col
            break
    
    # Display ESG score distribution
    st.markdown("### ESG Score Distribution")
    
    # Create histogram of ESG scores
    fig = px.histogram(
        df,
        x='esg_score',
        nbins=20,
        title='Distribution of ESG Scores',
        color_discrete_sequence=['#3366CC']
    )
    
    fig.update_layout(
        xaxis_title='ESG Score',
        yaxis_title='Number of Companies'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Create ESG analysis dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        # ESG vs. Environmental Giving
        if giving_col:
            fig = create_scatter_plot(
                df,
                x_col='esg_score',
                y_col=giving_col,
                color_col=industry_col if industry_col else None,
                hover_data=[name_col] if name_col else None,
                title='ESG Score vs. Environmental Giving'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ESG vs. Transparency
        if 'transparency_score' in df.columns:
            fig = create_scatter_plot(
                df,
                x_col='esg_score',
                y_col='transparency_score',
                color_col=industry_col if industry_col else None,
                hover_data=[name_col] if name_col else None,
                title='ESG Score vs. Transparency Score'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Display top ESG performers
    st.markdown("### Top ESG Performers")
    
    # Sort by ESG score
    top_esg = df.sort_values('esg_score', ascending=False).head(10)
    
    # Create a formatted table
    if name_col:
        top_esg_display = pd.DataFrame({
            'Company': top_esg[name_col],
            'ESG Score': top_esg['esg_score']
        })
        
        # Add industry if available
        if industry_col:
            top_esg_display['Industry'] = top_esg[industry_col]
        
        # Add giving if available
        if giving_col:
            top_esg_display['Environmental Giving'] = top_esg[giving_col]
        
        # Add transparency if available
        if 'transparency_score' in top_esg.columns:
            top_esg_display['Transparency Score'] = top_esg['transparency_score']
        
        # Format the dataframe for display
        column_config = {
            'Company': st.column_config.TextColumn('Company'),
            'ESG Score': st.column_config.NumberColumn('ESG Score', format="%.1f"),
            'Industry': st.column_config.TextColumn('Industry') if 'Industry' in top_esg_display.columns else None,
            'Environmental Giving': st.column_config.NumberColumn(
                'Environmental Giving', 
                format="$%.2f M" if 'millions' in giving_col else "$%.2f"
            ) if 'Environmental Giving' in top_esg_display.columns else None,
            'Transparency Score': st.column_config.NumberColumn(
                'Transparency Score', 
                format="%.1f"
            ) if 'Transparency Score' in top_esg_display.columns else None
        }
        
        st.dataframe(
            top_esg_display,
            column_config={k: v for k, v in column_config.items() if v is not None},
            hide_index=True,
            use_container_width=True
        )
    
    # Display industry ESG analysis
    if industry_col:
        with st.expander("Industry ESG Analysis"):
            # Calculate average ESG score by industry
            industry_esg = df.groupby(industry_col)['esg_score'].agg(['mean', 'median', 'std', 'count']).reset_index()
            industry_esg.columns = [industry_col, 'Average ESG Score', 'Median ESG Score', 'ESG Score Std Dev', 'Company Count']
            
            # Sort by average ESG score
            industry_esg = industry_esg.sort_values('Average ESG Score', ascending=False)
            
            # Create bar chart
            fig = create_bar_chart(
                industry_esg.head(10),
                x_col='Average ESG Score',
                y_col=industry_col,
                orientation='h',
                title='Top 10 Industries by Average ESG Score',
                text_col='Company Count'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display industry ESG statistics table
            st.markdown("### Industry ESG Statistics")
            
            st.dataframe(
                industry_esg,
                column_config={
                    industry_col: st.column_config.TextColumn('Industry'),
                    'Average ESG Score': st.column_config.NumberColumn('Average ESG Score', format="%.1f"),
                    'Median ESG Score': st.column_config.NumberColumn('Median ESG Score', format="%.1f"),
                    'ESG Score Std Dev': st.column_config.NumberColumn('Standard Deviation', format="%.1f"),
                    'Company Count': st.column_config.NumberColumn('Companies', format="%d")
                },
                hide_index=True,
                use_container_width=True
            )
    
    # Display ESG correlation analysis
    with st.expander("ESG Correlation Analysis"):
        # Create a correlation matrix
        corr_cols = ['esg_score']
        
        if giving_col:
            corr_cols.append(giving_col)
        
        if 'transparency_score' in df.columns:
            corr_cols.append('transparency_score')
        
        if 'environmental_impact_score' in df.columns:
            corr_cols.append('environmental_impact_score')
        
        if 'revenue_millions' in df.columns:
            corr_cols.append('revenue_millions')
        
        if 'leader_score' in df.columns:
            corr_cols.append('leader_score')
        
        if len(corr_cols) > 1:
            corr_matrix = df[corr_cols].corr()
            
            # Create heatmap
            fig = px.imshow(
                corr_matrix,
                text_auto='.2f',
                color_continuous_scale='RdBu_r',
                zmin=-1,
                zmax=1,
                title='Correlation Matrix of ESG and Other Environmental Metrics'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights about correlations
            st.markdown("### Key ESG Insights")
            
            # Calculate correlations with ESG score
            esg_correlations = []
            
            for col in corr_cols:
                if col != 'esg_score':
                    corr_value = corr_matrix.loc['esg_score', col]
                    esg_correlations.append((col, corr_value))
            
            # Sort by absolute correlation strength
            esg_correlations.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for col, corr_value in esg_correlations:
                # Format column name for display
                display_col = col.replace('_', ' ').title()
                
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
                
                st.markdown(f"• ESG Score has a **{strength} {direction} correlation** ({corr_value:.2f}) with {display_col}")
            
            # Overall interpretation
            if esg_correlations:
                strongest_metric, strongest_corr = esg_correlations[0]
                strongest_display = strongest_metric.replace('_', ' ').title()
                
                st.markdown(f"• The strongest relationship is between **ESG Score** and **{strongest_display}** ({strongest_corr:.2f})")
                
                # Check if transparency or giving is strongly correlated
                transparency_corr = next((corr for col, corr in esg_correlations if 'transparency' in col.lower()), None)
                giving_corr = next((corr for col, corr in esg_correlations if 'giving' in col.lower()), None)
                
                if transparency_corr and giving_corr:
                    if abs(transparency_corr) > abs(giving_corr):
                        st.markdown(f"• ESG Scores show a stronger relationship with **transparency** ({transparency_corr:.2f}) than with **environmental giving** ({giving_corr:.2f})")
                    else:
                        st.markdown(f"• ESG Scores show a stronger relationship with **environmental giving** ({giving_corr:.2f}) than with **transparency** ({transparency_corr:.2f})")