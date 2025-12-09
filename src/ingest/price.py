"""
Bitcoin price data collector using CoinGecko API.

This module fetches current price snapshots and historical price data
for Bitcoin from the CoinGecko API.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests

from src.core import get_logger, get_settings

logger = get_logger(__name__)


def fetch_current_price() -> Dict[str, Any]:
    """
    Fetch current Bitcoin price with 24h change percentage.
    
    Makes a request to CoinGecko to get current price and 24h price change.
    This is optimized for displaying current stats on the dashboard.
    
    Returns:
        Dictionary with keys:
        - price: Current Bitcoin price in USD (float)
        - price_change_24h: 24-hour price change percentage (float)
        - volume_24h: 24-hour trading volume in USD (float)
        - last_updated: Timestamp of the data (datetime)
        
    Example:
        >>> data = fetch_current_price()
        >>> print(f"BTC: ${data['price']:,.2f} ({data['price_change_24h']:+.2f}%)")
        BTC: $43,250.00 (+4.25%)
    """
    config = get_settings()
    base_url = str(config.COINGECKO_BASE)
    
    # Construct API endpoint with 24h change
    endpoint = f"{base_url}/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'usd',
        'include_24hr_vol': 'true',
        'include_24hr_change': 'true',
        'include_last_updated_at': 'true'
    }
    
    max_retries = 3
    backoff_factor = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Fetching current price data",
                extra={'attempt': attempt + 1, 'endpoint': endpoint}
            )
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            btc_data = data.get('bitcoin', {})
            
            price = btc_data.get('usd')
            price_change_24h = btc_data.get('usd_24h_change')
            volume_24h = btc_data.get('usd_24h_vol')
            last_updated = btc_data.get('last_updated_at')
            
            if price is None:
                raise ValueError("Missing price data in API response")
            
            result = {
                'price': float(price),
                'price_change_24h': float(price_change_24h) if price_change_24h is not None else 0.0,
                'volume_24h': float(volume_24h) if volume_24h is not None else 0.0,
                'last_updated': datetime.fromtimestamp(last_updated) if last_updated else datetime.utcnow()
            }
            
            logger.info(
                f"Current price fetched",
                extra={
                    'price': result['price'],
                    'change_24h': result['price_change_24h']
                }
            )
            
            return result
            
        except requests.exceptions.Timeout as e:
            logger.warning(
                f"Request timeout",
                extra={'attempt': attempt + 1, 'error': str(e)}
            )
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Request failed",
                extra={'attempt': attempt + 1, 'error': str(e)}
            )
        except (ValueError, KeyError) as e:
            logger.error(
                f"Error parsing API response",
                extra={'attempt': attempt + 1, 'error': str(e)}
            )
        
        if attempt < max_retries - 1:
            sleep_time = backoff_factor ** attempt
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
    
    raise requests.exceptions.RequestException(
        f"Failed to fetch current price after {max_retries} attempts"
    )


def fetch_price_snapshot() -> Dict[str, Any]:
    """
    Fetch current Bitcoin price and 24h volume from CoinGecko API.
    
    Makes a request to the CoinGecko simple/price endpoint to get
    the current Bitcoin price in USD and 24-hour trading volume.
    
    Returns:
        Dictionary with keys:
        - ts: Current timestamp in UTC (datetime)
        - price: Bitcoin price in USD (float)
        - volume: 24-hour trading volume in USD (float)
        
    Raises:
        requests.exceptions.RequestException: If API request fails after retries
        
    Example:
        >>> snapshot = fetch_price_snapshot()
        >>> print(f"BTC Price: ${snapshot['price']:,.2f}")
    """
    config = get_settings()
    base_url = str(config.COINGECKO_BASE)
    
    # Construct API endpoint
    endpoint = f"{base_url}/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'usd',
        'include_24hr_vol': 'true'
    }
    
    # Retry configuration
    max_retries = 3
    backoff_factor = 2  # Exponential backoff: 1s, 2s, 4s
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Fetching price snapshot",
                extra={'attempt': attempt + 1, 'endpoint': endpoint}
            )
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract price and volume
            btc_data = data.get('bitcoin', {})
            price = btc_data.get('usd')
            volume = btc_data.get('usd_24h_vol')
            
            if price is None or volume is None:
                raise ValueError("Missing price or volume data in API response")
            
            result = {
                'ts': datetime.utcnow(),
                'price': float(price),
                'volume': float(volume)
            }
            
            logger.info(
                f"Price snapshot fetched",
                extra={
                    'price': result['price'],
                    'volume': result['volume']
                }
            )
            
            return result
            
        except requests.exceptions.Timeout as e:
            logger.warning(
                f"Request timeout",
                extra={
                    'attempt': attempt + 1,
                    'max_retries': max_retries,
                    'error': str(e)
                }
            )
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Request failed",
                extra={
                    'attempt': attempt + 1,
                    'max_retries': max_retries,
                    'error': str(e),
                    'status_code': getattr(e.response, 'status_code', None)
                }
            )
        except (ValueError, KeyError) as e:
            logger.error(
                f"Error parsing API response",
                extra={
                    'attempt': attempt + 1,
                    'error': str(e)
                }
            )
        
        # Don't sleep after last attempt
        if attempt < max_retries - 1:
            sleep_time = backoff_factor ** attempt
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
    
    # All retries exhausted
    raise requests.exceptions.RequestException(
        f"Failed to fetch price snapshot after {max_retries} attempts"
    )


def backfill_prices(hours: int) -> List[Dict[str, Any]]:
    """
    Fetch historical hourly Bitcoin price data from CoinGecko.
    
    Retrieves hourly price candles for the specified time period.
    Uses the CoinGecko market_chart endpoint which provides OHLC data.
    
    Args:
        hours: Number of hours of historical data to fetch (max ~90 days)
        
    Returns:
        List of dictionaries, each containing:
        - ts: Timestamp for the price point (datetime)
        - price: Bitcoin price in USD (float)
        - volume: Trading volume (float, if available)
        
    Raises:
        requests.exceptions.RequestException: If API request fails after retries
        
    Example:
        >>> prices = backfill_prices(24)  # Last 24 hours
        >>> print(f"Fetched {len(prices)} hourly price points")
    """
    config = get_settings()
    base_url = str(config.COINGECKO_BASE)
    
    # Convert hours to days for CoinGecko API
    days = max(1, hours / 24)
    
    # Construct API endpoint
    endpoint = f"{base_url}/coins/bitcoin/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'hourly' if days <= 90 else 'daily'
    }
    
    # Retry configuration
    max_retries = 3
    backoff_factor = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Fetching historical prices",
                extra={
                    'attempt': attempt + 1,
                    'hours': hours,
                    'days': days,
                    'endpoint': endpoint
                }
            )
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=30  # Longer timeout for historical data
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract prices and volumes
            prices_raw = data.get('prices', [])
            volumes_raw = data.get('total_volumes', [])
            
            if not prices_raw:
                raise ValueError("No price data in API response")
            
            # Create volume lookup dict (timestamp -> volume)
            volume_dict = {int(ts): vol for ts, vol in volumes_raw}
            
            # Process price data
            results = []
            for ts_ms, price in prices_raw:
                ts_seconds = int(ts_ms / 1000)
                
                # Convert timestamp to datetime
                dt = datetime.utcfromtimestamp(ts_seconds)
                
                # Get corresponding volume
                volume = volume_dict.get(int(ts_ms), 0.0)
                
                results.append({
                    'ts': dt,
                    'price': float(price),
                    'volume': float(volume)
                })
            
            logger.info(
                f"Historical prices fetched",
                extra={
                    'count': len(results),
                    'hours_requested': hours
                }
            )
            
            return results
            
        except requests.exceptions.Timeout as e:
            logger.warning(
                f"Request timeout",
                extra={
                    'attempt': attempt + 1,
                    'max_retries': max_retries,
                    'error': str(e)
                }
            )
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Request failed",
                extra={
                    'attempt': attempt + 1,
                    'max_retries': max_retries,
                    'error': str(e),
                    'status_code': getattr(e.response, 'status_code', None)
                }
            )
        except (ValueError, KeyError) as e:
            logger.error(
                f"Error parsing API response",
                extra={
                    'attempt': attempt + 1,
                    'error': str(e)
                }
            )
        
        # Don't sleep after last attempt
        if attempt < max_retries - 1:
            sleep_time = backoff_factor ** attempt
            logger.info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
    
    # All retries exhausted
    raise requests.exceptions.RequestException(
        f"Failed to fetch historical prices after {max_retries} attempts"
    )


# Test block for development
if __name__ == "__main__":
    from src.data import init_db, save_prices, get_recent_prices
    
    # Initialize logger and config
    logger = get_logger(__name__)
    config = get_settings()
    
    print("💰 Testing Price Collector")
    print("=" * 60)
    
    # Initialize database
    init_db(config.DB_URL)
    
    # Test 1: Fetch current price snapshot
    print("\n📊 Test 1: Fetch current price snapshot")
    print("-" * 60)
    try:
        snapshot = fetch_price_snapshot()
        print(f"✅ Current BTC Price: ${snapshot['price']:,.2f}")
        print(f"✅ 24h Volume: ${snapshot['volume']:,.0f}")
        print(f"✅ Timestamp: {snapshot['ts']}")
        
        # Save to database
        save_prices([snapshot])
        print(f"✅ Saved snapshot to database")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Backfill historical prices
    print("\n📈 Test 2: Backfill historical prices (last 48 hours)")
    print("-" * 60)
    try:
        historical = backfill_prices(48)
        print(f"✅ Fetched {len(historical)} hourly price points")
        
        if historical:
            print(f"\n📊 Sample data points:")
            for i, point in enumerate(historical[:3], 1):
                print(f"  {i}. {point['ts']} - ${point['price']:,.2f} (vol: ${point['volume']:,.0f})")
            
            # Save to database
            save_prices(historical)
            print(f"\n✅ Saved {len(historical)} price points to database")
            
            # Retrieve and verify
            retrieved = get_recent_prices(hours=48)
            print(f"✅ Retrieved {len(retrieved)} price points from database")
            
            # Check price range
            prices = [p['price'] for p in retrieved]
            if prices:
                print(f"\n📊 Price statistics (last 48h):")
                print(f"  Min: ${min(prices):,.2f}")
                print(f"  Max: ${max(prices):,.2f}")
                print(f"  Avg: ${sum(prices)/len(prices):,.2f}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test retry logic with invalid endpoint
    print("\n🔄 Test 3: Retry logic (simulated failure)")
    print("-" * 60)
    print("(Skipping - would test with invalid API key)")
    
    print("\n" + "=" * 60)
    print("✅ Price collector tests complete!")
