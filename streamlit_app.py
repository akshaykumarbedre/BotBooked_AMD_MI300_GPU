import streamlit as st
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any

# Configure page settings
st.set_page_config(
    page_title="BotBooked.ai - AI Scheduling Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Dark Theme Configuration ---
DARK_THEME = {
    "primary-color": "#673AB7",  # Deep Purple
    "secondary-color": "#03A9F4", # Light Blue
    "accent-color": "#FFC107",   # Amber
    "success-color": "#4CAF50",
    "warning-color": "#FF9800",
    "danger-color": "#F44336",
    "dark-bg": "#1E1E1E",
    "light-bg": "#262730",
    "main-bg": "#121212",
    "text-color": "#E0E0E0",
    "secondary-text-color": "#A0A0A0",
    "card-bg-gradient-light": "#2A2A2A",
    "card-bg-gradient-dark": "#333333",
}

# Initialize processing state
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "api_response" not in st.session_state:
    st.session_state.api_response = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None
if "time_taken" not in st.session_state:
    st.session_state.time_taken = None

def apply_dark_theme():
    """Applies the dark theme's CSS variables."""
    theme_colors = DARK_THEME
    root_css_vars = ""
    for prop, value in theme_colors.items():
        root_css_vars += f"--{prop}: {value};\n"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        :root {{
            {root_css_vars}
        }}

        .stApp {{
            background-color: var(--main-bg) !important;
            color: var(--text-color) !important;
        }}

        body {{
            font-family: 'Poppins', sans-serif !important;
            background-color: var(--main-bg) !important;
            color: var(--text-color) !important;
        }}

        #MainMenu {{visibility: hidden;}}
        header {{visibility: visible;}}
        
        .main .block-container {{
            padding-top: 1rem;
            padding-right: 2rem;
            padding-left: 2rem;
            padding-bottom: 2rem;
            background-color: var(--main-bg) !important;
        }}
        
        .main-header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            padding: 3rem 2rem;
            border-radius: 20px;
            margin-bottom: 2.5rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            color: white;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .main-header h1 {{
            font-size: 3.5rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.4);
            letter-spacing: -1px;
        }}
        
        .main-header p {{
            font-size: 1.3rem;
            opacity: 0.95;
            margin: 0.75rem 0 0 0;
            line-height: 1.5;
        }}

        /* Text Area Styling for JSON Input */
        .stTextArea > div > div > textarea {{
            background-color: var(--dark-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--dark-bg) !important;
            border-radius: 15px !important;
            padding: 1rem !important;
            font-size: 1.0rem !important;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; /* Monospace for JSON */
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }}
        .stTextArea > div > div > textarea:focus {{
            border-color: var(--secondary-color) !important;
            box-shadow: 0 0 0 0.2rem var(--secondary-color)40 !important;
        }}

        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            color: white !important;
            border: none !important;
            padding: 0.85rem 2.5rem !important;
            border-radius: 30px !important;
            font-weight: 600 !important;
            margin-top: 1.1rem !important;
            font-size: 1.15rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 5px 20px rgba(103, 58, 183, 0.3) !important; /* Primary color shadow */
            cursor: pointer !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(103, 58, 183, 0.4) !important;
            filter: brightness(1.05) !important;
            color: white !important;
        }}

        .stButton > button:disabled {{
            background: var(--secondary-text-color) !important;
            color: var(--dark-bg) !important;
            cursor: not-allowed !important;
            transform: none !important;
            box-shadow: none !important;
        }}

        /* Response Display Styling */
        .response-container {{
            background-color: var(--dark-bg) !important;
            padding: 2rem;
            border-radius: 18px;
            box-shadow: 0 6px 25px rgba(0,0,0,0.3);
            margin-top: 2.5rem;
            border: 1px solid var(--dark-bg);
            color: var(--text-color) !important;
        }}
        .response-container h3 {{
            color: var(--primary-color) !important;
            font-weight: 600;
            margin-bottom: 1rem;
        }}
        .response-container pre {{
            background-color: var(--light-bg) !important;
            border-radius: 10px;
            padding: 1.5rem;
            white-space: pre-wrap; /* Ensures long lines wrap */
            word-wrap: break-word; /* Breaks long words */
            color: var(--text-color) !important;
            overflow-x: auto; /* Adds horizontal scroll for very long lines */
        }}

        /* General text styling */
        .stMarkdown, .stText, p, div, span {{
            color: var(--text-color) !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-color) !important;
        }}
        .stAlert {{
            background-color: var(--dark-bg) !important;
            color: var(--text-color) !important;
            border-radius: 10px;
            border: 1px solid var(--secondary-text-color);
        }}
        /* Metric Cards */
        [data-testid="stMetric"] {{
            background-color: var(--dark-bg) !important;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.2);
            border-bottom: 5px solid var(--accent-color);
            text-align: center;
        }}
        [data-testid="stMetric"] label {{
            color: var(--secondary-text-color) !important;
            font-size: 1rem;
            font-weight: 600;
        }}


        [data-testid="stMetric"] div[data-testid="stMetricValue"] {{
            font-size: 1.8rem; /* Slightly smaller for compactness */
            color: var(--secondary-color) !important; /* Changed to secondary for variety */
            font-weight: 700;
        }}
    </style>
    """, unsafe_allow_html=True)

def create_header():
    """Create the main application header with a modern design."""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 BotBooked.ai</h1>
        <p>Your Intelligent AI Scheduling Assistant</p>
    </div>
    """, unsafe_allow_html=True)

def send_json_to_backend(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sends JSON data to the backend API and returns the response along with time taken."""
    # This is the endpoint where your backend service will listen
    API_URL = "http://129.212.190.146:5000/receive" 
    
    start_time = time.time()
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(API_URL, json=json_data, headers=headers, timeout=60) # Increased timeout to 60 seconds
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        end_time = time.time()
        st.session_state.time_taken = f"{end_time - start_time:.2f} seconds"
        return response.json()
    except requests.exceptions.Timeout:
        st.session_state.error_message = "The request timed out. The backend service took too long to respond."
        st.session_state.time_taken = f"{time.time() - start_time:.2f} seconds (Timeout)"
        return {"error": st.session_state.error_message}
    except requests.exceptions.ConnectionError:
        st.session_state.error_message = "Could not connect to the backend service. Please ensure it is running and accessible."
        st.session_state.time_taken = f"{time.time() - start_time:.2f} seconds (Connection Error)"
        return {"error": st.session_state.error_message}
    except requests.exceptions.HTTPError as e:
        st.session_state.error_message = f"HTTP Error: {e.response.status_code} - {e.response.text}"
        st.session_state.time_taken = f"{time.time() - start_time:.2f} seconds (HTTP Error)"
        return {"error": st.session_state.error_message}
    except json.JSONDecodeError:
        st.session_state.error_message = "Failed to decode JSON response from the backend. The response might not be valid JSON."
        st.session_state.time_taken = f"{time.time() - start_time:.2f} seconds (JSON Decode Error)"
        return {"error": st.session_state.error_message}
    except Exception as e:
        st.session_state.error_message = f"An unexpected error occurred: {e}"
        st.session_state.time_taken = f"{time.time() - start_time:.2f} seconds (Unexpected Error)"
        return {"error": st.session_state.error_message}

def main():
    """Main application function to run the BotBooked.ai interface."""
    apply_dark_theme()
    create_header()

    st.markdown("### 📥 Enter Scheduling Request as JSON")
    
    # Example JSON input, updated to reflect current year
    

    user_json_input = st.text_area(
        label="Please enter your scheduling request in JSON format:",
        label_visibility="collapsed",
        height=300,
        placeholder=("Example JSON:\n"
                     "{\n"
                     "  \"user_id\": \"12345\",\n"
                     "  \"request\": \"Schedule a meeting with John Doe\",\n"
                     "  \"date\": \"2023-10-01\",\n"
                     "  \"time\": \"10:00\",\n"
                     "  \"duration\": 30\n"
                     "}"),
        key="user_json_textarea",
        disabled=st.session_state.is_processing
    )

    col_empty1, col_btn, col_empty2 = st.columns([1, 2, 1])
    with col_btn:
        if not st.session_state.is_processing:
            send_request_button = st.button("Schedule meeting", use_container_width=True, key="send_request_btn")
        else:
            st.button("🤖 Processing...", use_container_width=True, disabled=True, key="processing_btn")
            send_request_button = False

    if send_request_button:
        st.session_state.is_processing = True
        st.session_state.api_response = None
        st.session_state.error_message = None
        st.session_state.time_taken = None
        st.rerun() # Rerun to disable input and show processing state

    if st.session_state.is_processing:
        st.markdown("---")
        
        status_placeholder = st.empty()
        status_placeholder.info("Sending request to BotBooked.ai backend...")
        
        try:
            # Attempt to parse JSON input
            parsed_json = json.loads(user_json_input)
            
            # Send the JSON to the backend
            st.session_state.api_response = send_json_to_backend(parsed_json)
            
            # Clear processing state and indicators
            st.session_state.is_processing = False
            status_placeholder.empty() # Clear the info message
            st.rerun() # Rerun to update UI with response
            
        except json.JSONDecodeError:
            st.session_state.error_message = "Invalid JSON format. Please ensure your input is valid JSON."
            st.session_state.is_processing = False
            status_placeholder.empty()
            st.rerun() # Rerun to show error and re-enable input
        except Exception as e:
            st.session_state.error_message = f"An unexpected error occurred during request submission: {e}"
            st.session_state.is_processing = False
            status_placeholder.empty()
            st.rerun() # Rerun to show error and re-enable input


    # Display API response or error
    if st.session_state.api_response or st.session_state.error_message:
        st.markdown("---")
        st.markdown("## 📤 AI Response & Metrics")

        col1, col2 = st.columns([3, 1]) # Wider column for response, narrower for metric
        with col2:
            if st.session_state.time_taken:
                st.metric(label="Time Taken", value=st.session_state.time_taken)

        with col1:
            if st.session_state.api_response:
                st.markdown(f"""
                <div class="response-container">
                    <h3>Raw JSON Response from BotBooked.ai Backend:</h3>
                    <pre><code>{json.dumps(st.session_state.api_response, indent=2)}</code></pre>
                </div>
                """, unsafe_allow_html=True)
                
                # Optional: Add download button for the received JSON
                st.download_button(
                    label="⬇️ Download Response JSON",
                    data=json.dumps(st.session_state.api_response, indent=2),
                    file_name=f"botbooked_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_response_json_btn",
                    use_container_width=True
                )
            elif st.session_state.error_message:
                st.error(st.session_state.error_message)

        st.session_state.api_response = None # Clear response after display
        st.session_state.error_message = None # Clear error after display
        st.session_state.time_taken = None # Clear time taken after display

if __name__ == "__main__":
    main()