"""
modules/transparency.py
Implements the second part of the narrative: "How transparent are they?"
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
        create_pie_chart, create_bar_chart, create_line_chart, create_heatmap,
        display_insights_expander, create_filter_section
    )
except ImportError:
    # Define fallback functions if the module isn't available
    def create_pie_chart(df, values_col, names_col, title='', hole=0.4, vis_id=None):
        fig = px.pie(
            df,
            values=values_col,
            names=names_col,
            title=title,
            hole=hole
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
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
    
    def create_line_chart(df, x_col, y_col, color_col=None, title='', markers=True, vis_id=None):
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
            markers=markers
        )
        return fig
    
    def create_heatmap(df, x_cols, y_cols, values, title='', color_scale='Viridis', vis_id=None):
        if isinstance(df, pd.DataFrame):
            # For pivot tables
            fig = px.imshow(
                df, 
                labels=dict(x="Columns", y="Rows", color=values),
                title=title,
                color_continuous_scale=color_scale
            )
        else:
            # For raw data
            fig = px.imshow(
                df,
                x=x_cols,
                y=y_cols,
                title=title,
                color_continuous_scale=color_scale
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

def display_transparency_tab(df, historical_df=None):
    """Display the Transparency tab visualizations"""
    st.header("How transparent are they?", help="This section examines the quality and completeness of corporate environmental disclosures.")
    
    # Brief introduction to this section
    st.markdown("""
    This section examines the quality and completeness of corporate environmental disclosures.
    Explore reporting levels, transparency scores, year-over-year improvements, and reporting gaps.
    """)
    
    # Check if we need to generate transparency data
    if not has_transparency_data(df) and historical_df is None:
        st.warning("Transparency data not found in the dataset. Some visualizations may not be available.")
    
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
        "📝 Reporting Detail", 
        "📊 Transparency Ratings", 
        "📈 Reporting Trends",
        "🚫 Missing Data"
    ])
    
    with tab1:
        # Reporting Detail Level
        st.subheader("Reporting Detail Level")
        display_reporting_detail_section(filtered_df)
    
    with tab2:
        # Transparency Rating Visualization (#11)
        st.subheader("Transparency Score by Industry")
        display_transparency_rating_section(filtered_df)
    
    with tab3:
        # Year-over-year reporting improvement tracker
        st.subheader("Reporting Improvement Over Time")
        display_reporting_improvement_section(historical_df if historical_df is not None else filtered_df)
    
    with tab4:
        # Missing Data Indicator (#22)
        st.subheader("Missing Data Analysis")
        display_missing_data_section(filtered_df)

def has_transparency_data(df):
    """Check if the dataframe has transparency-related columns"""
    transparency_columns = [
        'transparency_score', 'reporting_level', 'Detail', 'detail_level',
        'score_environmental_impact_disclosure', 'score_giving_strategy_documentation',
        'score_goal_setting_and_progress', 'score_third_party_verification',
        'score_stakeholder_engagement'
    ]
    
    # Check if at least some transparency columns exist
    return any(col in df.columns for col in transparency_columns)

def display_reporting_detail_section(df):
    """Display reporting detail level visualization"""
    # Check if we have a reporting_level column or a Detail column
    if 'reporting_level' in df.columns:
        reporting_col = 'reporting_level'
        value_col = reporting_col
    elif 'Detail' in df.columns:
        # If we only have Detail column (0/1), convert to reporting levels
        reporting_col = 'Detail'
        df['reporting_level_derived'] = df['Detail'].apply(
            lambda x: 'Detailed' if x == 1 else 'Minimal'
        )
        value_col = 'reporting_level_derived'
    elif 'detail_level' in df.columns:
        reporting_col = 'detail_level'
        value_col = reporting_col
    else:
        st.info("Reporting detail level information not found in the dataset.")
        return
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Count companies by reporting level
        reporting_counts = df[value_col].value_counts().reset_index()
        reporting_counts.columns = ['Reporting Level', 'Count']
        
        # Calculate percentages
        total_companies = reporting_counts['Count'].sum()
        reporting_counts['Percentage'] = (reporting_counts['Count'] / total_companies) * 100
        
        # Create pie chart
        fig = create_pie_chart(
            reporting_counts,
            values_col='Count',
            names_col='Reporting Level',
            title='Distribution of Reporting Detail Levels',
            hole=0.4
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display reporting level distribution table
        st.markdown("### Reporting Level Distribution")
        
        # Sort levels by a standardized order if possible
        if reporting_col == 'reporting_level' or value_col == 'reporting_level_derived':
            level_order = {
                'Minimal': 0,
                'Basic': 1,
                'Standard': 2,
                'Detailed': 3,
                'Comprehensive': 4
            }
            
            # Check if all values are in the standard order
            if all(level in level_order for level in reporting_counts['Reporting Level']):
                # Sort by the defined order
                reporting_counts['Order'] = reporting_counts['Reporting Level'].map(level_order)
                reporting_counts = reporting_counts.sort_values('Order')
                reporting_counts = reporting_counts.drop(columns=['Order'])
        
        # Format table for display
        st.dataframe(
            reporting_counts,
            column_config={
                'Reporting Level': st.column_config.TextColumn('Reporting Level'),
                'Count': st.column_config.NumberColumn('Companies', format="%d"),
                'Percentage': st.column_config.ProgressColumn(
                    '% of Total',
                    min_value=0,
                    max_value=100,
                    format="%.1f%%"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Add context about what the reporting levels mean
    with st.expander("About Reporting Levels"):
        st.markdown("""
        ### Reporting Detail Levels
        
        The reporting detail levels indicate how thoroughly companies disclose their environmental philanthropic activities:
        
        - **Comprehensive**: Extensive quantitative and qualitative disclosures with third-party verification
        - **Detailed**: Thorough disclosures with specific metrics, goals, and outcomes
        - **Standard**: Basic information with some quantitative metrics
        - **Basic**: Limited information with minimal quantitative data
        - **Minimal**: Very little information disclosed, primarily qualitative
        
        Companies with higher reporting detail levels provide more transparent and accountable information about their environmental giving.
        """)
    
    # Add detailed analysis of reporting levels
    with st.expander("Reporting Level Analysis"):
        # For the original Detail column, calculate differently
        if reporting_col == 'Detail':
            at_detail = df[df['Detail'] == 1].shape[0]
            not_at_detail = total_companies - at_detail
            
            detail_context = f"""
            A submission "at Required Detail Level" includes detailed quantitative disclosures in its footnotes and schedules. 
            For example, instead of a total expense figure, it breaks down amounts into categories like compensation, accounting fees, and legal fees.
            
            - **At Required Detail Level**: {at_detail} companies ({at_detail/total_companies*100:.1f}%)
            - **NOT at Required Detail Level**: {not_at_detail} companies ({not_at_detail/total_companies*100:.1f}%)
            
            The high percentage of companies not meeting the required detail level suggests **incomplete** and/or **inconsistent** philanthropic reporting.
            """
            
            st.markdown(detail_context)
        
        # If we have reporting levels, analyze by industry
        if 'industry' in df.columns and reporting_col in df.columns:
            st.markdown("### Reporting Level by Industry")
            
            # Group by industry and reporting level
            industry_reporting = df.groupby(['industry', value_col]).size().reset_index()
            industry_reporting.columns = ['Industry', 'Reporting Level', 'Count']
            
            # Calculate total companies per industry
            industry_totals = industry_reporting.groupby('Industry')['Count'].sum().reset_index()
            industry_totals.columns = ['Industry', 'Total']
            
            # Merge to get percentages
            industry_reporting = pd.merge(industry_reporting, industry_totals, on='Industry')
            industry_reporting['Percentage'] = (industry_reporting['Count'] / industry_reporting['Total']) * 100
            
            # Filter to top industries
            top_industries = industry_totals.nlargest(10, 'Total')['Industry'].values
            top_industry_reporting = industry_reporting[industry_reporting['Industry'].isin(top_industries)]
            
            # Create stacked bar chart
            fig = px.bar(
                top_industry_reporting,
                x='Industry',
                y='Percentage',
                color='Reporting Level',
                title='Reporting Level Distribution by Industry (Top 10)',
                text='Count'
            )
            
            fig.update_traces(texttemplate='%{text}', textposition='inside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Identify industries with best and worst reporting
            if 'Detailed' in industry_reporting['Reporting Level'].values or 'Comprehensive' in industry_reporting['Reporting Level'].values:
                high_level = 'Detailed' if 'Detailed' in industry_reporting['Reporting Level'].values else 'Comprehensive'
                
                # Calculate percentage of high-level reporting by industry
                high_level_pcts = industry_reporting[industry_reporting['Reporting Level'] == high_level].copy()
                
                if len(high_level_pcts) > 0:
                    high_level_pcts = high_level_pcts.sort_values('Percentage', ascending=False)
                    
                    st.markdown(f"#### Industries with Best {high_level} Reporting")
                    
                    best_industries = high_level_pcts.head(5)
                    for _, row in best_industries.iterrows():
                        st.markdown(f"• **{row['Industry']}**: {row['Percentage']:.1f}% ({row['Count']} of {row['Total']} companies)")
                    
                    st.markdown(f"#### Industries with Worst {high_level} Reporting")
                    
                    worst_industries = high_level_pcts.tail(5)
                    for _, row in worst_industries.iterrows():
                        st.markdown(f"• **{row['Industry']}**: {row['Percentage']:.1f}% ({row['Count']} of {row['Total']} companies)")

def display_transparency_rating_section(df):
    """Display transparency rating visualizations"""
    # Check if we have a transparency_score column
    if 'transparency_score' not in df.columns:
        if 'Detail' in df.columns:
            # Create a simple transparency score based on Detail
            df['transparency_score'] = df['Detail'].apply(lambda x: 80 if x == 1 else 30)
        else:
            st.info("Transparency score information not found in the dataset.")
            return
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Get industry column
        industry_col = None
        for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
            if col in df.columns:
                industry_col = col
                break
        
        if industry_col is None:
            # If no industry column, show overall transparency score distribution
            fig = px.histogram(
                df,
                x='transparency_score',
                nbins=20,
                title='Distribution of Transparency Scores',
                color_discrete_sequence=['#3366CC']
            )
            
            fig.update_layout(
                xaxis_title='Transparency Score',
                yaxis_title='Number of Companies'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Calculate industry averages
            industry_transparency = df.groupby(industry_col)['transparency_score'].agg(['mean', 'count']).reset_index()
            industry_transparency.columns = [industry_col, 'Avg. Transparency Score', 'Company Count']
            
            # Sort by score and take top industries
            industry_transparency = industry_transparency.sort_values('Avg. Transparency Score', ascending=False)
            top_industries = industry_transparency.head(15)
            
            # Create horizontal bar chart
            fig = create_bar_chart(
                top_industries,
                x_col='Avg. Transparency Score',
                y_col=industry_col,
                color_col='Avg. Transparency Score',
                orientation='h',
                title='Top 15 Industries by Transparency Score',
                text_col='Company Count'
            )
            
            # Add a vertical line for overall average
            overall_avg = df['transparency_score'].mean()
            fig.add_vline(
                x=overall_avg, 
                line_dash="dash", 
                line_color="red", 
                annotation_text=f"Overall Avg: {overall_avg:.1f}",
                annotation_position="top right"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create a transparency score gauge chart
        overall_avg = df['transparency_score'].mean()
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = overall_avg,
            title = {'text': "Average Transparency Score"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "gray"},
                    {'range': [50, 75], 'color': "lightblue"},
                    {'range': [75, 100], 'color': "royalblue"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display metrics about transparency
        st.markdown("### Transparency Metrics")
        
        # Calculate percentage in each quartile
        q1 = (df['transparency_score'] < 25).mean() * 100
        q2 = ((df['transparency_score'] >= 25) & (df['transparency_score'] < 50)).mean() * 100
        q3 = ((df['transparency_score'] >= 50) & (df['transparency_score'] < 75)).mean() * 100
        q4 = (df['transparency_score'] >= 75).mean() * 100
        
        # Display metrics as a bullet list
        st.markdown(f"• **Poor** (0-25): {q1:.1f}% of companies")
        st.markdown(f"• **Fair** (25-50): {q2:.1f}% of companies")
        st.markdown(f"• **Good** (50-75): {q3:.1f}% of companies")
        st.markdown(f"• **Excellent** (75-100): {q4:.1f}% of companies")
        
        # Determine transparency rating
        if overall_avg >= 75:
            rating = "Excellent"
        elif overall_avg >= 50:
            rating = "Good"
        elif overall_avg >= 25:
            rating = "Fair"
        else:
            rating = "Poor"
        
        st.markdown(f"### Overall Transparency Rating: **{rating}**")
    
    # Add industry comparison details
    with st.expander("Industry Transparency Comparison"):
        if industry_col:
            # Allow user to select sorting method
            sort_by = st.radio(
                "Sort industries by:",
                ["Transparency Score", "Number of Companies"],
                horizontal=True
            )
            
            # Sort and display the full industry dataset
            if sort_by == "Transparency Score":
                display_df = industry_transparency.sort_values('Avg. Transparency Score', ascending=False)
            else:
                display_df = industry_transparency.sort_values('Company Count', ascending=False)
            
            # Calculate the relative comparison to average
            display_df['Compared to Average'] = ((display_df['Avg. Transparency Score'] / overall_avg) - 1) * 100
            
            # Format the dataframe for display
            st.dataframe(
                display_df,
                column_config={
                    industry_col: "Industry",
                    'Avg. Transparency Score': st.column_config.NumberColumn('Transparency Score (0-100)', format="%.1f"),
                    'Company Count': st.column_config.NumberColumn('Number of Companies', format="%d"),
                    'Compared to Average': st.column_config.ProgressColumn(
                        'Compared to Average',
                        format="%.1f%%",
                        min_value=-50,
                        max_value=50
                    )
                },
                hide_index=True,
                use_container_width=True
            )
    
    # Add detailed metrics if available
    if any(col.startswith('score_') for col in df.columns):
        with st.expander("Detailed Transparency Metrics"):
            # Get all score columns
            score_cols = [col for col in df.columns if col.startswith('score_')]
            
            if score_cols:
                # Calculate averages for each score
                score_avgs = {}
                for col in score_cols:
                    # Clean up column name for display
                    display_name = col.replace('score_', '').replace('_', ' ').title()
                    score_avgs[display_name] = df[col].mean()
                
                # Create a bar chart of the score averages
                score_df = pd.DataFrame({'Metric': list(score_avgs.keys()), 'Average Score': list(score_avgs.values())})
                score_df = score_df.sort_values('Average Score', ascending=False)
                
                fig = px.bar(
                    score_df,
                    x='Average Score',
                    y='Metric',
                    orientation='h',
                    title='Average Scores by Transparency Metric',
                    color='Average Score',
                    color_continuous_scale='Viridis'
                )
                
                # Update layout to add a scale reference
                fig.update_layout(
                    xaxis=dict(title='Average Score (0-10 scale)'),
                    xaxis_range=[0, 10]
                )
                
                # Display the chart
                st.plotly_chart(fig, use_container_width=True)
                
                # Display highest and lowest scoring metrics
                highest_metric = score_df.iloc[0]
                lowest_metric = score_df.iloc[-1]
                
                st.markdown("### Key Transparency Insights")
                st.markdown(f"• Companies score highest on **{highest_metric['Metric']}** ({highest_metric['Average Score']:.1f}/10)")
                st.markdown(f"• Companies score lowest on **{lowest_metric['Metric']}** ({lowest_metric['Average Score']:.1f}/10)")
                
                # Calculate percentage of companies with good scores (>7/10) for each metric
                good_scores = {}
                for col in score_cols:
                    display_name = col.replace('score_', '').replace('_', ' ').title()
                    good_scores[display_name] = (df[col] >= 7).mean() * 100
                
                # Display the percentages
                st.markdown("### Percentage of Companies with Good Scores (7+/10)")
                
                for metric, pct in sorted(good_scores.items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"• **{metric}**: {pct:.1f}%")

def display_reporting_improvement_section(df):
    """Display year-over-year reporting improvement visualizations"""
    # Check if we have historical data with years
    if isinstance(df, dict) and 'transparency_history' in df:
        # We have a dictionary of historical dataframes
        historical_df = df['transparency_history']
        
        if isinstance(historical_df, pd.DataFrame) and 'year' in historical_df.columns and 'transparency_score' in historical_df.columns:
            # Group by year to get overall average
            yearly_avg = historical_df.groupby('year')['transparency_score'].mean().reset_index()
            
            # Create line chart for overall trend
            fig = create_line_chart(
                yearly_avg,
                x_col='year',
                y_col='transparency_score',
                title='Average Transparency Score Trend'
            )
            
            # Update layout to make the chart clearer
            fig.update_layout(
                xaxis_title='Year',
                yaxis_title='Average Transparency Score',
                yaxis_range=[0, 100]
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Allow breakdown by industry
            industry_col = 'industry' if 'industry' in historical_df.columns else None
            
            if industry_col:
                st.markdown("### Industry Trends Over Time")
                
                # Let user select industries to compare
                industries = sorted(historical_df[industry_col].unique())
                selected_industries = st.multiselect(
                    "Select industries to compare:",
                    options=industries,
                    default=industries[:5] if len(industries) > 5 else industries
                )
                
                if selected_industries:
                    # Filter for selected industries
                    filtered_df = historical_df[historical_df[industry_col].isin(selected_industries)]
                    
                    # Group by industry and year
                    industry_yearly = filtered_df.groupby([industry_col, 'year'])['transparency_score'].mean().reset_index()
                    
                    # Create line chart for selected industries
                    fig = px.line(
                        industry_yearly,
                        x='year',
                        y='transparency_score',
                        color=industry_col,
                        title='Transparency Score by Industry Over Time',
                        labels={
                            'year': 'Year',
                            'transparency_score': 'Avg. Transparency Score',
                            industry_col: 'Industry'
                        }
                    )
                    
                    # Add the overall average line
                    fig.add_trace(
                        go.Scatter(
                            x=yearly_avg['year'],
                            y=yearly_avg['transparency_score'],
                            mode='lines+markers',
                            name='Overall Average',
                            line=dict(color='black', width=3, dash='dot')
                        )
                    )
                    
                    fig.update_layout(
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                        yaxis=dict(title='Average Transparency Score (0-100)')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calculate improvement rates
                    if len(yearly_avg) > 1:
                        first_year = yearly_avg['year'].min()
                        last_year = yearly_avg['year'].max()
                        overall_first = yearly_avg[yearly_avg['year'] == first_year]['transparency_score'].values[0]
                        overall_last = yearly_avg[yearly_avg['year'] == last_year]['transparency_score'].values[0]
                        overall_change = ((overall_last - overall_first) / overall_first) * 100
                        
                        st.markdown(f"### Improvement Analysis ({first_year} to {last_year})")
                        
                        # Create a dataframe to show improvement by industry
                        improvement_data = []
                        
                        for industry in selected_industries:
                            industry_data = filtered_df[filtered_df[industry_col] == industry]
                            if len(industry_data) > 0:
                                first_score = industry_data[industry_data['year'] == first_year]['transparency_score'].mean()
                                last_score = industry_data[industry_data['year'] == last_year]['transparency_score'].mean()
                                
                                if pd.notna(first_score) and pd.notna(last_score):
                                    change_pct = ((last_score - first_score) / first_score) * 100
                                    improvement_data.append({
                                        'Industry': industry,
                                        'First Year Score': first_score,
                                        'Latest Year Score': last_score,
                                        'Change (%)': change_pct
                                    })
                        
                        if improvement_data:
                            improvement_df = pd.DataFrame(improvement_data)
                            improvement_df = improvement_df.sort_values('Change (%)', ascending=False)
                            
                            st.dataframe(
                                improvement_df,
                                column_config={
                                    'Industry': st.column_config.TextColumn('Industry'),
                                    'First Year Score': st.column_config.NumberColumn(f'{first_year} Score', format="%.1f"),
                                    'Latest Year Score': st.column_config.NumberColumn(f'{last_year} Score', format="%.1f"),
                                    'Change (%)': st.column_config.ProgressColumn(
                                        'Improvement',
                                        help='Percentage change in transparency score',
                                        format='%.1f%%',
                                        min_value=-10,
                                        max_value=50
                                    )
                                },
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Highlight industries improving faster or slower than average
                            st.markdown(f"**Overall transparency** has improved by **{overall_change:.1f}%** from {first_year} to {last_year}.")
                            
                            above_avg = improvement_df[improvement_df['Change (%)'] > overall_change]['Industry'].tolist()
                            below_avg = improvement_df[improvement_df['Change (%)'] < overall_change]['Industry'].tolist()
                            
                            if above_avg:
                                st.markdown(f"**Industries improving faster than average**: {', '.join(above_avg[:3])}{' and others' if len(above_avg) > 3 else ''}")
                            
                            if below_avg:
                                st.markdown(f"**Industries improving slower than average**: {', '.join(below_avg[:3])}{' and others' if len(below_avg) > 3 else ''}")
        
    elif isinstance(df, pd.DataFrame) and 'year' in df.columns and 'transparency_score' in df.columns:
        # We have the right historical dataframe
        historical_df = df
        
        # Group by year to get overall average
        yearly_avg = historical_df.groupby('year')['transparency_score'].mean().reset_index()
        
        # Create line chart for overall trend
        fig = create_line_chart(
            yearly_avg,
            x_col='year',
            y_col='transparency_score',
            title='Average Transparency Score Trend'
        )
        
        # Update layout to make the chart clearer
        fig.update_layout(
            xaxis_title='Year',
            yaxis_title='Average Transparency Score',
            yaxis_range=[0, 100]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Allow breakdown by industry
        industry_col = 'industry' if 'industry' in historical_df.columns else None
        
        if industry_col:
            st.markdown("### Industry Trends Over Time")
            
            # Let user select industries to compare
            industries = sorted(historical_df[industry_col].unique())
            selected_industries = st.multiselect(
                "Select industries to compare:",
                options=industries,
                default=industries[:5] if len(industries) > 5 else industries
            )
            
            if selected_industries:
                # Filter for selected industries
                filtered_df = historical_df[historical_df[industry_col].isin(selected_industries)]
                
                # Create line chart for selected industries
                fig = px.line(
                    filtered_df,
                    x='year',
                    y='transparency_score',
                    color=industry_col,
                    title='Transparency Score by Industry Over Time',
                    labels={
                        'year': 'Year',
                        'transparency_score': 'Avg. Transparency Score',
                        industry_col: 'Industry'
                    }
                )
                
                # Add the overall average line
                fig.add_trace(
                    go.Scatter(
                        x=yearly_avg['year'],
                        y=yearly_avg['transparency_score'],
                        mode='lines+markers',
                        name='Overall Average',
                        line=dict(color='black', width=3, dash='dot')
                    )
                )
                
                fig.update_layout(
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    yaxis=dict(title='Average Transparency Score (0-100)')
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate improvement rates
                if len(yearly_avg) > 1:
                    first_year = yearly_avg['year'].min()
                    last_year = yearly_avg['year'].max()
                    overall_first = yearly_avg[yearly_avg['year'] == first_year]['transparency_score'].values[0]
                    overall_last = yearly_avg[yearly_avg['year'] == last_year]['transparency_score'].values[0]
                    overall_change = ((overall_last - overall_first) / overall_first) * 100
                    
                    st.markdown(f"### Improvement Analysis ({first_year} to {last_year})")
                    
                    # Create a dataframe to show improvement by industry
                    improvement_data = []
                    
                    for industry in selected_industries:
                        industry_data = filtered_df[filtered_df[industry_col] == industry]
                        if len(industry_data) > 0:
                            first_score = industry_data[industry_data['year'] == first_year]['transparency_score'].mean()
                            last_score = industry_data[industry_data['year'] == last_year]['transparency_score'].mean()
                            
                            if pd.notna(first_score) and pd.notna(last_score):
                                change_pct = ((last_score - first_score) / first_score) * 100
                                improvement_data.append({
                                    'Industry': industry,
                                    'First Year Score': first_score,
                                    'Latest Year Score': last_score,
                                    'Change (%)': change_pct
                                })
                    
                    if improvement_data:
                        improvement_df = pd.DataFrame(improvement_data)
                        improvement_df = improvement_df.sort_values('Change (%)', ascending=False)
                        
                        st.dataframe(
                            improvement_df,
                            column_config={
                                'Industry': st.column_config.TextColumn('Industry'),
                                'First Year Score': st.column_config.NumberColumn(f'{first_year} Score', format="%.1f"),
                                'Latest Year Score': st.column_config.NumberColumn(f'{last_year} Score', format="%.1f"),
                                'Change (%)': st.column_config.ProgressColumn(
                                    'Improvement',
                                    help='Percentage change in transparency score',
                                    format='%.1f%%',
                                    min_value=-10,
                                    max_value=50
                                )
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        # Highlight industries improving faster or slower than average
                        st.markdown(f"**Overall transparency** has improved by **{overall_change:.1f}%** from {first_year} to {last_year}.")
                        
                        above_avg = improvement_df[improvement_df['Change (%)'] > overall_change]['Industry'].tolist()
                        below_avg = improvement_df[improvement_df['Change (%)'] < overall_change]['Industry'].tolist()
                        
                        if above_avg:
                            st.markdown(f"**Industries improving faster than average**: {', '.join(above_avg[:3])}{' and others' if len(above_avg) > 3 else ''}")
                        
                        if below_avg:
                            st.markdown(f"**Industries improving slower than average**: {', '.join(below_avg[:3])}{' and others' if len(below_avg) > 3 else ''}")
    
    else:
        # Try to extract date information if available
        date_col = None
        for col_option in ['Date of Filing', 'Filing Date', 'Report Date', 'date']:
            if col_option in df.columns:
                date_col = col_option
                break
        
        if date_col is None:
            st.info("Historical date information not found in the dataset.")
            return
        
        try:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df['filing_date'] = pd.to_datetime(df[date_col], errors='coerce')
            else:
                df['filing_date'] = df[date_col]
            
            # Extract year
            df['filing_year'] = df['filing_date'].dt.year
            
            # Check if we have transparency score or Detail
            score_col = None
            if 'transparency_score' in df.columns:
                score_col = 'transparency_score'
            elif 'Detail' in df.columns:
                score_col = 'Detail'
                # Convert to percentage
                df['detail_score'] = df['Detail'] * 100
                score_col = 'detail_score'
            
            if score_col:
                # Group by year to get average score
                yearly_avg = df.groupby('filing_year')[score_col].mean().reset_index()
                yearly_avg.columns = ['year', 'avg_score']
                
                # Create line chart for trend
                fig = create_line_chart(
                    yearly_avg,
                    x_col='year',
                    y_col='avg_score',
                    title='Reporting Quality Trend'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add context
                st.markdown(f"This chart shows the trend in reporting quality over time. {'Higher values indicate more detailed reporting.' if score_col == 'detail_score' else 'Higher transparency scores indicate more comprehensive environmental disclosures.'}")
            else:
                st.info("Transparency score or detail information not found in the dataset.")
        except Exception as e:
            st.error(f"Error processing date information: {e}")
            st.info("Could not analyze reporting improvement trends.")

def display_missing_data_section(df):
    """Display missing data indicator visualizations"""
    # Identify environmental disclosure columns to check for missing data
    env_cols = []
    
    # Check for specific environmental metrics
    for col in [
        'env_giving_millions', 'environmental_impact_score', 'emissions_tons', 
        'waste_tons', 'water_usage_gallons', 'energy_consumption_mwh',
        'env_loss_contingencies_millions', 'env_remediation_expenses_millions',
        'Environmental Remediation Expenses', 'Accrual for Environmental Loss Contingencies',
        'Charitable Contributions'
    ]:
        if col in df.columns:
            env_cols.append(col)
    
    # Check for transparency score columns
    score_cols = [col for col in df.columns if col.startswith('score_')]
    env_cols.extend(score_cols)
    
    if not env_cols:
        st.info("No environmental metrics found to analyze missing data.")
        return
    
    # Calculate missing data percentages
    missing_data = []
    
    for col in env_cols:
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / len(df)) * 100
        
        missing_data.append({
            'Metric': col.replace('_', ' ').title(),
            'Missing Count': missing_count,
            'Missing Percentage': missing_pct
        })
    
    # Convert to dataframe and sort
    missing_df = pd.DataFrame(missing_data)
    missing_df = missing_df.sort_values('Missing Percentage', ascending=False)
    
    # Create bar chart of missing percentages
    fig = px.bar(
        missing_df,
        x='Missing Percentage',
        y='Metric',
        orientation='h',
        title='Missing Data by Environmental Metric',
        color='Missing Percentage',
        color_continuous_scale='Reds',
        text='Missing Count'
    )
    
    fig.update_traces(texttemplate='%{text} companies', textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display missing data table
    st.dataframe(
        missing_df,
        column_config={
            'Metric': st.column_config.TextColumn('Metric'),
            'Missing Count': st.column_config.NumberColumn('Missing Companies', format="%d"),
            'Missing Percentage': st.column_config.ProgressColumn(
                '% Missing',
                help='Percentage of companies not reporting this metric',
                format="%.1f%%",
                min_value=0,
                max_value=100
            )
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Industry analysis of missing data if industry column is available
    industry_col = None
    for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
        if col in df.columns:
            industry_col = col
            break
    
    if industry_col:
        with st.expander("Missing Data by Industry"):
            # For simplicity, focus on the most-missing metric
            most_missing_metric = missing_df.iloc[0]['Metric'].replace(' ', '_').lower()
            most_missing_col = None
            
            # Find the actual column name
            for col in env_cols:
                if col.lower() == most_missing_metric or col.replace('_', ' ').title() == missing_df.iloc[0]['Metric']:
                    most_missing_col = col
                    break
            
            if most_missing_col:
                # Calculate missing percentage by industry
                industry_missing = df.groupby(industry_col)[most_missing_col].apply(
                    lambda x: x.isna().mean() * 100
                ).reset_index()
                industry_missing.columns = ['Industry', 'Missing Percentage']
                
                # Add company count by industry
                industry_counts = df.groupby(industry_col).size().reset_index()
                industry_counts.columns = ['Industry', 'Company Count']
                
                # Merge the dataframes
                industry_missing = pd.merge(industry_missing, industry_counts, on='Industry')
                
                # Sort by missing percentage
                industry_missing = industry_missing.sort_values('Missing Percentage', ascending=False)
                
                # Create bar chart
                fig = px.bar(
                    industry_missing.head(15),
                    x='Missing Percentage',
                    y='Industry',
                    orientation='h',
                    title=f'Top 15 Industries Missing "{missing_df.iloc[0]["Metric"]}" Data',
                    color='Missing Percentage',
                    color_continuous_scale='Reds',
                    text='Company Count'
                )
                
                fig.update_traces(texttemplate='%{text} companies', textposition='outside')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create a heatmap of missing data by industry and metric
                st.subheader("Missing Data Heatmap by Industry and Metric")
                
                # Calculate missing percentage for each industry and metric
                heatmap_data = []
                
                # Limit to top industries by company count
                top_industries = industry_counts.nlargest(10, 'Company Count')['Industry'].values
                
                for ind in top_industries:
                    industry_df = df[df[industry_col] == ind]
                    
                    for col in env_cols:
                        missing_pct = industry_df[col].isna().mean() * 100
                        
                        heatmap_data.append({
                            'Industry': ind,
                            'Metric': col.replace('_', ' ').title(),
                            'Missing Percentage': missing_pct
                        })
                
                # Convert to dataframe
                heatmap_df = pd.DataFrame(heatmap_data)
                
                # Create a pivot table for the heatmap
                heatmap_pivot = heatmap_df.pivot(index='Industry', columns='Metric', values='Missing Percentage')
                
                # Create heatmap
                fig = px.imshow(
                    heatmap_pivot,
                    labels=dict(x="Metric", y="Industry", color="% Missing"),
                    x=heatmap_pivot.columns,
                    y=heatmap_pivot.index,
                    color_continuous_scale='Reds',
                    title='Missing Data Heatmap (% Missing by Industry and Metric)'
                )
                
                fig.update_layout(
                    xaxis={'tickangle': 45}
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Add missing data insights
    with st.expander("Missing Data Insights"):
        st.markdown("### Key Missing Data Insights")
        
        # Calculate overall missing percentage
        overall_missing = sum(missing_df['Missing Count']) / (len(df) * len(env_cols)) * 100
        
        st.markdown(f"• Overall, **{overall_missing:.1f}%** of environmental data is missing across all metrics")
        
        # Most and least missing metrics
        most_missing = missing_df.iloc[0]
        least_missing = missing_df.iloc[-1]
        
        st.markdown(f"• **{most_missing['Metric']}** is the least reported metric ({most_missing['Missing Percentage']:.1f}% missing)")
        st.markdown(f"• **{least_missing['Metric']}** is the most commonly reported metric ({least_missing['Missing Percentage']:.1f}% missing)")
        
        # Industry-specific insights if available
        if industry_col and 'industry_missing' in locals():
            worst_industry = industry_missing.iloc[0]
            best_industry = industry_missing.iloc[-1]
            
            st.markdown(f"• **{worst_industry['Industry']}** has the highest percentage of missing data ({worst_industry['Missing Percentage']:.1f}%)")
            st.markdown(f"• **{best_industry['Industry']}** has the lowest percentage of missing data ({best_industry['Missing Percentage']:.1f}%)")
        
        # Recommendations based on missing data
        st.markdown("""
        ### Recommendations for Improving Transparency
        
        Based on this missing data analysis, we recommend:
        
        1. **Industry Standards**: Industries with high missing data percentages should develop standardized reporting frameworks
        2. **Regulatory Focus**: Regulators should focus on the least-reported metrics when developing disclosure requirements
        3. **Transparency Incentives**: Create incentives for companies to improve reporting in areas with significant gaps
        4. **Best Practice Sharing**: Companies with complete reporting should share their approaches with industry peers
        """)