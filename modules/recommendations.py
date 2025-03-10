"""
modules/recommendations.py
Implements the final part of the narrative: "What can be done?"
More structured implementation based on the dashboard visualization suggestions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def display_recommendations_tab(df):
    """Display the Recommendations tab visualizations"""
    st.header("What can be done?", help="This section provides recommendations based on the data analysis.")
    
    # Brief introduction to this section
    st.markdown("""
    This section provides actionable recommendations for various stakeholders based on our analysis of 
    corporate environmental philanthropy data. Learn how different groups can use these insights to drive change.
    """)
    
    # Use tabs for different stakeholder recommendations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Policy Recommendations", 
        "🏢 Corporate Improvement", 
        "🌍 Community Advocacy",
        "📊 Data Improvements"
    ])
    
    with tab1:
        # Policy recommendations panel
        st.subheader("Policy Recommendations")
        display_policy_recommendations(df)
    
    with tab2:
        # Corporate improvement roadmap
        st.subheader("Corporate Improvement Roadmap")
        display_corporate_improvements(df)
    
    with tab3:
        # Community advocacy toolkit
        st.subheader("Community Advocacy Toolkit")
        display_community_advocacy(df)
    
    with tab4:
        # Data improvement recommendations
        st.subheader("Data Improvement Recommendations")
        display_data_improvements(df)

def display_policy_recommendations(df):
    """Display policy recommendations based on data insights"""
    st.markdown("""
    ### Key Policy Recommendations
    
    Based on our analysis of corporate environmental philanthropy data, we recommend the following policy actions:
    """)
    
    # Create expandable sections for different policy areas
    with st.expander("1. Enhanced Disclosure Requirements", expanded=True):
        st.markdown("""
        #### Findings
        The data shows significant gaps in environmental disclosure, with inconsistent reporting across companies and industries.
        
        #### Recommendations
        - **Standardize Environmental Philanthropy Reporting**: Develop consistent reporting frameworks that all publicly traded companies must follow
        - **Mandate Giving Transparency**: Require detailed disclosure of environmental charitable giving, including recipient information and purpose
        - **Require Impact Assessment**: Companies should report the intended and actual impact of their environmental philanthropy
        
        #### Implementation
        - Update SEC filing requirements to include standardized environmental philanthropy sections
        - Develop reporting templates with clear metrics and definitions
        - Enforce compliance through existing regulatory mechanisms
        """)
    
    with st.expander("2. Geographic Equity in Environmental Funding"):
        # Check if we have geographic data
        has_geo_data = False
        for col in ['state', 'State', 'region', 'Region']:
            if col in df.columns:
                has_geo_data = True
                break
        
        if has_geo_data:
            # Display a map or chart showing geographic disparities if possible
            state_col = 'state' if 'state' in df.columns else 'State'
            giving_col = next((col for col in ['env_giving_millions', 'Charitable Contributions'] if col in df.columns), None)
            
            if state_col in df.columns and giving_col in df.columns:
                # Aggregate by state
                state_giving = df.groupby(state_col)[giving_col].sum().reset_index()
                state_giving.columns = ['State', 'Total Giving']
                
                # Sort by giving
                state_giving = state_giving.sort_values('Total Giving', ascending=False)
                
                # Show top and bottom states
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### States with Highest Giving")
                    st.dataframe(
                        state_giving.head(5),
                        column_config={
                            'State': st.column_config.TextColumn('State'),
                            'Total Giving': st.column_config.NumberColumn('Total Giving ($M)', format="$%.2f M")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("#### States with Lowest Giving")
                    st.dataframe(
                        state_giving.tail(5),
                        column_config={
                            'State': st.column_config.TextColumn('State'),
                            'Total Giving': st.column_config.NumberColumn('Total Giving ($M)', format="$%.2f M")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
        
        st.markdown("""
        #### Findings
        Environmental philanthropic giving is unevenly distributed geographically, with certain regions receiving disproportionately more funding than others.
        
        #### Recommendations
        - **Geographic Targeting Incentives**: Create tax or regulatory incentives for environmental giving in underserved areas
        - **Regional Equity Requirements**: For large corporations, require a minimum percentage of environmental giving to support communities where they operate
        - **Environmental Justice Focus**: Prioritize funding for areas facing significant environmental challenges or historical disinvestment
        
        #### Implementation
        - Develop a geographic equity index to identify underserved areas
        - Create regulatory frameworks that reward geographically balanced giving
        - Establish minimum local giving requirements for companies with national operations
        """)
    
    with st.expander("3. Industry-Specific Standards"):
        # Check if we have industry data
        has_industry_data = False
        for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
            if col in df.columns:
                has_industry_data = True
                industry_col = col
                break
        
        if has_industry_data:
            # Display average giving by industry
            giving_col = next((col for col in ['env_giving_millions', 'Charitable Contributions'] if col in df.columns), None)
            
            if giving_col:
                # Calculate average giving by industry
                industry_giving = df.groupby(industry_col)[giving_col].mean().reset_index()
                industry_giving.columns = ['Industry', 'Average Giving']
                
                # Sort by average giving
                industry_giving = industry_giving.sort_values('Average Giving', ascending=False)
                
                # Show bar chart
                fig = px.bar(
                    industry_giving.head(10),
                    x='Average Giving',
                    y='Industry',
                    orientation='h',
                    title='Top 10 Industries by Average Environmental Giving'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        #### Findings
        There are significant disparities in environmental giving between industries, with some high-impact industries showing disproportionately low giving relative to their environmental footprint.
        
        #### Recommendations
        - **Industry-Specific Benchmarks**: Develop giving standards based on environmental impact by industry
        - **Progressive Giving Expectations**: Set higher giving expectations for industries with larger environmental footprints
        - **Sector-Specific Reporting Requirements**: Customize disclosure requirements to address industry-specific environmental challenges
        
        #### Implementation
        - Collaborate with industry associations to develop appropriate standards
        - Create industry-specific guidelines with minimum giving thresholds based on revenue and environmental impact
        - Implement phased approaches for industries transitioning to higher standards
        """)
    
    with st.expander("4. Tax and Regulatory Incentives"):
        st.markdown("""
        #### Findings
        Current incentive structures may not adequately encourage strategic environmental philanthropy aligned with pressing environmental challenges.
        
        #### Recommendations
        - **Enhanced Tax Benefits**: Provide additional tax incentives for environmental giving above industry benchmarks
        - **Impact-Based Incentives**: Create graduated benefits based on demonstrated environmental impact, not just giving amount
        - **Regulatory Recognition**: Develop programs that recognize and reward exemplary corporate environmental philanthropy
        
        #### Implementation
        - Modify tax codes to provide higher deduction rates for strategic environmental giving
        - Create regulatory recognition programs with tangible benefits for top performers
        - Establish third-party verification mechanisms to validate impact claims
        """)

def display_corporate_improvements(df):
    """Display corporate improvement recommendations"""
    st.markdown("""
    ### Corporate Improvement Roadmap
    
    Companies can use these recommendations to enhance their environmental philanthropy strategies:
    """)
    
    # Create a visual roadmap using tabs for different maturity levels
    roadmap_tab1, roadmap_tab2, roadmap_tab3 = st.tabs([
        "🔴 Beginning", 
        "🟠 Developing", 
        "🟢 Leading"
    ])
    
    with roadmap_tab1:
        st.markdown("""
        ## Beginning Level
        
        ### Current State
        - Minimal or ad-hoc environmental giving
        - Limited transparency and reporting
        - No clear connection between business operations and philanthropy
        
        ### Improvement Steps
        
        #### 1. Establish a Baseline
        - Conduct an inventory of current environmental giving
        - Benchmark against industry peers
        - Assess alignment with business operations and impact
        
        #### 2. Develop a Basic Strategy
        - Define clear goals and focus areas for environmental giving
        - Establish a consistent budget allocation process
        - Create simple metrics to track giving and basic outcomes
        
        #### 3. Improve Transparency
        - Publish basic information about environmental philanthropy
        - Include environmental giving in sustainability reports
        - Share success stories and partnerships
        """)
    
    with roadmap_tab2:
        st.markdown("""
        ## Developing Level
        
        ### Current State
        - Established environmental giving program
        - Regular reporting with some metrics
        - Partial alignment with business strategy
        
        ### Improvement Steps
        
        #### 1. Enhance Strategic Alignment
        - Connect environmental giving to material environmental impacts
        - Develop a theory of change for philanthropic initiatives
        - Align giving with company expertise and capabilities
        
        #### 2. Improve Measurement
        - Implement robust tracking of environmental outcomes
        - Develop impact indicators for major initiatives
        - Gather feedback from beneficiaries and partners
        
        #### 3. Expand Transparency
        - Create detailed environmental giving reports
        - Share both successes and challenges
        - Provide context on giving relative to environmental footprint
        """)
    
    with roadmap_tab3:
        st.markdown("""
        ## Leading Level
        
        ### Current State
        - Strategic environmental philanthropy program
        - Comprehensive impact measurement
        - High transparency and stakeholder engagement
        
        ### Improvement Steps
        
        #### 1. Maximize Strategic Impact
        - Integrate philanthropy with other environmental initiatives
        - Focus on systemic change and leverage points
        - Develop innovative funding models (e.g., catalytic capital, impact investing)
        
        #### 2. Advanced Measurement and Evaluation
        - Implement rigorous impact evaluation methodologies
        - Track long-term outcomes and ecosystem effects
        - Use data analytics to optimize giving strategies
        
        #### 3. Collaborative Leadership
        - Lead industry collaborations and collective impact initiatives
        - Share best practices and tools with peers
        - Advocate for improved standards and policies
        """)
    
    # Self-assessment tool
    with st.expander("Corporate Self-Assessment Tool"):
        st.markdown("""
        ### Evaluate Your Company's Environmental Philanthropy
        
        Use this simple assessment to gauge your company's current state and identify improvement opportunities.
        """)
        
        # Create assessment questions
        st.markdown("#### Strategy and Alignment")
        strategy_score = st.select_slider(
            "How strategically aligned is your environmental giving with your business operations and impacts?",
            options=["Not aligned", "Somewhat aligned", "Moderately aligned", "Well aligned", "Perfectly aligned"],
            value="Moderately aligned"
        )
        
        st.markdown("#### Measurement and Reporting")
        measurement_score = st.select_slider(
            "How comprehensive is your measurement and reporting of environmental philanthropy?",
            options=["Minimal/none", "Basic metrics", "Regular reporting", "Detailed impact metrics", "Comprehensive evaluation"],
            value="Regular reporting"
        )
        
        st.markdown("#### Geographic Distribution")
        geographic_score = st.select_slider(
            "How well distributed is your environmental giving across your operational footprint?",
            options=["Highly concentrated", "Somewhat concentrated", "Moderately distributed", "Well distributed", "Optimally distributed"],
            value="Moderately distributed"
        )
        
        st.markdown("#### Stakeholder Engagement")
        engagement_score = st.select_slider(
            "How effectively do you engage stakeholders in your environmental philanthropy?",
            options=["Minimal engagement", "Limited engagement", "Moderate engagement", "Substantial engagement", "Comprehensive engagement"],
            value="Moderate engagement"
        )
        
        # Calculate assessment results
        score_mapping = {
            "Not aligned": 1, "Somewhat aligned": 2, "Moderately aligned": 3, "Well aligned": 4, "Perfectly aligned": 5,
            "Minimal/none": 1, "Basic metrics": 2, "Regular reporting": 3, "Detailed impact metrics": 4, "Comprehensive evaluation": 5,
            "Highly concentrated": 1, "Somewhat concentrated": 2, "Moderately distributed": 3, "Well distributed": 4, "Optimally distributed": 5,
            "Minimal engagement": 1, "Limited engagement": 2, "Moderate engagement": 3, "Substantial engagement": 4, "Comprehensive engagement": 5
        }
        
        total_score = score_mapping[strategy_score] + score_mapping[measurement_score] + score_mapping[geographic_score] + score_mapping[engagement_score]
        avg_score = total_score / 4
        
        if avg_score < 2:
            maturity_level = "Beginning"
            color = "🔴"
        elif avg_score < 4:
            maturity_level = "Developing"
            color = "🟠"
        else:
            maturity_level = "Leading"
            color = "🟢"
        
        st.markdown(f"### Assessment Result: {color} {maturity_level} Level")
        st.progress(avg_score / 5)
        st.markdown(f"Score: {total_score}/20 (Average: {avg_score:.1f}/5)")
        
        st.markdown("### Key Recommendations Based on Your Assessment")
        
        if score_mapping[strategy_score] < 3:
            st.markdown("• **Improve Strategy**: Develop a more coherent environmental giving strategy aligned with your core business")
        
        if score_mapping[measurement_score] < 3:
            st.markdown("• **Enhance Measurement**: Implement more robust tracking and reporting of environmental philanthropy")
        
        if score_mapping[geographic_score] < 3:
            st.markdown("• **Broaden Distribution**: Expand giving to more locations where you operate or have environmental impacts")
        
        if score_mapping[engagement_score] < 3:
            st.markdown("• **Increase Engagement**: Develop stronger relationships with environmental stakeholders and beneficiaries")

def display_community_advocacy(df):
    """Display community advocacy recommendations"""
    st.markdown("""
    ### Community Advocacy Toolkit
    
    Community organizations and advocates can use these tools and strategies to encourage more effective corporate environmental philanthropy:
    """)
    
    # Create expandable sections for different advocacy areas
    with st.expander("1. Corporate Accountability Strategies", expanded=True):
        st.markdown("""
        #### Finding Corporate Information
        - Use this dashboard to identify companies' environmental giving practices
        - Search SEC filings and corporate sustainability reports
        - Check environmental nonprofits' annual reports for corporate donors
        
        #### Evaluating Corporate Performance
        - Compare companies against industry benchmarks
        - Assess giving relative to environmental impact
        - Look for alignment between public statements and actual giving
        
        #### Accountability Tactics
        - Publish scorecards and rankings of corporate environmental giving
        - Engage companies through shareholder advocacy
        - Use social media to highlight leaders and laggards
        - Partner with responsible companies to establish best practices
        """)
    
    with st.expander("2. Local Giving Gap Analysis"):
        # Check if we have geographic data
        has_geo_data = False
        for col in ['state', 'State', 'region', 'Region']:
            if col in df.columns:
                has_geo_data = True
                state_col = col
                break
        
        if has_geo_data and 'local_giving_pct' in df.columns:
            # Display average local giving percentage
            avg_local = df['local_giving_pct'].mean()
            
            # Create a gauge chart for local giving
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = avg_local,
                title = {'text': "Average % of Giving That Stays Local"},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgray"},
                        {'range': [25, 50], 'color': "gray"},
                        {'range': [50, 75], 'color': "lightblue"},
                        {'range': [75, 100], 'color': "royalblue"},
                    ]
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        #### Identifying Local Giving Gaps
        - Research which companies operate in your community
        - Compare their local environmental giving to their environmental impact
        - Identify discrepancies between national giving and local support
        
        #### Developing Community-Specific Asks
        - Document local environmental needs and opportunities
        - Create specific, actionable funding proposals
        - Align requests with companies' stated environmental priorities
        
        #### Building Local Coalitions
        - Partner with other community organizations
        - Engage local government officials
        - Develop relationships with company representatives
        - Create unified messaging about community environmental needs
        """)
    
    with st.expander("3. Media and Communication Tools"):
        st.markdown("""
        #### Framing the Narrative
        - Highlight the connection between corporate operations and local environmental challenges
        - Tell compelling stories about community environmental needs
        - Emphasize shared benefit of increased environmental giving
        
        #### Media Strategies
        - Develop press releases comparing corporate giving to environmental impact
        - Create shareable social media content about corporate responsibility
        - Pitch stories to local and industry media outlets
        - Recognize and celebrate corporate environmental leaders
        
        #### Communication Templates
        - Company research briefing format
        - Sample press release on corporate environmental giving
        - Social media template for highlighting local giving gaps
        - Template letter to corporate leadership
        """)
    
    with st.expander("4. Policy Advocacy Approaches"):
        st.markdown("""
        #### Local Policy Opportunities
        - Advocate for local transparency requirements
        - Support community benefits agreements with environmental provisions
        - Promote tax incentives for local environmental giving
        
        #### State and Federal Policy
        - Push for enhanced environmental disclosure requirements
        - Advocate for geographic equity in environmental philanthropy
        - Support tax policies that incentivize strategic environmental giving
        
        #### Building Policy Coalitions
        - Partner with environmental justice organizations
        - Engage business leaders who support improved standards
        - Collaborate with academic institutions on policy research
        - Create multi-stakeholder coalitions for policy change
        """)

def display_data_improvements(df):
    """Display data improvement recommendations"""
    st.markdown("""
    ### Data Improvement Recommendations
    
    To enhance the quality and usefulness of corporate environmental philanthropy data, we recommend the following improvements:
    """)
    
    # Calculate missing data percentages
    missing_data = {}
    
    # Check for key columns
    key_columns = [
        'environmental_impact_score', 'emissions_tons', 'env_giving_millions',
        'Charitable Contributions', 'transparency_score', 'reporting_level',
        'env_loss_contingencies_millions', 'env_remediation_expenses_millions'
    ]
    
    for col in key_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            missing_data[col] = {'count': missing_count, 'percentage': missing_pct}
    
    if missing_data:
        # Create a bar chart of missing percentages
        missing_df = pd.DataFrame({
            'Metric': [col.replace('_', ' ').title() for col in missing_data.keys()],
            'Missing Percentage': [data['percentage'] for data in missing_data.values()]
        })
        
        missing_df = missing_df.sort_values('Missing Percentage', ascending=False)
        
        # Display the chart
        fig = px.bar(
            missing_df,
            x='Missing Percentage',
            y='Metric',
            orientation='h',
            title='Missing Data by Metric',
            color='Missing Percentage',
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Create expandable sections for different data improvement areas
    with st.expander("1. Data Collection Improvements", expanded=True):
        st.markdown("""
        #### Current Data Gaps
        - Inconsistent reporting of environmental giving details
        - Limited information on recipients and intended impact
        - Incomplete geographic distribution data
        - Inadequate connection between giving and environmental footprint
        
        #### Collection Recommendations
        - Implement standardized reporting templates
        - Develop clear definitions for environmental giving categories
        - Create consistent timeline and frequency for data submissions
        - Establish validation mechanisms for reported data
        """)
    
    with st.expander("2. Data Quality Enhancements"):
        st.markdown("""
        #### Current Quality Issues
        - Variations in how companies categorize environmental giving
        - Inconsistent metrics for reporting environmental impact
        - Limited third-party verification of reported information
        - Incomplete historical data making trend analysis difficult
        
        #### Quality Recommendations
        - Establish clear data quality standards and definitions
        - Implement automated validation checks
        - Require third-party verification for key metrics
        - Create incentives for high-quality, complete reporting
        - Develop methodologies for estimating missing data
        """)
    
    with st.expander("3. Additional Data Points"):
        st.markdown("""
        #### High-Value Additional Metrics
        - Detailed recipient information for environmental grants
        - Specific environmental outcomes and impacts
        - Connection between giving and company's material environmental issues
        - Geographic distribution at county or community level
        - Environmental justice dimensions of giving
        
        #### Implementation Approaches
        - Phased introduction of new reporting requirements
        - Pilot programs with industry leaders
        - Partnerships with nonprofit recipients for outcome reporting
        - Integration with existing ESG reporting frameworks
        - Development of impact measurement guidelines
        """)
    
    with st.expander("4. Data Access and Usability"):
        st.markdown("""
        #### Current Access Limitations
        - Dispersed data across multiple sources
        - Inconsistent formats making analysis difficult
        - Limited machine-readable data
        - Restricted access to detailed information
        
        #### Usability Recommendations
        - Create centralized repository for environmental philanthropy data
        - Implement standardized data formats and taxonomies
        - Develop APIs for programmatic data access
        - Provide open access to aggregated datasets
        - Create user-friendly tools for stakeholders to analyze data
        """)