# modules/chatbot.py

import streamlit as st
import openai
import pandas as pd
import json

def get_company_data(company_name, df):
    """Retrieve data for a specific company"""
    # Handle different data structures
    if 'company_name' in df.columns:
        # Generated data
        # Case-insensitive partial match
        matches = df[df['company_name'].str.lower().str.contains(company_name.lower())]
        
        if len(matches) == 0:
            return {"error": f"No company found matching '{company_name}'"}
        
        # If multiple matches, take the closest one or the first
        company_data = matches.iloc[0].to_dict()
        
        # Format numeric values for better readability
        formatted_data = {
            "company_name": company_data["company_name"],
            "industry": company_data["industry"],
            "state": company_data["state"],
            "size": company_data["size"],
            "revenue_millions": f"${company_data['revenue_millions']:.1f}M",
            "env_giving_millions": f"${company_data['env_giving_millions']:.2f}M",
            "env_giving_pct": f"{company_data['env_giving_pct']:.2f}%"
        }
    else:
        # Real data
        # Case-insensitive partial match
        matches = df[df['Name'].str.lower().str.contains(company_name.lower())]
        
        if len(matches) == 0:
            return {"error": f"No company found matching '{company_name}'"}
        
        # If multiple matches, take the closest one or the first
        company_data = matches.iloc[0].to_dict()
        
        # Format the data appropriately
        formatted_data = {
            "company_name": company_data.get("Name", "N/A"),
            "industry": str(company_data.get("Standard Industrial Classification (SIC)", "N/A")),
            "state": company_data.get("State", "N/A"),
            "public_float": f"${company_data.get('Public Float', 0):,.0f}",
            "gross_profit": f"${company_data.get('Gross Profit', 0):,.0f}",
            "charitable_contributions": f"${company_data.get('Charitable Contributions', 0):,.0f}",
            "environmental_expenses": f"${company_data.get('Environmental Remediation Expenses', 0):,.0f}"
        }
    
    return formatted_data

# Other functions similar to what you had before, adapted to handle different data structures...

def create_chat_interface(df, geo_df=None):
    """Create an interactive chat interface powered by OpenAI with function calling"""
    st.header("💬 Ask Questions About the Data")
    
    st.markdown("""
    Use this chat interface to ask questions about the corporate environmental giving data.
    Examples:
    - "Which industries give the most to environmental causes?"
    - "Tell me about companies in California"
    - "What are the reporting patterns for environmental giving?"
    - "Which states have the highest charitable contributions?"
    """)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Determine if we're using real or generated data
    using_real_data = 'company_name' not in df.columns
    
    # Create appropriate data summaries based on data type
    if using_real_data:
        # Real data summaries
        data_summary = f"""
        Key data points:
        - Number of companies: {df['Name'].nunique()}
        - Number of industries (SICs): {df['Standard Industrial Classification (SIC)'].nunique()}
        - States represented: {df['State'].nunique()}
        - Companies reporting charitable contributions: {df[df['Charitable Contributions'].notna()]['Name'].nunique()}
        - Companies reporting environmental remediation: {df[df['Environmental Remediation Expenses'].notna()]['Name'].nunique()}
        """
    else:
        # Generated data summaries
        data_summary = f"""
        Key data points:
        - Number of companies: {len(df)}
        - Number of industries: {df['industry'].nunique()}
        - Total environmental giving: ${df['env_giving_millions'].sum():.1f}M
        - Top 3 industries by giving: {', '.join(df.groupby('industry')['env_giving_millions'].sum().sort_values(ascending=False).head(3).index.tolist())}
        - Top 3 states by giving: {', '.join(geo_df.sort_values('env_giving_millions', ascending=False).head(3)['state'].tolist()) if geo_df is not None else 'Not Available'}
        """
    
    # Prepare system prompt with data context
    system_prompt = f"""
    You are a helpful assistant embedded in a dashboard about corporate environmental philanthropy.

    The dashboard contains these tabs and visualizations:
    
    1. CORPORATE PLAYERS TAB:
       - Information about the companies, their industries, locations, and basic metrics
       - Geographic Distribution of companies and their environmental giving
       - Industry Breakdown of environmental philanthropy
       - Company Size Distribution and its relation to giving patterns
       - Top Companies by environmental contributions
    
    2. TRANSPARENCY TAB:
       - Detail Level Reporting: How transparent companies are in their financial disclosures
       - Transparency Scores by industry and company
       - Reporting Improvement Over Time: How reporting has changed
       - Missing Data Indicators: Where reporting gaps exist
    
    3. IMPACT VS. GIVING TAB:
       - Environmental Impact vs. Giving: Relationship between footprint and philanthropy
       - Loss Contingencies vs. Philanthropy: How potential liabilities relate to giving
       - Environmental Incidents Map: Where companies have had environmental violations
       - Impact-Giving Correlation: Statistical relationship between impact and giving
    
    4. GENUINE OR STRATEGIC TAB:
       - Marketing Claims vs. Actual Giving: Comparing promises with reality
       - Local vs. National/International Giving: Where the money goes
       - HQ Location vs. Giving Patterns: Geographic relationship between company presence and giving
       - Philanthropy Effectiveness Score: Rating the strategic value of giving
    
    5. LEADERS & LAGGARDS TAB:
       - Industry Benchmarks: Who exceeds or falls short of industry averages
       - Time Series Trends: How giving has changed over time
       - Peer Comparison: Side-by-side analysis of similar companies
       - ESG Scores vs. Giving: Relationship between overall ESG performance and environmental giving
    
    6. WHAT CAN BE DONE TAB:
       - Policy Recommendations: Suggestions for regulatory approaches
       - Corporate Improvement Roadmap: Steps for companies to enhance practices
       - Giving by Cause Area: Which environmental causes receive the most funding
       - Giving Efficiency Metrics: Which giving programs are most effective
    
    DATA SUMMARY:
    {data_summary}
    
    When responding:
    1. Be concise and focus on relevant data insights
    2. When appropriate, suggest which dashboard tab or visualization might help answer the question
    3. If you don't have the specific information, acknowledge that and suggest what relevant information is available
    4. Format your responses using markdown for readability
    """
    
    # Define the tools based on the data structure we have
    if using_real_data:
        # Tools for real data
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_company_data",
                    "description": "Get detailed data about a specific company",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string", 
                                "description": "The name of the company to look up"
                            }
                        },
                        "required": ["company_name"]
                    }
                }
            },
            # Add other appropriate tools for real data...
        ]
    else:
        # Tools for generated data
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_company_data",
                    "description": "Get detailed data about a specific company",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string", 
                                "description": "The name of the company to look up"
                            }
                        },
                        "required": ["company_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_industry_data",
                    "description": "Get aggregated data about a specific industry",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "industry": {
                                "type": "string", 
                                "description": "The name of the industry to look up"
                            }
                        },
                        "required": ["industry"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_state_data",
                    "description": "Get data about a specific state",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string", 
                                "description": "The name of the state to look up"
                            }
                        },
                        "required": ["state"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_comparison_data",
                    "description": "Compare different entities by a specific metric",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_type": {
                                "type": "string", 
                                "description": "The type of entity to compare (industry, state, or company size)",
                                "enum": ["industry", "state", "company size"]
                            },
                            "metric": {
                                "type": "string", 
                                "description": "The metric to compare by (giving, percentage)",
                                "enum": ["giving", "percentage"]
                            }
                        },
                        "required": ["entity_type", "metric"]
                    }
                }
            }
        ]
    
    # Accept user input
    if prompt := st.chat_input("Ask a question about corporate environmental giving..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Get OpenAI API key from Streamlit secrets
                api_key = st.secrets.get("openai_api_key", None)
                
                # If we can't get it from secrets, try to get it from session state
                if not api_key and "openai_api_key" in st.session_state:
                    api_key = st.session_state.openai_api_key
                
                # If we still don't have an API key, prompt the user for one
                if not api_key:
                    api_key = st.text_input("Enter your OpenAI API key:", type="password")
                    if api_key:
                        st.session_state.openai_api_key = api_key
                
                if api_key:
                    # Configure OpenAI client
                    client = openai.OpenAI(api_key=api_key)
                    
                    # Create a list of message objects for the API
                    messages = [
                        {"role": "system", "content": system_prompt}
                    ]
                    
                    # Add chat history to context (up to last 5 messages to stay within token limits)
                    for message in st.session_state.messages[-10:]:
                        messages.append({"role": message["role"], "content": message["content"]})
                    
                    # Try to get a model that supports tools, fall back if not available
                    try:
                        # Get initial response from OpenAI with function calling
                        response = client.chat.completions.create(
                            model="gpt-4-1106-preview",  # Use a model that supports tools
                            messages=messages,
                            tools=tools,
                            tool_choice="auto",
                            temperature=0.7
                        )
                        
                        response_message = response.choices[0].message
                        
                        # Check if the model wants to call functions
                        if response_message.tool_calls:
                            # Process the function calls
                            results = process_tool_calls(response_message.tool_calls, df, geo_df)
                            
                            # Add the model's initial response to the messages
                            messages.append(response_message)
                            
                            # Add the function results to the messages
                            for result in results:
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": result["tool_call_id"],
                                    "name": result["function_name"],
                                    "content": json.dumps(result["result"])
                                })
                            
                            # Get the final response
                            final_response = client.chat.completions.create(
                                model="gpt-4-1106-preview",
                                messages=messages,
                                stream=True
                            )
                            
                            # Display the response as it streams in
                            for chunk in final_response:
                                if chunk.choices[0].delta.content:
                                    content = chunk.choices[0].delta.content
                                    full_response += content
                                    message_placeholder.markdown(full_response + "▌")
                            
                            message_placeholder.markdown(full_response)
                        else:
                            # If no function calls, just display the content directly
                            full_response = response_message.content
                            message_placeholder.markdown(full_response)
                    except:
                        # Fall back to gpt-3.5-turbo if gpt-4 is not available
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=messages,
                            stream=True
                        )
                        
                        # Display the response as it streams in
                        for chunk in response:
                            if chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                                full_response += content
                                message_placeholder.markdown(full_response + "▌")
                        
                        message_placeholder.markdown(full_response)
                else:
                    full_response = "Please provide an OpenAI API key to use the chat feature."
                    message_placeholder.markdown(full_response)
            
            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.markdown(error_message)
                full_response = error_message
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# Function for processing tool calls (for now just a stub to avoid errors) 
def process_tool_calls(tool_calls, df, geo_df=None):
    """Process function calls from the OpenAI API"""
    results = []
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name == "get_company_data":
            company_name = function_args.get("company_name")
            result = get_company_data(company_name, df)
            results.append({
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "result": result
            })
        
        # Add other function handling here...
    
    return results