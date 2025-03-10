"""
modules/data_generator.py
Provides functions to generate synthetic data for the SEED dashboard
when actual data is not available.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Store additional dataframes in a dictionary instead of attaching them to pandas DataFrames
additional_dataframes = {}

def get_additional_dataframe(key):
    """
    Get an additional dataframe by key
    
    Args:
        key (str): Key for the additional dataframe
        
    Returns:
        pandas.DataFrame or None: The additional dataframe, or None if not found
    """
    return additional_dataframes.get(key, None)

def generate_geographic_data(company_df=None):
    """
    Generate aggregated geographic data for regional analysis
    
    Args:
        company_df (pandas.DataFrame, optional): Company data to derive geographic stats
        
    Returns:
        pandas.DataFrame: Geographic data by state
    """
    # If company data is provided, use it to derive geographic stats
    if isinstance(company_df, pd.DataFrame) and 'state' in company_df.columns:
        # Group by state
        geo_data = company_df.groupby(['state', 'state_name', 'region']).agg({
            'company_id' if 'company_id' in company_df.columns else 'Name': 'count',
            'env_giving_millions' if 'env_giving_millions' in company_df.columns else 'Charitable Contributions': 'sum',
            'transparency_score': 'mean',
            'environmental_impact_score': 'mean',
            'incident_count': 'sum',
            'esg_score': 'mean',
            'local_giving_millions': 'sum',
            'national_giving_millions': 'sum'
        }).reset_index()
        
        # Rename columns
        geo_data.rename(columns={
            'company_id': 'num_companies',
            'transparency_score': 'avg_transparency_score',
            'environmental_impact_score': 'avg_environmental_impact',
            'esg_score': 'avg_esg_score'
        }, inplace=True)
        
        # Calculate derived metrics
        geo_data['avg_giving_per_company'] = geo_data['env_giving_millions'] / geo_data['num_companies']
        geo_data['local_giving_pct'] = (geo_data['local_giving_millions'] / geo_data['env_giving_millions']) * 100
        
        if 'revenue_millions' in company_df.columns:
            # Calculate total revenue by state
            state_revenue = company_df.groupby('state')['revenue_millions'].sum().reset_index()
            geo_data = pd.merge(geo_data, state_revenue, on='state')
            
            # Calculate giving as percentage of revenue
            geo_data['giving_pct_of_revenue'] = (geo_data['env_giving_millions'] / geo_data['revenue_millions']) * 100
        
        # Add state abbreviations
        geo_data['state_abbr'] = geo_data['state']
        
        # Calculate incident density (incidents per company)
        geo_data['incident_density'] = geo_data['incident_count'] / geo_data['num_companies']
        
        # Calculate "giving efficiency" - ratio of giving to environmental impact
        geo_data['giving_to_impact_ratio'] = geo_data['env_giving_millions'] / (geo_data['avg_environmental_impact'] * geo_data['num_companies'] / 100)
        
        # Generate environmental justice metrics by state
        if 'incident_df' in additional_dataframes:
            incident_df = additional_dataframes['incident_df']
            if 'in_environmental_justice_community' in incident_df.columns:
                # Calculate incidents in EJ communities by state
                ej_incidents = incident_df[incident_df['in_environmental_justice_community']].groupby('state').size().reset_index()
                ej_incidents.columns = ['state', 'ej_incident_count']
                
                # Merge with geo_data
                geo_data = pd.merge(geo_data, ej_incidents, on='state', how='left')
                geo_data['ej_incident_count'] = geo_data['ej_incident_count'].fillna(0)
                
                # Calculate percentage of incidents in EJ communities
                geo_data['ej_incident_pct'] = (geo_data['ej_incident_count'] / geo_data['incident_count']) * 100
                geo_data['ej_incident_pct'] = geo_data['ej_incident_pct'].fillna(0)
        
        return geo_data
    
    # If no company data, generate from scratch
    states = {
        'CA': {'name': 'California', 'weight': 0.12, 'region': 'West'},
        'TX': {'name': 'Texas', 'weight': 0.09, 'region': 'South'},
        'NY': {'name': 'New York', 'weight': 0.06, 'region': 'Northeast'},
        'FL': {'name': 'Florida', 'weight': 0.07, 'region': 'South'},
        'IL': {'name': 'Illinois', 'weight': 0.04, 'region': 'Midwest'},
        'PA': {'name': 'Pennsylvania', 'weight': 0.04, 'region': 'Northeast'},
        'OH': {'name': 'Ohio', 'weight': 0.035, 'region': 'Midwest'},
        'GA': {'name': 'Georgia', 'weight': 0.035, 'region': 'South'},
        'NC': {'name': 'North Carolina', 'weight': 0.03, 'region': 'South'},
        'MI': {'name': 'Michigan', 'weight': 0.03, 'region': 'Midwest'},
        'NJ': {'name': 'New Jersey', 'weight': 0.025, 'region': 'Northeast'},
        'VA': {'name': 'Virginia', 'weight': 0.025, 'region': 'South'},
        'WA': {'name': 'Washington', 'weight': 0.025, 'region': 'West'},
        'AZ': {'name': 'Arizona', 'weight': 0.025, 'region': 'West'},
        'MA': {'name': 'Massachusetts', 'weight': 0.02, 'region': 'Northeast'},
        'TN': {'name': 'Tennessee', 'weight': 0.02, 'region': 'South'},
        'IN': {'name': 'Indiana', 'weight': 0.02, 'region': 'Midwest'},
        'MO': {'name': 'Missouri', 'weight': 0.018, 'region': 'Midwest'},
        'MD': {'name': 'Maryland', 'weight': 0.018, 'region': 'South'},
        'WI': {'name': 'Wisconsin', 'weight': 0.018, 'region': 'Midwest'},
        'CO': {'name': 'Colorado', 'weight': 0.018, 'region': 'West'},
        'MN': {'name': 'Minnesota', 'weight': 0.017, 'region': 'Midwest'},
        'SC': {'name': 'South Carolina', 'weight': 0.015, 'region': 'South'},
        'AL': {'name': 'Alabama', 'weight': 0.015, 'region': 'South'},
        'LA': {'name': 'Louisiana', 'weight': 0.014, 'region': 'South'},
        'KY': {'name': 'Kentucky', 'weight': 0.013, 'region': 'South'},
        'OR': {'name': 'Oregon', 'weight': 0.013, 'region': 'West'},
        'OK': {'name': 'Oklahoma', 'weight': 0.012, 'region': 'South'},
        'CT': {'name': 'Connecticut', 'weight': 0.011, 'region': 'Northeast'},
        'UT': {'name': 'Utah', 'weight': 0.01, 'region': 'West'},
        'IA': {'name': 'Iowa', 'weight': 0.01, 'region': 'Midwest'},
        'NV': {'name': 'Nevada', 'weight': 0.01, 'region': 'West'},
        'AR': {'name': 'Arkansas', 'weight': 0.009, 'region': 'South'},
        'MS': {'name': 'Mississippi', 'weight': 0.009, 'region': 'South'},
        'KS': {'name': 'Kansas', 'weight': 0.009, 'region': 'Midwest'},
        'NM': {'name': 'New Mexico', 'weight': 0.007, 'region': 'West'},
        'NE': {'name': 'Nebraska', 'weight': 0.006, 'region': 'Midwest'},
        'ID': {'name': 'Idaho', 'weight': 0.006, 'region': 'West'},
        'WV': {'name': 'West Virginia', 'weight': 0.005, 'region': 'South'},
        'HI': {'name': 'Hawaii', 'weight': 0.004, 'region': 'West'},
        'NH': {'name': 'New Hampshire', 'weight': 0.004, 'region': 'Northeast'},
        'ME': {'name': 'Maine', 'weight': 0.004, 'region': 'Northeast'},
        'MT': {'name': 'Montana', 'weight': 0.003, 'region': 'West'},
        'RI': {'name': 'Rhode Island', 'weight': 0.003, 'region': 'Northeast'},
        'DE': {'name': 'Delaware', 'weight': 0.003, 'region': 'South'},
        'SD': {'name': 'South Dakota', 'weight': 0.003, 'region': 'Midwest'},
        'ND': {'name': 'North Dakota', 'weight': 0.002, 'region': 'Midwest'},
        'AK': {'name': 'Alaska', 'weight': 0.002, 'region': 'West'},
        'VT': {'name': 'Vermont', 'weight': 0.002, 'region': 'Northeast'},
        'WY': {'name': 'Wyoming', 'weight': 0.002, 'region': 'West'},
        'DC': {'name': 'District of Columbia', 'weight': 0.001, 'region': 'South'}
    }
    
    # Create state data with corporate presence and environmental giving
    state_data = []
    total_companies = 7406  # A realistic number from your document
    
    for state_abbr, info in states.items():
        # Number of companies based on state weight with some variation
        num_companies = int(total_companies * info['weight'] * np.random.uniform(0.85, 1.15))
        
        # Base giving varies by region to create interesting patterns
        region_factor = {
            'West': 1.2,       # West Coast tends to give more
            'Northeast': 1.1,   # Northeast also gives more
            'Midwest': 0.9,    # Midwest gives slightly less
            'South': 0.8       # South gives less on average
        }
        
        # Calculate environmental giving with regional differences
        # and some randomness for variation
        base_giving = num_companies * 2.5  # Average $2.5M per company
        regional_giving = base_giving * region_factor[info['region']]
        env_giving = regional_giving * np.random.uniform(0.7, 1.3)
        
        # Generate local vs national giving split
        local_giving_pct = np.random.beta(2, 3) * 100  # Beta distribution, favoring lower values
        local_giving = env_giving * (local_giving_pct / 100)
        national_giving = env_giving - local_giving
        
        # Average giving per company in this state
        avg_giving_per_company = env_giving / num_companies if num_companies > 0 else 0
        
        # Calculate transparency score
        if info['region'] == 'West':
            transparency = np.random.uniform(60, 85)
        elif info['region'] == 'Northeast':
            transparency = np.random.uniform(55, 80)
        elif info['region'] == 'Midwest':
            transparency = np.random.uniform(45, 70)
        else:  # South
            transparency = np.random.uniform(40, 65)
        
        # Calculate environmental impact score
        if info['region'] == 'West':
            env_impact = np.random.uniform(40, 65)  # Lower impact
        elif info['region'] == 'Northeast':
            env_impact = np.random.uniform(45, 70)
        elif info['region'] == 'Midwest':
            env_impact = np.random.uniform(50, 75)
        else:  # South
            env_impact = np.random.uniform(55, 80)  # Higher impact
        
        # Regional differences in giving as % of revenue
        if info['region'] == 'West':
            giving_pct = np.random.uniform(0.08, 0.15)
        elif info['region'] == 'Northeast':
            giving_pct = np.random.uniform(0.06, 0.12)
        elif info['region'] == 'Midwest':
            giving_pct = np.random.uniform(0.05, 0.1)
        else:  # South
            giving_pct = np.random.uniform(0.04, 0.09)
        
        # Calculate incident count - related to environmental impact
        incident_count = int(env_impact * num_companies / 1000)
        
        # Calculate ESG score based on transparency, impact, and giving
        esg_score = (
            transparency * 0.4 +            # 40% weight on transparency
            (100 - env_impact) * 0.3 +      # 30% weight on environmental impact (less is better)
            (giving_pct * 100) * 0.3        # 30% weight on giving percentage
        )
        
        # Calculate incidents in environmental justice communities
        ej_incident_count = int(incident_count * np.random.uniform(0.3, 0.7))
        ej_incident_pct = (ej_incident_count / incident_count * 100) if incident_count > 0 else 0
        
        # Calculate giving efficiency
        giving_to_impact_ratio = env_giving / (env_impact * num_companies / 100)
        
        state_data.append({
            'state': state_abbr,
            'state_name': info['name'],
            'state_abbr': state_abbr,
            'region': info['region'],
            'num_companies': num_companies,
            'env_giving_millions': round(env_giving, 2),
            'local_giving_millions': round(local_giving, 2),
            'national_giving_millions': round(national_giving, 2),
            'local_giving_pct': round(local_giving_pct, 2),
            'avg_giving_per_company': round(avg_giving_per_company, 2),
            'giving_pct_of_revenue': giving_pct,
            'avg_transparency_score': transparency,
            'avg_environmental_impact': env_impact,
            'incident_count': incident_count,
            'ej_incident_count': ej_incident_count,
            'ej_incident_pct': ej_incident_pct,
            'avg_esg_score': esg_score,
            'giving_to_impact_ratio': giving_to_impact_ratio
        })
    
    return pd.DataFrame(state_data)

def generate_historical_data(df):
    """
    Generate historical data for time series analysis
    
    Args:
        df (pandas.DataFrame): Company data
        
    Returns:
        dict: Dictionary containing historical dataframes
    """
    # Generate historical transparency scores (years 2020-2024)
    years = list(range(2020, datetime.now().year + 1))
    
    # Store year-by-year scores
    historical_scores = []
    
    for _, row in df.iterrows():
        company_id = row['company_id']
        industry = row['industry']
        current_score = row['transparency_score']
        
        # Generate historical scores (generally improving over time)
        for year in years:
            # Earlier years had lower scores
            year_factor = (year - 2019) * 0.05  # 5% improvement per year
            historical_score = current_score * (1 - year_factor) + np.random.normal(0, 5)
            historical_score = max(0, min(100, historical_score))
            
            # Add historical reporting level
            if historical_score < 20:
                historical_reporting_level = 'Minimal'
            elif historical_score < 40:
                historical_reporting_level = 'Basic'
            elif historical_score < 60:
                historical_reporting_level = 'Standard'
            elif historical_score < 80:
                historical_reporting_level = 'Detailed'
            else:
                historical_reporting_level = 'Comprehensive'
            
            historical_scores.append({
                'company_id': company_id,
                'company_name': row['company_name'],
                'industry': industry,
                'year': year,
                'transparency_score': historical_score,
                'reporting_level': historical_reporting_level
            })
    
    # Create transparency history dataframe
    transparency_history = pd.DataFrame(historical_scores)
    
    # Generate historical giving data
    historical_giving = []
    
    for _, row in df.iterrows():
        company_id = row['company_id']
        current_giving = row['env_giving_millions']
        current_revenue = row['revenue_millions']
        
        # Generate giving trend (generally increasing)
        for year in years:
            # Earlier years had lower giving
            year_factor = 1 - ((year - 2019) * 0.07)  # 7% less per year going back
            historical_giving_value = current_giving * year_factor * np.random.uniform(0.9, 1.1)
            
            # Also generate historical revenue (similar trend but less volatile)
            historical_revenue = current_revenue * (1 - ((year - 2019) * 0.04)) * np.random.uniform(0.95, 1.05)
            
            # Calculate giving as percentage of revenue
            if historical_revenue > 0:
                historical_giving_pct = (historical_giving_value / historical_revenue) * 100
            else:
                historical_giving_pct = 0
            
            historical_giving.append({
                'company_id': company_id,
                'company_name': row['company_name'],
                'industry': row['industry'],
                'year': year,
                'env_giving_millions': historical_giving_value,
                'revenue_millions': historical_revenue,
                'env_giving_pct': historical_giving_pct
            })
    
    # Create giving history dataframe
    giving_history = pd.DataFrame(historical_giving)
    
    # Generate historical environmental impact data
    historical_impact = []
    
    for _, row in df.iterrows():
        company_id = row['company_id']
        current_impact = row['environmental_impact_score']
        current_emissions = row['emissions_tons']
        current_remediation = row['env_remediation_expenses_millions']
        
        # Generate impact trend (slightly increasing)
        for year in years:
            # Earlier years had slightly lower impact
            year_factor = 1 - ((year - 2019) * 0.02)  # 2% less per year going back
            historical_impact_value = current_impact * year_factor * np.random.uniform(0.95, 1.05)
            
            # Generate historical emissions and remediation
            historical_emissions = current_emissions * year_factor * np.random.uniform(0.9, 1.1)
            historical_remediation = current_remediation * year_factor * np.random.uniform(0.85, 1.15)
            
            historical_impact.append({
                'company_id': company_id,
                'company_name': row['company_name'],
                'industry': row['industry'],
                'year': year,
                'environmental_impact_score': historical_impact_value,
                'emissions_tons': historical_emissions,
                'env_remediation_expenses_millions': historical_remediation
            })
    
    # Create impact history dataframe
    impact_history = pd.DataFrame(historical_impact)
    
    # Generate additional metrics for time series analysis
    
    # 1. Industry-level aggregations by year
    industry_yearly_transparency = transparency_history.groupby(['industry', 'year'])['transparency_score'].mean().reset_index()
    industry_yearly_transparency.rename(columns={'transparency_score': 'avg_transparency_score'}, inplace=True)
    
    industry_yearly_giving = giving_history.groupby(['industry', 'year'])['env_giving_millions'].sum().reset_index()
    industry_yearly_giving.rename(columns={'env_giving_millions': 'total_industry_giving_millions'}, inplace=True)
    
    industry_yearly_impact = impact_history.groupby(['industry', 'year'])['environmental_impact_score'].mean().reset_index()
    industry_yearly_impact.rename(columns={'environmental_impact_score': 'avg_environmental_impact'}, inplace=True)
    
    # Store these in the additional dataframes
    additional_dataframes['industry_yearly_transparency'] = industry_yearly_transparency
    additional_dataframes['industry_yearly_giving'] = industry_yearly_giving
    additional_dataframes['industry_yearly_impact'] = industry_yearly_impact
    
    # Return all historical dataframes in a dictionary
    return {
        'transparency_history': transparency_history,
        'giving_history': giving_history,
        'impact_history': impact_history
    }

def generate_incident_data(df):
    """
    Generate environmental incident data based on company data
    
    Args:
        df (pandas.DataFrame): Company data
        
    Returns:
        pandas.DataFrame: Incident data
    """
    incident_data = []
    
    for _, row in df.iterrows():
        if pd.notna(row['incident_count']) and row['incident_count'] > 0:
            for _ in range(int(row['incident_count'])):
                # Generate incident severity (1-5 scale)
                severity = np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.15, 0.1, 0.05])
                
                # Generate incident type based on industry
                if row['industry'] == 'Energy':
                    incident_types = ['Oil Spill', 'Gas Leak', 'Emissions Exceedance', 'Water Contamination', 'Permit Violation']
                    weights = [0.3, 0.25, 0.2, 0.15, 0.1]
                elif row['industry'] == 'Manufacturing' or row['industry'] == 'Chemical':
                    incident_types = ['Chemical Spill', 'Waste Disposal Violation', 'Emissions Exceedance', 'Water Contamination', 'Permit Violation']
                    weights = [0.3, 0.25, 0.2, 0.15, 0.1]
                elif row['industry'] == 'Transportation':
                    incident_types = ['Fuel Spill', 'Emissions Exceedance', 'Noise Violation', 'Waste Disposal Violation', 'Permit Violation']
                    weights = [0.3, 0.3, 0.2, 0.1, 0.1]
                else:
                    incident_types = ['Waste Disposal Violation', 'Permit Violation', 'Emissions Exceedance', 'Water Usage Violation', 'Material Spill']
                    weights = [0.25, 0.25, 0.2, 0.15, 0.15]
                
                incident_type = np.random.choice(incident_types, p=weights)
                
                # Generate random coordinates near the company's location
                latitude = row['latitude'] + np.random.normal(0, 0.5)
                longitude = row['longitude'] + np.random.normal(0, 0.5)
                
                # Keep lat/long within reasonable bounds
                latitude = max(25, min(49, latitude))
                longitude = max(-125, min(-65, longitude))
                
                # Generate incident date
                # More recent incidents are more likely
                days_ago = int(np.random.exponential(scale=365)) % 1825  # Up to 5 years ago
                incident_date = datetime.now() - timedelta(days=days_ago)
                
                # Create impact description based on severity and type
                impact_descriptions = {
                    1: "Minor incident with minimal environmental impact. Quickly contained and remediated.",
                    2: "Minor incident affecting a limited area. Required standard cleanup procedures.",
                    3: "Moderate incident with localized environmental effects. Required significant remediation.",
                    4: "Serious incident with substantial environmental impact. Extended remediation required.",
                    5: "Major incident with significant environmental damage. Long-term remediation ongoing."
                }
                
                # Generate location description
                county = f"{random.choice(['North', 'South', 'East', 'West', 'Central', 'Upper', 'Lower'])} {random.choice(['Ridge', 'Valley', 'Creek', 'River', 'Lake', 'Woods', 'Plains', 'Hills'])} County"
                
                # Calculate distance to nearest population center
                distance_to_population = np.random.lognormal(mean=1.5, sigma=1.0)  # in miles
                
                # Determine if the incident is in an environmental justice community
                # More severe incidents are more likely to be in EJ communities
                ej_probability = 0.2 + (severity * 0.1)  # 20-70% probability based on severity
                in_ej_community = np.random.random() < ej_probability
                
                # Flag for whether incident was disclosed promptly
                prompt_disclosure = np.random.random() < (0.9 - (severity * 0.1))  # Less severe more likely disclosed
                
                # Generate days until disclosure
                if prompt_disclosure:
                    disclosure_lag = np.random.randint(0, 5)  # 0-4 days
                else:
                    disclosure_lag = np.random.randint(5, 90)  # 5-89 days
                
                # Community impact rating (1-5)
                community_impact = min(5, severity + np.random.randint(-1, 2))  # Related to severity but not identical
                
                # Create incident record
                incident_data.append({
                    'company_id': row['company_id'],
                    'company_name': row['company_name'],
                    'state': row['state'],
                    'industry': row['industry'],
                    'incident_type': incident_type,
                    'severity': severity,
                    'latitude': latitude,
                    'longitude': longitude,
                    'date': incident_date,
                    'year': incident_date.year,
                    'impact_description': impact_descriptions[severity],
                    'remediation_cost_millions': severity * np.random.uniform(0.05, 0.2) * 
                                               (4.0 if row['size'].startswith('Very Large') else
                                                2.0 if row['size'].startswith('Large') else
                                                1.0 if row['size'].startswith('Medium') else 0.5),
                    'county': county,
                    'distance_to_population_miles': distance_to_population,
                    'in_environmental_justice_community': in_ej_community,
                    'prompt_disclosure': prompt_disclosure,
                    'disclosure_lag_days': disclosure_lag,
                    'community_impact_rating': community_impact
                })
    
    # Create dataframe of incidents
    if incident_data:
        incident_df = pd.DataFrame(incident_data)
    else:
        # Create empty dataframe with the right columns
        incident_df = pd.DataFrame(columns=[
            'company_id', 'company_name', 'state', 'industry', 'incident_type',
            'severity', 'latitude', 'longitude', 'date', 'year',
            'impact_description', 'remediation_cost_millions', 'county',
            'distance_to_population_miles', 'in_environmental_justice_community',
            'prompt_disclosure', 'disclosure_lag_days', 'community_impact_rating'
        ])
    
    return incident_df

def generate_marketing_data(df):
    """
    Generate marketing claims data for greenwashing analysis (#10)
    
    Args:
        df (pandas.DataFrame): Company data
        
    Returns:
        pandas.DataFrame: Marketing claims data
    """
    marketing_data = []
    
    for _, row in df.iterrows():
        # Extract base data
        company_id = row['company_id']
        company_name = row['company_name']
        industry = row['industry']
        env_giving = row['env_giving_millions']
        env_impact = row['environmental_impact_score']
        
        # Marketing claims intensity was already generated and stored in the main dataframe
        marketing_intensity = row['marketing_claims_intensity']
        
        # Generate specific types of claims
        claim_types = [
            "Carbon Neutrality/Net Zero",
            "Sustainable Products/Services",
            "Environmental Leadership",
            "Resource Conservation",
            "Responsible Supply Chain",
            "Eco-Friendly Practices"
        ]
        
        # For each company, generate 2-6 specific claims
        num_claims = np.random.randint(2, min(7, len(claim_types) + 1))
        selected_claim_types = np.random.choice(claim_types, size=num_claims, replace=False)
        
        for claim_type in selected_claim_types:
            # Generate claim specifics
            claim_intensity = marketing_intensity * np.random.uniform(0.7, 1.3)
            claim_intensity = min(100, max(0, claim_intensity))
            
            # Determine if the claim is substantiated
            base_substantiation = 100 - abs(marketing_intensity - (env_giving * 20))
            substantiation_score = min(100, max(0, base_substantiation * np.random.uniform(0.7, 1.3)))
            
            # Claim placement/channels
            channels = ["Corporate Website", "Annual Report", "Press Release", 
                       "Social Media", "Advertisement", "Product Packaging"]
            
            num_channels = np.random.randint(1, len(channels) + 1)
            selected_channels = ', '.join(np.random.choice(channels, size=num_channels, replace=False))
            
            # Date of claim (within past 2 years)
            days_ago = np.random.randint(0, 730)
            claim_date = datetime.now() - timedelta(days=days_ago)
            
            # Add claim to data
            marketing_data.append({
                'company_id': company_id,
                'company_name': company_name,
                'industry': industry,
                'claim_type': claim_type,
                'claim_intensity': claim_intensity,
                'substantiation_score': substantiation_score,
                'channels': selected_channels,
                'claim_date': claim_date,
                'greenwashing_risk': max(0, claim_intensity - substantiation_score)
            })
    
    return pd.DataFrame(marketing_data)


def generate_cause_area_summary(df):
    """
    Generate summary data for environmental cause areas (#7)
    
    Args:
        df (pandas.DataFrame): Company data
        
    Returns:
        pandas.DataFrame: Cause area summary data
    """
    # Extract cause area columns
    cause_columns = [col for col in df.columns if col.startswith('giving_') and 'pct' not in col and 'millions' not in col]
    
    if not cause_columns:
        # If no cause columns found, return empty dataframe
        return pd.DataFrame()
    
    # Prepare data for summary
    cause_data = []
    
    for cause_col in cause_columns:
        # Extract cause name from column name
        cause_name = cause_col.replace('giving_', '').replace('_', ' ').title()
        
        # Calculate total giving for this cause
        total_giving = df[cause_col].sum()
        
        # Count companies supporting this cause
        supporting_companies = df[df[cause_col] > 0].shape[0]
        
        # Calculate percentage of total environmental giving
        total_env_giving = df['env_giving_millions'].sum()
        percentage_of_total = (total_giving / total_env_giving) * 100 if total_env_giving > 0 else 0
        
        # Add to cause data
        cause_data.append({
            'cause_area': cause_name,
            'total_giving_millions': total_giving,
            'supporting_companies': supporting_companies,
            'percentage_of_total_giving': percentage_of_total
        })
    
    # Convert to dataframe
    cause_df = pd.DataFrame(cause_data)
    
    # Add industry-specific cause area data
    industry_cause_data = []
    
    for industry in df['industry'].unique():
        industry_df = df[df['industry'] == industry]
        
        for cause_col in cause_columns:
            cause_name = cause_col.replace('giving_', '').replace('_', ' ').title()
            industry_cause_giving = industry_df[cause_col].sum()
            
            if industry_cause_giving > 0:
                industry_cause_data.append({
                    'industry': industry,
                    'cause_area': cause_name,
                    'industry_giving_millions': industry_cause_giving
                })
    
    # Store industry cause data
    additional_dataframes['industry_cause_df'] = pd.DataFrame(industry_cause_data)
    
    return cause_df


def generate_corporate_data(num_companies=500):
    """
    Generate sample data for corporate players visualizations
    
    Args:
        num_companies (int): Number of companies to generate
        
    Returns:
        pandas.DataFrame: Synthetic corporate data
    """
    # Define data distributions
    states = {
        'CA': {'name': 'California', 'weight': 0.15, 'region': 'West'},
        'NY': {'name': 'New York', 'weight': 0.12, 'region': 'Northeast'},
        'TX': {'name': 'Texas', 'weight': 0.10, 'region': 'South'},
        'FL': {'name': 'Florida', 'weight': 0.08, 'region': 'South'},
        'IL': {'name': 'Illinois', 'weight': 0.07, 'region': 'Midwest'},
        'MA': {'name': 'Massachusetts', 'weight': 0.06, 'region': 'Northeast'},
        'WA': {'name': 'Washington', 'weight': 0.06, 'region': 'West'},
        'PA': {'name': 'Pennsylvania', 'weight': 0.05, 'region': 'Northeast'},
        'OH': {'name': 'Ohio', 'weight': 0.05, 'region': 'Midwest'},
        'GA': {'name': 'Georgia', 'weight': 0.05, 'region': 'South'},
        'MI': {'name': 'Michigan', 'weight': 0.05, 'region': 'Midwest'},
        'MN': {'name': 'Minnesota', 'weight': 0.04, 'region': 'Midwest'},
        'CO': {'name': 'Colorado', 'weight': 0.04, 'region': 'West'},
        'NC': {'name': 'North Carolina', 'weight': 0.04, 'region': 'South'},
        'NJ': {'name': 'New Jersey', 'weight': 0.04, 'region': 'Northeast'},
    }
    
    # Calculate normalized weights for state selection
    state_weights = np.array([state['weight'] for state in states.values()])
    state_weights = state_weights / state_weights.sum()
    state_abbrs = list(states.keys())
    
    industries = [
        {'name': 'Energy', 'weight': 0.11, 'env_impact': 'high', 'sic': '1311'},
        {'name': 'Technology', 'weight': 0.15, 'env_impact': 'low', 'sic': '7370'},
        {'name': 'Manufacturing', 'weight': 0.15, 'env_impact': 'high', 'sic': '3711'},
        {'name': 'Retail', 'weight': 0.10, 'env_impact': 'medium', 'sic': '5331'},
        {'name': 'Healthcare', 'weight': 0.10, 'env_impact': 'low', 'sic': '8000'},
        {'name': 'Financial Services', 'weight': 0.08, 'env_impact': 'low', 'sic': '6021'},
        {'name': 'Food & Beverage', 'weight': 0.08, 'env_impact': 'medium', 'sic': '2080'},
        {'name': 'Transportation', 'weight': 0.06, 'env_impact': 'high', 'sic': '4512'},
        {'name': 'Telecommunications', 'weight': 0.05, 'env_impact': 'low', 'sic': '4813'},
        {'name': 'Chemical', 'weight': 0.05, 'env_impact': 'high', 'sic': '2800'},
        {'name': 'Construction', 'weight': 0.07, 'env_impact': 'medium', 'sic': '1531'},
    ]
    
    # Calculate normalized weights for industry selection
    industry_weights = np.array([industry['weight'] for industry in industries])
    industry_weights = industry_weights / industry_weights.sum()
    
    sizes = [
        {'name': 'Small ($10M-$100M)', 'weight': 0.4, 'min_rev': 10, 'max_rev': 100, 'transparency_factor': 0.5},
        {'name': 'Medium ($100M-$1B)', 'weight': 0.3, 'min_rev': 100, 'max_rev': 1000, 'transparency_factor': 0.7},
        {'name': 'Large ($1B-$10B)', 'weight': 0.2, 'min_rev': 1000, 'max_rev': 10000, 'transparency_factor': 0.85},
        {'name': 'Very Large (>$10B)', 'weight': 0.1, 'min_rev': 10000, 'max_rev': 50000, 'transparency_factor': 0.95}
    ]
    
    # Calculate normalized weights for size selection
    size_weights = np.array([size['weight'] for size in sizes])
    size_weights = size_weights / size_weights.sum()
    
    # Company name prefixes and suffixes
    name_prefixes = ["Global", "American", "International", "National", "United", "Allied", 
                     "Pacific", "Atlantic", "Advanced", "Strategic", "Superior", "Prime", 
                     "Pinnacle", "Summit", "Elite", "Modern", "Capital", "Consolidated"]
    
    name_suffixes = ["Corp", "Inc", "Corporation", "Industries", "Group", "Partners", 
                     "Enterprises", "Holdings", "Solutions", "Systems", "Technologies", 
                     "Innovations", "Resources", "Associates", "International", "Worldwide"]
    
    industry_words = {
        "Energy": ["Energy", "Power", "Gas", "Oil", "Solar", "Renewables"],
        "Technology": ["Tech", "Digital", "Software", "Systems", "Computing", "Data"],
        "Manufacturing": ["Manufacturing", "Industrial", "Products", "Fabrication"],
        "Retail": ["Retail", "Stores", "Consumer", "Marketplace", "Shopping"],
        "Healthcare": ["Health", "Medical", "Care", "Wellness", "Pharmaceuticals"],
        "Financial Services": ["Financial", "Banking", "Investments", "Capital", "Credit"],
        "Food & Beverage": ["Foods", "Beverages", "Nutrition", "Dining"],
        "Transportation": ["Transport", "Logistics", "Shipping", "Freight", "Carriers"],
        "Telecommunications": ["Telecom", "Communications", "Network", "Wireless"],
        "Chemical": ["Chemical", "Materials", "Polymers", "Compounds"],
        "Construction": ["Construction", "Building", "Development", "Properties", "Structures"]
    }
    
    # Define environmental cause areas based on visualization suggestion #7
    environmental_causes = [
        "Climate Change Mitigation",
        "Renewable Energy",
        "Habitat Conservation",
        "Biodiversity Protection",
        "Ocean Conservation",
        "Water Resource Protection",
        "Sustainable Agriculture",
        "Environmental Justice",
        "Environmental Education",
        "Waste Reduction & Recycling",
        "Air Quality Improvement",
        "Sustainable Transportation"
    ]
    
    # Define reporting metrics for transparency rating (#11)
    transparency_metrics = [
        "Environmental Impact Disclosure",
        "Giving Strategy Documentation",
        "Goal Setting and Progress Tracking",
        "Third-Party Verification",
        "Stakeholder Engagement"
    ]
    
    # Define reporting levels
    reporting_levels = ['Minimal', 'Basic', 'Standard', 'Detailed', 'Comprehensive']
    
    # Create companies
    companies = []
    
    for i in range(num_companies):
        # Select state
        state_idx = np.random.choice(len(state_abbrs), p=state_weights)
        state = state_abbrs[state_idx]
        
        # Select industry
        industry_idx = np.random.choice(len(industries), p=industry_weights)
        industry = industries[industry_idx]
        
        # Select size
        size_idx = np.random.choice(len(sizes), p=size_weights)
        size = sizes[size_idx]
        
        # Generate revenue based on size
        revenue = np.random.uniform(size['min_rev'], size['max_rev'])
        
        # Environmental giving depends on industry, size, and some randomness
        # Higher impact industries tend to give proportionally more
        base_giving_pct = np.random.uniform(0.01, 0.5)
        
        if industry['env_impact'] == 'high':
            giving_factor = 1.5
        elif industry['env_impact'] == 'medium':
            giving_factor = 1.0
        else:
            giving_factor = 0.7
        
        # Size adjustment - larger companies give proportionally less
        if size['name'].startswith('Small'):
            size_giving_factor = 1.2
        elif size['name'].startswith('Medium'):
            size_giving_factor = 1.0
        elif size['name'].startswith('Large'):
            size_giving_factor = 0.8
        else:
            size_giving_factor = 0.6
        
        # Calculate giving percentage and amount
        env_giving_pct = base_giving_pct * giving_factor * size_giving_factor
        env_giving = revenue * (env_giving_pct / 100)
        
        # Generate a company name
        industry_name = industry['name']
        industry_word = np.random.choice(industry_words.get(industry_name, [""])) if industry_name in industry_words else ""
        
        if industry_word and np.random.random() < 0.7:
            # 70% chance to use industry-specific word in name
            company_name = f"{np.random.choice(name_prefixes)} {industry_word} {np.random.choice(name_suffixes)}"
        else:
            # 30% chance for a more generic name
            company_name = f"{np.random.choice(name_prefixes)} {np.random.choice(name_suffixes)}"
        
        # Add location data
        latitude = 37.0902 + np.random.normal(0, 3)  # Centered around US
        longitude = -95.7129 + np.random.normal(0, 5)
        
        # Generate random address
        street_number = np.random.randint(100, 9999)
        street_names = ["Main St", "Park Ave", "Broadway", "Market St", "Oak St", "Washington Ave", "5th Ave", "1st St"]
        street = f"{street_number} {np.random.choice(street_names)}"
        
        cities = {
            'CA': ['Los Angeles', 'San Francisco', 'San Diego', 'San Jose'],
            'NY': ['New York', 'Buffalo', 'Rochester', 'Syracuse'],
            'TX': ['Houston', 'Dallas', 'Austin', 'San Antonio'],
            'FL': ['Miami', 'Orlando', 'Tampa', 'Jacksonville'],
            'IL': ['Chicago', 'Springfield', 'Peoria', 'Rockford'],
            'MA': ['Boston', 'Cambridge', 'Worcester', 'Springfield'],
            'WA': ['Seattle', 'Tacoma', 'Spokane', 'Bellevue'],
            'PA': ['Philadelphia', 'Pittsburgh', 'Allentown', 'Erie'],
            'OH': ['Columbus', 'Cleveland', 'Cincinnati', 'Toledo'],
            'GA': ['Atlanta', 'Savannah', 'Augusta', 'Athens'],
            'MI': ['Detroit', 'Grand Rapids', 'Ann Arbor', 'Lansing'],
            'MN': ['Minneapolis', 'Saint Paul', 'Rochester', 'Duluth'],
            'CO': ['Denver', 'Colorado Springs', 'Boulder', 'Fort Collins'],
            'NC': ['Charlotte', 'Raleigh', 'Greensboro', 'Durham'],
            'NJ': ['Newark', 'Jersey City', 'Paterson', 'Atlantic City']
        }
        
        city = np.random.choice(cities.get(state, ['Unknown City']))
        
        # Generate transparency data
        transparency_score = np.random.normal(50, 15) * size['transparency_factor']
        transparency_score = max(0, min(100, transparency_score))
        
        if transparency_score < 20:
            reporting_level = 'Minimal'
        elif transparency_score < 40:
            reporting_level = 'Basic'
        elif transparency_score < 60:
            reporting_level = 'Standard'
        elif transparency_score < 80:
            reporting_level = 'Detailed'
        else:
            reporting_level = 'Comprehensive'
        
        # Add Detail level (for compatibility with original code)
        detail_level = 1 if reporting_level in ['Detailed', 'Comprehensive'] else 0
        
        # Generate transparency metrics scores (0-10 scale)
        transparency_metric_scores = {}
        for metric in transparency_metrics:
            # Base score aligned with overall transparency with some variation
            base_score = transparency_score / 10  # Convert 0-100 to 0-10
            variation = np.random.normal(0, 1)  # Add noise
            metric_score = max(0, min(10, base_score + variation))
            metric_key = f"score_{metric.lower().replace(' ', '_')}"
            transparency_metric_scores[metric_key] = metric_score
        
        # Environmental impact data
        # High impact industries have higher scores
        impact_base = np.random.gamma(shape=2.0, scale=10.0)
        
        if industry['env_impact'] == 'high':
            impact_factor = 3.0
        elif industry['env_impact'] == 'medium':
            impact_factor = 1.8
        else:
            impact_factor = 1.0
        
        # Larger companies have bigger environmental footprints
        if size['name'].startswith('Small'):
            size_impact_factor = 0.7
        elif size['name'].startswith('Medium'):
            size_impact_factor = 1.0
        elif size['name'].startswith('Large'):
            size_impact_factor = 2.0
        else:
            size_impact_factor = 4.0
        
        environmental_impact = impact_base * impact_factor * size_impact_factor
        environmental_impact = min(100, environmental_impact)  # Scale to 0-100
        
        # Calculate emissions (in tons of CO2 equivalent)
        emissions = environmental_impact * 1000 * np.random.uniform(0.8, 1.2)
        
        # Water usage (gallons)
        water_usage = environmental_impact * 5000 * np.random.uniform(0.7, 1.3)
        
        # Waste (tons)
        waste = environmental_impact * 100 * np.random.uniform(0.6, 1.4)
        
        # Energy consumption (MWh)
        energy = environmental_impact * 500 * np.random.uniform(0.75, 1.25)
        
        # Environmental loss contingencies (millions)
        env_loss_contingencies = environmental_impact * 0.5 * np.random.uniform(0.6, 1.4)
        
        # Environmental remediation expenses (millions)
        env_remediation = environmental_impact * 0.3 * np.random.uniform(0.7, 1.3)
        
        # Environmental incidents count
        incident_lambda = max(0.1, impact_factor - 1) * size_impact_factor * 0.5
        incident_count = np.random.poisson(incident_lambda)
        
        # ESG Score (0-100)
        esg_base = 60  # Average score
        esg_variation = 20  # Variation range
        
        # Factors affecting ESG
        # 1. High environmental giving increases score
        giving_effect = env_giving_pct * 10  # Scale to meaningful impact
        
        # 2. Low environmental impact increases score
        impact_effect = -environmental_impact * 0.1  # Negative effect from impact
        
        # 3. High transparency increases score
        transparency_effect = transparency_score * 0.2
        
        # Calculate ESG score with random component
        esg_score = esg_base + giving_effect + impact_effect + transparency_effect + np.random.normal(0, esg_variation/4)
        esg_score = max(0, min(100, esg_score))  # Constrain to 0-100
        
        # Generate cause area distribution
        cause_area_data = {}
        
        # Determine number of causes the company supports (larger companies support more causes)
        if size['name'].startswith('Small'):
            num_causes = np.random.randint(1, 4)
        elif size['name'].startswith('Medium'):
            num_causes = np.random.randint(2, 6)
        elif size['name'].startswith('Large'):
            num_causes = np.random.randint(3, 8)
        else:
            num_causes = np.random.randint(4, len(environmental_causes) + 1)
        
        num_causes = min(num_causes, len(environmental_causes))
        
        # Select causes randomly
        selected_causes = np.random.choice(environmental_causes, size=num_causes, replace=False)
        
        # Distribute the giving amount among the causes
        # Generate weights that sum to 1
        weights = np.random.dirichlet(np.ones(num_causes))
        
        for cause, weight in zip(selected_causes, weights):
            cause_area_data[f"giving_{cause.lower().replace(' ', '_')}"] = env_giving * weight
        
        # Generate local vs national/international giving data (for #20)
        local_giving_pct = np.random.beta(2, 3) * 100  # Beta distribution centered around 40%
        local_giving = env_giving * (local_giving_pct / 100)
        national_giving = env_giving - local_giving
        
        # Generate filing date (within past year)
        days_ago = np.random.randint(0, 365)
        filing_date = datetime.now() - timedelta(days=days_ago)
        
        # Add marketing claims indicator (for greenwashing analysis #10)
        marketing_claims_intensity = np.random.uniform(0, 100)  # 0-100 scale
        marketing_vs_giving_gap = marketing_claims_intensity - (env_giving_pct * 100)
        
        # Add to the list of companies
        company_data = {
            'company_id': i,
            'company_name': company_name,
            'state': state,
            'state_name': states[state]['name'],
            'region': states[state]['region'],
            'industry': industry['name'],
            'sic_code': industry['sic'],
            'size': size['name'],
            'revenue_millions': revenue,
            'env_giving_millions': env_giving,
            'env_giving_pct': env_giving_pct,
            'transparency_score': transparency_score,
            'reporting_level': reporting_level,
            'detail_level': detail_level,
            'address': street,
            'city': city,
            'latitude': latitude,
            'longitude': longitude,
            'environmental_impact_score': environmental_impact,
            'emissions_tons': emissions,
            'water_usage_gallons': water_usage,
            'waste_tons': waste,
            'energy_consumption_mwh': energy,
            'env_loss_contingencies_millions': env_loss_contingencies,
            'env_remediation_expenses_millions': env_remediation,
            'incident_count': incident_count,
            'esg_score': esg_score,
            'local_giving_pct': local_giving_pct,
            'local_giving_millions': local_giving,
            'national_giving_millions': national_giving,
            'date_of_filing': filing_date,
            'marketing_claims_intensity': marketing_claims_intensity,
            'marketing_vs_giving_gap': marketing_vs_giving_gap
        }
        
        # Add transparency metric scores
        company_data.update(transparency_metric_scores)
        
        # Add cause area distribution
        company_data.update(cause_area_data)
        
        # Add to companies list
        companies.append(company_data)
    
    # Convert to DataFrame
    df = pd.DataFrame(companies)
    
    # Generate environmental incidents data
    incident_df = generate_incident_data(df)
    
    # Generate historical data
    historical_data = generate_historical_data(df)
    
    # Generate marketing claims data (for greenwashing analysis #10)
    marketing_df = generate_marketing_data(df)
    
    # Store additional dataframes in the global dictionary
    additional_dataframes['incident_df'] = incident_df
    additional_dataframes['transparency_history'] = historical_data['transparency_history']
    additional_dataframes['giving_history'] = historical_data['giving_history']
    additional_dataframes['impact_history'] = historical_data['impact_history']
    additional_dataframes['marketing_df'] = marketing_df
    additional_dataframes['cause_area_df'] = generate_cause_area_summary(df)
    
    # For compatibility with the original code, attach incident_df
    df.incident_df = incident_df
    
    return df

