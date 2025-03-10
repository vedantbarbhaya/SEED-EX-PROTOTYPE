"""
SEED Dashboard: Sustainability and Equity Environmental Dashboard
Main application file that serves as the entry point for the Streamlit dashboard
"""

import streamlit as st

# Set page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="SEED Dashboard - Sustainability and Equity Environmental Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
from datetime import datetime
import os
import io
import sys
import importlib.util
from PIL import Image

# Check if the modules directory exists
if not os.path.exists("modules"):
    st.error("Modules directory not found. Please create a 'modules' directory in your project root.")
    st.stop()

# Check if __init__.py exists in the modules directory
if not os.path.exists("modules/__init__.py"):
    st.warning("modules/__init__.py not found. Creating an empty one...")
    try:
        with open("modules/__init__.py", "w") as f:
            pass  # Create an empty file
    except Exception as e:
        st.error(f"Failed to create modules/__init__.py: {e}")

# Function to check if a module file exists
def check_module(module_name, display_name):
    module_path = f"modules/{module_name}.py"
    if not os.path.exists(module_path):
        st.error(f"Module file '{module_path}' not found. Please create this file.")
        return False
    return True

# Check all required module files
modules_ok = True
modules_ok &= check_module("data_loader", "Data Loader")
modules_ok &= check_module("data_generator", "Data Generator")
modules_ok &= check_module("corporate_players", "Corporate Players")
modules_ok &= check_module("transparency", "Transparency")
modules_ok &= check_module("impact_giving", "Impact vs. Giving")
modules_ok &= check_module("leaders_laggards", "Leaders & Laggards")
modules_ok &= check_module("recommendations", "Recommendations")
modules_ok &= check_module("visualizations", "Visualizations")

if not modules_ok:
    st.error("Some required modules are missing. Please create all necessary module files in the 'modules' directory.")
    st.stop()

# Import our modules
try:
    # Make sure 'modules' is in the Python path
    if not "." in sys.path:
        sys.path.insert(0, ".")
    
    from modules.data_loader import load_data, get_sample_data
    from modules.corporate_players import display_corporate_players_tab
    from modules.transparency import display_transparency_tab
    from modules.impact_giving import display_impact_giving_tab
    from modules.leaders_laggards import display_leaders_laggards_tab
    from modules.recommendations import display_recommendations_tab
    from modules.visualizations import register_visualization
    
    # If we've reached here, all imports succeeded
    st.success("Successfully imported all required modules.")
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.error("Make sure all module files are properly set up with the correct functions.")
    
    # Try to identify which module is causing the problem
    try:
        import importlib.util
        for module_name in ["data_loader", "corporate_players", "transparency", "impact_giving", 
                           "leaders_laggards", "recommendations", "visualizations"]:
            spec = importlib.util.find_spec(f"modules.{module_name}")
            if spec is None:
                st.error(f"Could not find module 'modules.{module_name}'")
            else:
                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    st.info(f"Successfully loaded module 'modules.{module_name}'")
                    
                    # Check for specific functions
                    if module_name == "data_loader" and (not hasattr(module, "load_data") or not hasattr(module, "get_sample_data")):
                        st.error(f"Module 'modules.{module_name}' is missing required functions: load_data, get_sample_data")
                    elif module_name == "corporate_players" and not hasattr(module, "display_corporate_players_tab"):
                        st.error(f"Module 'modules.{module_name}' is missing required function: display_corporate_players_tab")
                    elif module_name == "transparency" and not hasattr(module, "display_transparency_tab"):
                        st.error(f"Module 'modules.{module_name}' is missing required function: display_transparency_tab")
                    elif module_name == "impact_giving" and not hasattr(module, "display_impact_giving_tab"):
                        st.error(f"Module 'modules.{module_name}' is missing required function: display_impact_giving_tab")
                    elif module_name == "leaders_laggards" and not hasattr(module, "display_leaders_laggards_tab"):
                        st.error(f"Module 'modules.{module_name}' is missing required function: display_leaders_laggards_tab")
                    elif module_name == "recommendations" and not hasattr(module, "display_recommendations_tab"):
                        st.error(f"Module 'modules.{module_name}' is missing required function: display_recommendations_tab")
                    elif module_name == "visualizations" and not hasattr(module, "register_visualization"):
                        st.error(f"Module 'modules.{module_name}' is missing required function: register_visualization")
                except Exception as e:
                    st.error(f"Error loading module 'modules.{module_name}': {e}")
    except Exception as e:
        st.error(f"Could not analyze module problem: {e}")
        
    st.stop()

# Define simplified fallback functions in case modules fail to load properly
def fallback_display_tab(df, tab_name):
    st.header(f"{tab_name} (Fallback Version)")
    st.warning(f"The {tab_name} module didn't load properly. This is a simplified fallback view.")
    
    # Show basic dataframe information
    st.subheader("Data Overview")
    st.write(f"Data shape: {df.shape}")
    st.write("First few rows:")
    st.dataframe(df.head())
    
    # Show column statistics
    st.subheader("Column Statistics")
    st.dataframe(df.describe())

# Load logo 
def load_logo():
    try:
        # Try to load from pictures directory
        if os.path.exists("pictures/logo.png"):
            return Image.open("pictures/logo.png")
        else:
            # Return None if logo doesn't exist
            return None
    except Exception as e:
        st.error(f"Error loading logo: {e}")
        return None

# Function to display the sidebar
def display_sidebar():
    logo = load_logo()
    if logo:
        st.sidebar.image(logo, width=200)
    
    st.sidebar.title("SEED Dashboard")
    st.sidebar.markdown("### Sustainability and Equity Environmental Dashboard")
    
    # Add navigation
    tab = st.sidebar.radio(
        "Navigate to:",
        ["Corporate Players", "Transparency Analysis", "Impact vs. Giving", 
         "Leaders & Laggards", "Recommendations"]
    )
    
    # Additional filters that apply across all tabs
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Global Filters")
    
    # Only show these filters when data is loaded
    if 'data' in st.session_state and st.session_state.data is not None:
        data = st.session_state.data
        
        # Year filter if we have year data
        year_col = None
        for col in ['year', 'Year', 'filing_year', 'Date of Filing']:
            if col in data.columns:
                year_col = col
                break
        
        if year_col:
            try:
                # Try to extract years
                if year_col == 'Date of Filing':
                    # Convert to datetime if it's not already
                    if not pd.api.types.is_datetime64_any_dtype(data[year_col]):
                        years = pd.to_datetime(data[year_col], errors='coerce').dt.year.dropna().unique()
                    else:
                        years = data[year_col].dt.year.unique()
                else:
                    years = data[year_col].unique()
                
                # Sort years
                years = sorted(years)
                
                if len(years) > 1:
                    selected_year = st.sidebar.selectbox(
                        "Select Year:",
                        options=["All Years"] + list(years),
                        index=0
                    )
                    
                    if selected_year != "All Years":
                        if year_col == 'Date of Filing':
                            # Filter by year in the date
                            if not pd.api.types.is_datetime64_any_dtype(data[year_col]):
                                data = data[pd.to_datetime(data[year_col], errors='coerce').dt.year == selected_year]
                            else:
                                data = data[data[year_col].dt.year == selected_year]
                        else:
                            # Direct year filter
                            data = data[data[year_col] == selected_year]
                        
                        # Update session state with filtered data
                        st.session_state.filtered_data = data
                    else:
                        st.session_state.filtered_data = data
            except Exception as e:
                st.sidebar.warning(f"Could not filter by year: {e}")
                st.session_state.filtered_data = data
        else:
            st.session_state.filtered_data = data
            
        # Industry filter if we have industry data
        industry_col = None
        for col in ['industry', 'Industry', 'Standard Industrial Classification (SIC)', 'SIC']:
            if col in data.columns:
                industry_col = col
                break
        
        if industry_col:
            industries = sorted(data[industry_col].dropna().unique())
            
            selected_industries = st.sidebar.multiselect(
                "Filter by Industry:",
                options=industries,
                default=[]
            )
            
            if selected_industries:
                data = data[data[industry_col].isin(selected_industries)]
                # Update session state with filtered data
                st.session_state.filtered_data = data
    
    # Add about section
    st.sidebar.markdown("---")
    with st.sidebar.expander("About SEED Dashboard"):
        st.markdown("""
        The **Sustainability and Equity Environmental Dashboard (SEED)** tracks corporate spending on environmental and social justice causes using data from SEC filings, IRS reports, and sustainability disclosures.
        
        This tool enhances transparency in fund distribution, helping stakeholders understand where funds come from and where they're going.
        
        Developed by The Undivide Project.
        """)
    
    # Add download button for the data if available
    if 'data' in st.session_state and st.session_state.data is not None:
        st.sidebar.markdown("---")
        st.sidebar.download_button(
            label="Download Full Dataset (CSV)",
            data=convert_df_to_csv(st.session_state.filtered_data),
            file_name=f"seed_dashboard_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    return tab

# Function to convert dataframe to CSV
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Main app function
def main():
    # Initialize session state for data if it doesn't exist
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.session_state.filtered_data = None
        st.session_state.geo_data = None
        st.session_state.historical_data = None
    
    # Display sidebar and get selected tab
    selected_tab = display_sidebar()
    
    # Main content area
    st.title("SEED: Sustainability and Equity Environmental Dashboard")
    
    # Data selection section
    with st.container():
        st.markdown("## Data Source")
        
        data_source = st.radio(
            "Select data source:",
            ["Upload File", "Use Sample Data", "Connect to API (Coming Soon)"],
            horizontal=True
        )
        
        if data_source == "Upload File":
            uploaded_file = st.file_uploader("Upload your data (CSV or Excel):", type=["csv", "xlsx"])
            
            if uploaded_file is not None:
                try:
                    st.session_state.data = load_data(uploaded_file)
                    st.session_state.filtered_data = st.session_state.data
                    st.success(f"Successfully loaded data with {len(st.session_state.data)} records.")
                except Exception as e:
                    st.error(f"Error loading data: {e}")
                    st.session_state.data = None
                    st.session_state.filtered_data = None
        
        elif data_source == "Use Sample Data":
            if st.button("Load Sample Data"):
                with st.spinner("Loading sample data..."):
                    try:
                        data_dict = get_sample_data()
                        st.session_state.data = data_dict.get("corporate_data")
                        st.session_state.filtered_data = st.session_state.data
                        st.session_state.geo_data = data_dict.get("geographic_data")
                        st.session_state.historical_data = data_dict.get("historical_data")
                        st.success(f"Successfully loaded sample data with {len(st.session_state.data)} records.")
                    except Exception as e:
                        st.error(f"Error loading sample data: {e}")
                        st.session_state.data = None
                        st.session_state.filtered_data = None
        
        elif data_source == "Connect to API (Coming Soon)":
            st.info("API connection functionality is coming soon.")
            
        # Divider
        st.markdown("---")
    
    # Display the appropriate tab content
    if st.session_state.filtered_data is not None:
        try:
            if selected_tab == "Corporate Players":
                display_corporate_players_tab(
                    st.session_state.filtered_data,
                    st.session_state.geo_data
                )
            
            elif selected_tab == "Transparency Analysis":
                display_transparency_tab(
                    st.session_state.filtered_data,
                    st.session_state.historical_data
                )
            
            elif selected_tab == "Impact vs. Giving":
                display_impact_giving_tab(st.session_state.filtered_data)
            
            elif selected_tab == "Leaders & Laggards":
                display_leaders_laggards_tab(st.session_state.filtered_data)
            
            elif selected_tab == "Recommendations":
                display_recommendations_tab(st.session_state.filtered_data)
        except NameError as e:
            st.error(f"Module function not available: {e}")
            fallback_display_tab(st.session_state.filtered_data, selected_tab)
        except Exception as e:
            st.error(f"Error displaying {selected_tab}: {e}")
            fallback_display_tab(st.session_state.filtered_data, selected_tab)
    
    else:
        st.info("Please select a data source to continue.")
        
        # Display a preview of what the dashboard offers
        with st.expander("Dashboard Preview"):
            st.markdown("""
            ### What This Dashboard Offers
            
            1. **Corporate Players Analysis**: Explore who the companies are, where they're located, and what industries they represent.
            
            2. **Transparency Analysis**: Analyze how transparent companies are about their environmental activities and giving.
            
            3. **Impact vs. Giving Analysis**: Examine the relationship between companies' environmental impact and their charitable giving.
            
            4. **Leaders & Laggards**: Identify which companies and industries are leading the way and which are falling behind.
            
            5. **Recommendations**: Get insights and recommendations based on the data analysis.
            
            To get started, please load data using one of the options above.
            """)

# Run the app
if __name__ == "__main__":
    main()