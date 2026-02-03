# Kalshi Market Scanner

A command-line tool that scans Kalshi prediction markets closing within the next 24 hours and displays pricing information.

## Features

- Fetches all active markets from Kalshi's production API
- Filters for markets closing within 24 hours
- Displays market title, yes/no prices, and time until close
- Calculates bid-ask spread and flags wide spreads (>$0.10)
- Clean terminal output with color formatting

## Requirements

- Python 3.10+
- Kalshi account with API credentials

## Setup

1. **Clone and install dependencies:**
   ```bash
   cd kalshi-scanner
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Generate Kalshi API credentials:**
   - Log in to [Kalshi](https://kalshi.com)
   - Navigate to Settings → API Keys
   - Generate a new API key (RSA key pair)
   - Save the private key as `private_key.pem` in this directory

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   - `KALSHI_API_KEY_ID`: Your API key ID from Kalshi
   - `KALSHI_PRIVATE_KEY_PATH`: Path to your private key file (default: `./private_key.pem`)

## Usage

```bash
python main.py
```

### Output

The scanner displays a table with:
- **Market**: Contract title
- **Yes Price**: Current yes bid price
- **No Price**: Implied no price (100 - yes)
- **Spread**: Bid-ask spread (flagged with `!` if > $0.10)
- **Time Left**: Time until market closes

## Configuration

Edit constants in `main.py` to customize:
- `HOURS_THRESHOLD`: Filter window (default: 24 hours)
- `SPREAD_THRESHOLD_CENTS`: Wide spread threshold (default: 10 cents)

## Project Structure

```
kalshi-scanner/
├── main.py           # Main scanner application
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
├── .env              # Your credentials (git-ignored)
├── private_key.pem   # Your private key (git-ignored)
└── README.md
```

## Error Handling

- Missing credentials: Clear error message with setup instructions
- API connection issues: Displayed with context
- Trading inactive: Warning shown but scan continues
