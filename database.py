import sqlite3
import json
from datetime import datetime

DB_PATH = "trading.db"

def init_db():
    """Initialize database with tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Active trading rules (buy/sell orders)
    c.execute('''
        CREATE TABLE IF NOT EXISTS trading_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            rule_type TEXT NOT NULL,  -- 'buy' or 'sell'
            target_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'active',  -- active, executed, cancelled
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            executed_at TIMESTAMP
        )
    ''')
    
    # Portfolio holdings (paper trading)
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL,
            avg_buy_price REAL NOT NULL,
            current_value REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transaction history
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,  -- 'buy' or 'sell'
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_value REAL NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Database operations...
def add_trading_rule(symbol, rule_type, target_price, quantity):
    """Add new buy/sell rule"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO trading_rules (symbol, rule_type, target_price, quantity)
        VALUES (?, ?, ?, ?)
    ''', (symbol.upper(), rule_type, target_price, quantity))
    conn.commit()
    rule_id = c.lastrowid
    conn.close()
    return rule_id

def get_active_rules():
    """Get all active trading rules"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM trading_rules WHERE status = 'active'")
    rules = [dict(zip([key[0] for key in c.description], row)) for row in c.fetchall()]
    conn.close()
    return rules

def update_rule_status(rule_id, status):
    """Update rule status and execution time"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE trading_rules 
        SET status = ?, executed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (status, rule_id))
    conn.commit()
    conn.close()

def add_to_portfolio(symbol, quantity, price):
    """Add/update portfolio after buy"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if already exists
    c.execute("SELECT quantity, avg_buy_price FROM portfolio WHERE symbol = ?", (symbol,))
    existing = c.fetchone()
    
    if existing:
        old_qty, old_price = existing
        new_qty = old_qty + quantity
        # Weighted average price
        new_price = ((old_qty * old_price) + (quantity * price)) / new_qty
        c.execute('''
            UPDATE portfolio 
            SET quantity = ?, avg_buy_price = ?, last_updated = CURRENT_TIMESTAMP 
            WHERE symbol = ?
        ''', (new_qty, new_price, symbol))
    else:
        c.execute('''
            INSERT INTO portfolio (symbol, quantity, avg_buy_price)
            VALUES (?, ?, ?)
        ''', (symbol, quantity, price))
    
    conn.commit()
    conn.close()

def remove_from_portfolio(symbol, quantity, price):
    """Remove from portfolio after sell"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT quantity, avg_buy_price FROM portfolio WHERE symbol = ?", (symbol,))
    existing = c.fetchone()
    
    if existing and existing[0] >= quantity:
        new_qty = existing[0] - quantity
        if new_qty == 0:
            c.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol,))
        else:
            c.execute('''
                UPDATE portfolio 
                SET quantity = ?, last_updated = CURRENT_TIMESTAMP 
                WHERE symbol = ?
            ''', (new_qty, symbol))
        
        # Record profit/loss
        profit = (price - existing[1]) * quantity
        c.execute('''
            INSERT INTO transactions (symbol, action, quantity, price, total_value)
            VALUES (?, 'sell', ?, ?, ?)
        ''', (symbol, quantity, price, quantity * price))
        
        conn.commit()
        conn.close()
        return True, profit
    conn.close()
    return False, 0

def get_portfolio():
    """Get current portfolio with live P&L"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM portfolio ORDER BY last_updated DESC")
    portfolio = [dict(zip([key[0] for key in c.description], row)) for row in c.fetchall()]
    conn.close()
    return portfolio

def get_transactions(limit=50):
    """Get recent transactions"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY executed_at DESC LIMIT ?", (limit,))
    txs = [dict(zip([key[0] for key in c.description], row)) for row in c.fetchall()]
    conn.close()
    return txs