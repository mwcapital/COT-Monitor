"""
Data fetching and processing module for CFTC COT data
"""
import streamlit as st
import pandas as pd
from sodapy import Socrata
import json
from config import CFTC_API_BASE, DATASET_CODE, DEFAULT_LIMIT, CFTC_COLUMNS


@st.cache_data
def load_instruments_database():
    """Load the instruments JSON database"""
    try:
        # Try multiple locations for backward compatibility
        json_paths = [
            'data/instruments_LegacyF.json',  # New location
            'instruments_LegacyF.json',        # Legacy location
            '../data/instruments_LegacyF.json' # Alternative path
        ]
        
        for path in json_paths:
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
                
        st.error("❌ instruments_LegacyF.json file not found. Please ensure it's in the data/ directory.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading instruments database: {e}")
        return None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_cftc_data(instrument_name, api_token):
    """Fetch CFTC data for a specific instrument"""
    try:
        client = Socrata(CFTC_API_BASE, api_token)

        results = client.get(
            DATASET_CODE,
            where=f"market_and_exchange_names='{instrument_name}'",
            select=",".join(CFTC_COLUMNS),
            order="report_date_as_yyyy_mm_dd ASC",
            limit=DEFAULT_LIMIT
        )

        client.close()

        if not results:
            return None

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Convert date column
        df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])

        # Convert numeric columns
        numeric_columns = [col for col in CFTC_COLUMNS if
                           col != "report_date_as_yyyy_mm_dd" and col != "market_and_exchange_names"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Calculate additional metrics
        df['net_noncomm_positions'] = df['noncomm_positions_long_all'] - df['noncomm_positions_short_all']
        df['net_comm_positions'] = df['comm_positions_long_all'] - df['comm_positions_short_all']
        df['net_reportable_positions'] = df['tot_rept_positions_long_all'] - df['tot_rept_positions_short']

        return df.sort_values('report_date_as_yyyy_mm_dd')

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


def get_asset_class(commodity_group):
    """Map commodity group to asset class"""
    energy = ["PETROLEUM AND PRODUCTS", "ELECTRICITY", "NATURAL GAS"]
    metals = ["PRECIOUS METALS", "BASE METALS"]
    agriculture = ["GRAINS AND OILSEEDS", "LIVESTOCK", "DAIRY", "SOFTS", "WOOD PRODUCTS"]
    
    if commodity_group in energy:
        return "Energy"
    elif commodity_group in metals:
        return "Metals"
    elif commodity_group in agriculture:
        return "Agriculture"
    else:
        return "Other"