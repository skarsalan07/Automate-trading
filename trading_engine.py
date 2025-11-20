import finnhub
import os
from dotenv import load_dotenv
from database import (
    get_active_rules, update_rule_status, 
    add_to_portfolio, remove_from_portfolio
)

load_dotenv()
finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))

def get_real_time_quote(symbol):
    """Fetch real-time stock quote"""
    try:
        quote = finnhub_client.quote(symbol.upper())
        if quote and quote['c'] != 0:  # 'c' = current price
            return {
                'symbol': symbol.upper(),
                'price': quote['c'],
                'change': quote['d'],
                'change_percent': quote['dp'],
                'high': quote['h'],
                'low': quote['l'],
                'open': quote['o'],
                'previous_close': quote['pc']
            }
        return None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def check_and_execute_trades():
    """Core auto-trading logic - runs every 5 seconds"""
    print("🔍 Checking trading rules...")
    rules = get_active_rules()
    
    for rule in rules:
        symbol = rule['symbol']
        quote = get_real_time_quote(symbol)
        
        if not quote:
            continue
            
        current_price = quote['price']
        target_price = rule['target_price']
        should_execute = False
        
        # Check conditions
        if rule['rule_type'] == 'buy' and current_price <= target_price:
            print(f"🟢 BUY TRIGGERED: {symbol} at ${current_price} (target: ${target_price})")
            should_execute = True
        elif rule['rule_type'] == 'sell' and current_price >= target_price:
            print(f"🔴 SELL TRIGGERED: {symbol} at ${current_price} (target: ${target_price})")
            should_execute = True
        
        if should_execute:
            try:
                # Execute paper trade
                if rule['rule_type'] == 'buy':
                    add_to_portfolio(symbol, rule['quantity'], current_price)
                
                elif rule['rule_type'] == 'sell':
                    success, profit = remove_from_portfolio(symbol, rule['quantity'], current_price)
                    if not success:
                        print(f"❌ SELL FAILED: Not enough {symbol} in portfolio")
                        continue
                
                # Mark rule as executed
                update_rule_status(rule['id'], 'executed')
                print(f"✅ TRADE EXECUTED: {rule['rule_type'].upper()} {rule['quantity']} shares of {symbol}")
                
            except Exception as e:
                print(f"❌ EXECUTION ERROR: {e}")
                update_rule_status(rule['id'], 'failed')