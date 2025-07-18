# CFTC COT Data Dashboard

A comprehensive Streamlit dashboard for analyzing Commodity Futures Trading Commission (CFTC) Commitments of Traders (COT) reports.

## Features

### =� Analysis Types
- **Time Series Analysis**: Track market trends over time
- **Share of Open Interest**: Visualize position distribution among trader categories
- **Seasonality Analysis**: Identify seasonal patterns in market behavior
- **Percentile Analysis**: Compare current values to historical distributions
- **Momentum Dashboard**: Monitor market momentum with adaptive scaling
- **Trader Participation Analysis**: Deep dive into trader behavior patterns

### <� Key Capabilities
- Real-time data fetching from CFTC API
- Interactive charts with Plotly
- Multiple instrument support
- Adaptive time range selection
- Statistical overlays and indicators
- Export functionality

## Installation

### Prerequisites
- Python 3.8 or higher
- pip or UV package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/COT-Analysis.git
cd COT-Analysis
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Alternative: Using UV Package Manager
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root:
```bash
SOCRATA_API_TOKEN=your_api_token_here
```

2. Get your free API token from: https://data.cftc.gov/

## Running the Application

### Using Streamlit directly:
```bash
streamlit run streamlit_app.py
```

### Alternative entry points:
```bash
# Using the modular app structure
streamlit run src/app.py

# Using the legacy monolithic file (not recommended)
streamlit run src/legacyF.py
```

## Project Structure

```
COT-Analysis/
   streamlit_app.py          # Main entry point
   requirements.txt          # Python dependencies
   pyproject.toml           # Project metadata
   data/                    # Data files
      instruments_LegacyF.json
   src/                     # Source code
      app.py              # Modular app entry
      config.py           # Configuration
      data_fetcher.py     # CFTC API integration
      display_functions.py # Display utilities
      charts/             # Chart modules
         base_charts.py
         seasonality_charts.py
         participation_charts.py
         share_of_oi.py
      ui_components.py    # UI components
      legacyF.py         # Legacy monolithic file
   tests/                  # Test files
   examples/              # Demo scripts
```

## Usage

1. **Select Analysis Mode**: Choose between Single Instrument or Multi-Instrument analysis
2. **Choose Instrument**: Search and select from available futures contracts
3. **Select Chart Type**: Pick from various analysis options
4. **Fetch Data**: Click "Fetch Data" to retrieve latest COT reports
5. **Interact**: Use date ranges, toggles, and other controls to explore the data

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document functions with docstrings

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

### Common Issues

1. **API Token Error**: Ensure your SOCRATA_API_TOKEN is set correctly
2. **Import Errors**: Make sure you're running from the project root
3. **Missing Data**: Some instruments may have limited historical data

### Debug Mode
Set Streamlit to development mode:
```bash
streamlit run streamlit_app.py --server.runOnSave true --server.fileWatcherType auto
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CFTC for providing public COT data
- Streamlit for the web framework
- Plotly for interactive visualizations