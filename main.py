#!/usr/bin/env python3
"""
Kalshi Market Scanner
Scans active markets closing within 24 hours and displays pricing info.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from kalshi_python_sync import ApiException, Configuration, KalshiClient

# Constants
HOURS_THRESHOLD = 24
SPREAD_THRESHOLD_CENTS = 10  # Flag spreads > $0.10


def load_credentials() -> tuple[str, str]:
    """Load API credentials from environment."""
    load_dotenv()

    api_key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")

    if not api_key_id:
        raise ValueError("KALSHI_API_KEY_ID not set in environment")
    if not private_key_path:
        raise ValueError("KALSHI_PRIVATE_KEY_PATH not set in environment")

    key_path = Path(private_key_path)
    if not key_path.exists():
        raise FileNotFoundError(f"Private key not found: {private_key_path}")

    private_key = key_path.read_text()
    return api_key_id, private_key


def create_client(api_key_id: str, private_key: str) -> KalshiClient:
    """Initialize and return Kalshi API client."""
    config = Configuration(
        host="https://api.elections.kalshi.com/trade-api/v2"
    )
    config.api_key_id = api_key_id
    config.private_key_pem = private_key

    return KalshiClient(config)


def get_markets_closing_soon(client: KalshiClient, hours: int = HOURS_THRESHOLD) -> list:
    """Fetch markets closing within the specified hours using API-level filtering."""
    now = datetime.now(timezone.utc)
    max_close_ts = int((now.timestamp() + hours * 3600))
    min_close_ts = int(now.timestamp())

    markets = []
    cursor = None

    while True:
        response = client.get_markets(
            status="open",
            min_close_ts=min_close_ts,
            max_close_ts=max_close_ts,
            cursor=cursor,
            limit=200
        )
        markets.extend(response.markets)

        cursor = response.cursor
        if not cursor:
            break

    # Enrich with time calculations and sort
    result = []
    for market in markets:
        close_time = market.close_time
        if isinstance(close_time, str):
            close_time = datetime.fromisoformat(close_time.replace("Z", "+00:00"))

        hours_until_close = (close_time - now).total_seconds() / 3600

        if hours_until_close > 0:
            result.append({
                "market": market,
                "hours_until_close": hours_until_close,
                "close_time": close_time
            })

    result.sort(key=lambda x: x["hours_until_close"])
    return result


def format_time_until(hours: float) -> str:
    """Format hours into human-readable time string."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes}m"
    elif hours < 24:
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m}m"
    else:
        days = int(hours / 24)
        h = int(hours % 24)
        return f"{days}d {h}h"


def cents_to_dollars(cents: int) -> str:
    """Convert cents to dollar string."""
    return f"${cents / 100:.2f}"


def calculate_spread(market) -> tuple[int, bool]:
    """
    Calculate bid-ask spread from market data.
    Returns (spread_in_cents, is_wide).
    """
    yes_bid = getattr(market, "yes_bid", None) or 0
    yes_ask = getattr(market, "yes_ask", None) or 0

    if yes_bid and yes_ask:
        spread = yes_ask - yes_bid
    else:
        spread = 0

    is_wide = spread > SPREAD_THRESHOLD_CENTS
    return spread, is_wide


def display_markets(markets_data: list, console: Console) -> None:
    """Display markets in a formatted table."""
    if not markets_data:
        console.print("[yellow]No markets closing in the next 24 hours.[/yellow]")
        return

    table = Table(title=f"Markets Closing Within {HOURS_THRESHOLD} Hours")

    table.add_column("Market", style="cyan", max_width=50)
    table.add_column("Yes Price", justify="right", style="green")
    table.add_column("No Price", justify="right", style="red")
    table.add_column("Spread", justify="right")
    table.add_column("Time Left", justify="right", style="yellow")

    wide_spread_count = 0

    for data in markets_data:
        market = data["market"]
        hours = data["hours_until_close"]

        # Get prices (in cents) - prefer bid, fallback to last_price
        yes_price = market.yes_bid or market.last_price or 0
        no_price = market.no_bid or (100 - yes_price if yes_price else 0)

        # Calculate spread
        spread, is_wide = calculate_spread(market)
        spread_str = cents_to_dollars(spread) if spread > 0 else "-"
        if is_wide:
            spread_str = f"[bold red]{spread_str} ![/bold red]"
            wide_spread_count += 1

        # Truncate long titles
        title = market.title
        if len(title) > 47:
            title = title[:47] + "..."

        table.add_row(
            title,
            cents_to_dollars(yes_price) if yes_price else "-",
            cents_to_dollars(no_price) if no_price else "-",
            spread_str,
            format_time_until(hours)
        )

    console.print(table)
    console.print(f"\n[bold]Total markets:[/bold] {len(markets_data)}")

    if wide_spread_count > 0:
        console.print(
            f"[bold red]Wide spreads (>{cents_to_dollars(SPREAD_THRESHOLD_CENTS)}):[/bold red] "
            f"{wide_spread_count}"
        )


def main():
    console = Console()

    try:
        console.print("[bold]Kalshi Market Scanner[/bold]\n")

        # Load credentials
        console.print("Loading credentials...", style="dim")
        api_key_id, private_key = load_credentials()

        # Create client
        console.print("Connecting to Kalshi API...", style="dim")
        client = create_client(api_key_id, private_key)

        # Verify connection by checking exchange status
        status = client.get_exchange_status()
        if not status.trading_active:
            console.print("[yellow]Warning: Trading is currently inactive[/yellow]")

        # Fetch markets closing soon (API-level filtering for speed)
        console.print(f"Fetching markets closing within {HOURS_THRESHOLD} hours...", style="dim")
        closing_soon = get_markets_closing_soon(client, HOURS_THRESHOLD)
        console.print(f"Found {len(closing_soon)} markets\n", style="dim")

        # Display results
        display_markets(closing_soon, console)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nMake sure your .env file points to a valid private key.")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        console.print("\nCopy .env.example to .env and add your credentials.")
        sys.exit(1)
    except ApiException as e:
        console.print(f"[red]API Error ({e.status}):[/red] {e.reason}")
        if e.status == 401:
            console.print("\nCheck that your API key ID and private key are correct.")
        elif e.status == 403:
            console.print("\nYour API key may not have permission for this operation.")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
