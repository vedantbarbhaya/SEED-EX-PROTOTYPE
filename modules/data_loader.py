"""
modules/data_loader.py
Functions for loading and processing data for the SEED dashboard
"""

import pandas as pd
import numpy as np
import streamlit as st
import io
import os
from datetime import datetime

# Try importing the data generator
try:
    from modules.data_generator import (
        generate_corporate_data, 
        generate_geographic_data,
        get_additional_dataframe
    )
except ImportError:
    st.error("Could not import data generator module. Sample data may not be available.")

def load_data(file):
    """
    Load data from uploaded file (CSV or Excel)
    
    Args:
        file (UploadedFile): The file uploaded through Streamlit
        
    Returns:
        pandas.DataFrame: The loaded data
    """
    # Get the file name and extension
    file_name = file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Read the file based on its extension
    if file_extension == '.csv':
        # Try different encodings and delimiters
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file, encoding='latin1')
            except:
                df = pd.read_csv(file, encoding='cp1252')
        except pd.errors.ParserError:
            # Try with different separator
            df = pd.read_csv(file, sep=';')
    
    elif file_extension in ['.xlsx', '.xls']:
        df = pd.read_excel(file)
    
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    # Perform some basic data cleaning
    df = clean_data(df)
    
    return df

def clean_data(df):
    """
    Perform basic data cleaning operations
    
    Args:
        df (pandas.DataFrame): The data to clean
        
    Returns:
        pandas.DataFrame: The cleaned data
    """
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Standardize column names
    df_clean.columns = [col.strip() for col in df_clean.columns]
    
    # Handle date columns
    date_columns = identify_date_columns(df_clean)
    for col in date_columns:
        df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Handle numeric columns
    numeric_columns = identify_numeric_columns(df_clean)
    for col in numeric_columns:
        # Try to convert to numeric, but keep as is if conversion fails
        try:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        except:
            pass
    
    # Fill common missing values
    categorical_columns = df_clean.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        # Fill missing categorical values
        if df_clean[col].isna().sum() > 0:
            df_clean[col] = df_clean[col].fillna("Unknown")
    
    # Try to detect and standardize specific columns that might be present
    standardize_common_columns(df_clean)
    
    return df_clean

def identify_date_columns(df):
    """
    Identify columns that likely contain dates
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        
    Returns:
        list: Column names that likely contain dates
    """
    date_columns = []
    
    # Check column names that suggest dates
    date_keywords = ['date', 'year', 'month', 'day', 'period', 'time']
    
    for col in df.columns:
        # Check if the column name contains date keywords
        if any(keyword in col.lower() for keyword in date_keywords):
            date_columns.append(col)
        else:
            # Try to convert column to datetime if it's not obviously a date
            try:
                # Get a sample to test
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    pd.to_datetime(sample, errors='raise')
                    date_columns.append(col)
            except:
                # Not a date column
                pass
    
    return date_columns

def identify_numeric_columns(df):
    """
    Identify columns that likely contain numeric data
    
    Args:
        df (pandas.DataFrame): The dataframe to analyze
        
    Returns:
        list: Column names that likely contain numeric data
    """
    # Start with columns that are already numeric
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    
    # Check other columns
    for col in df.columns:
        if col not in numeric_columns:
            # Check for columns with currency or numeric keywords
            numeric_keywords = ['amount', 'value', 'price', 'cost', 'revenue', 'profit', 
                             'expense', 'income', 'budget', 'total', 'sum', 'count',
                             'number', 'qty', 'quantity', 'score', 'rating', 'percent',
                             'percentage', 'ratio', 'million', 'billion', 'thousand']
            
            if any(keyword in col.lower() for keyword in numeric_keywords):
                # Try to convert to numeric
                try:
                    # Sample the column to avoid processing the entire column
                    sample = df[col].dropna().head(10)
                    if len(sample) > 0:
                        # Try to handle common currency formats
                        sample = sample.astype(str).str.replace('$', '', regex=False)
                        sample = sample.str.replace(',', '', regex=False)
                        sample = sample.str.replace('%', '', regex=False)
                        pd.to_numeric(sample, errors='raise')
                        numeric_columns.append(col)
                except:
                    # Not a numeric column
                    pass
    
    return numeric_columns

def standardize_common_columns(df):
    """
    Try to standardize common column names and formats
    
    Args:
        df (pandas.DataFrame): The dataframe to standardize (modified in place)
    """
    # Map of possible column names to standard names
    column_mapping = {
        # Company identifiers
        'name': 'company_name',
        'company': 'company_name',
        'corporation': 'company_name',
        'company_id': 'company_id',
        'id': 'company_id',
        'identifier': 'company_id',
        
        # Location information
        'state': 'state',
        'province': 'state',
        'region': 'state',
        'country': 'country',
        'city': 'city',
        'address': 'address',
        'zip': 'zip_code',
        'zipcode': 'zip_code',
        'postal': 'zip_code',
        'postal_code': 'zip_code',
        'lat': 'latitude',
        'latitude': 'latitude',
        'long': 'longitude',
        'longitude': 'longitude',
        
        # Financial information
        'revenue': 'revenue_millions',
        'gross_profit': 'gross_profit_millions',
        'profit': 'profit_millions',
        'income': 'income_millions',
        'market_cap': 'market_cap_millions',
        'market_value': 'market_cap_millions',
        'public_float': 'public_float_millions',
        
        # Environmental information
        'environmental_giving': 'env_giving_millions',
        'env_giving': 'env_giving_millions',
        'giving': 'env_giving_millions',
        'charitable_contributions': 'env_giving_millions',
        'donations': 'env_giving_millions',
        'philanthropy': 'env_giving_millions',
        
        # Impact information
        'emissions': 'emissions_tons',
        'ghg': 'emissions_tons',
        'carbon': 'emissions_tons',
        'carbon_footprint': 'emissions_tons',
        'waste': 'waste_tons',
        'water_usage': 'water_usage_gallons',
        'energy': 'energy_consumption_mwh',
        'energy_usage': 'energy_consumption_mwh',
        'power_consumption': 'energy_consumption_mwh',
        
        # Industry information
        'industry': 'industry',
        'sector': 'industry',
        'sic': 'sic_code',
        'standard_industrial_classification': 'sic_code',
        'naics': 'naics_code',
        
        # Transparency information
        'transparency': 'transparency_score',
        'reporting_quality': 'transparency_score',
        'disclosure_quality': 'transparency_score',
        'reporting_level': 'reporting_level',
        'detail': 'detail_level'
    }
    
    # Try to map columns based on similarity
    for col in df.columns:
        col_lower = col.lower().replace(' ', '_')
        
        # Find the closest match
        for possible_name, standard_name in column_mapping.items():
            if possible_name == col_lower or col_lower.endswith('_' + possible_name) or possible_name in col_lower:
                # Don't rename if the column already exists
                if standard_name not in df.columns:
                    df.rename(columns={col: standard_name}, inplace=True)
                break
    
    # Standardize financial amounts to millions
    financial_columns = ['revenue_millions', 'gross_profit_millions', 'profit_millions', 
                        'income_millions', 'market_cap_millions', 'public_float_millions',
                        'env_giving_millions']
    
    for col in financial_columns:
        if col in df.columns:
            # Check if values are likely in different units
            mean_value = df[col].mean()
            
            # If the mean is very large, values might be in dollars instead of millions
            if mean_value > 1e9:  # Values likely in dollars
                df[col] = df[col] / 1e6
            elif mean_value < 0.01 and mean_value > 0:  # Values likely in billions
                df[col] = df[col] * 1000

def get_sample_data():
    """
    Generate sample data for the dashboard
    
    Returns:
        dict: Dictionary containing sample dataframes
    """
    # Generate corporate data
    corporate_data = generate_corporate_data(num_companies=500)
    
    # Generate geographic data
    geographic_data = generate_geographic_data(corporate_data)
    
    # Get historical data
    historical_data = {
        'transparency_history': get_additional_dataframe('transparency_history'),
        'giving_history': get_additional_dataframe('giving_history'),
        'impact_history': get_additional_dataframe('impact_history')
    }
    
    # Get incident data
    incident_data = get_additional_dataframe('incident_df')
    
    # Attach incident data to corporate data
    if incident_data is not None:
        corporate_data.incident_df = incident_data
    
    return {
        "corporate_data": corporate_data,
        "geographic_data": geographic_data,
        "historical_data": historical_data
    }