let currentSymbol = '';

// Fetch real-time quote
async function fetchQuote() {
    const symbol = document.getElementById('symbolInput').value.trim().toUpperCase();
    if (!symbol) return alert('Enter a stock symbol');
    
    currentSymbol = symbol;
    const res = await fetch(`/api/quote/${symbol}`);
    const data = await res.json();
    
    if (data.error) return alert(data.error);
    
    document.getElementById('quoteDisplay').innerHTML = `
        <div class="bg-gray-700 p-4 rounded-lg">
            <div class="flex justify-between items-center">
                <h3 class="text-2xl font-bold">${data.symbol}</h3>
                <span class="text-3xl font-bold ${
                    data.change >= 0 ? 'text-green-400' : 'text-red-400'
                }">$${data.price.toFixed(2)}</span>
            </div>
            <div class="grid grid-cols-4 gap-2 mt-3 text-sm">
                <div>Open: $${data.open.toFixed(2)}</div>
                <div>High: $${data.high.toFixed(2)}</div>
                <div>Low: $${data.low.toFixed(2)}</div>
                <div>Prev: $${data.previous_close.toFixed(2)}</div>
            </div>
            <div class="mt-2 ${
                data.change >= 0 ? 'text-green-400' : 'text-red-400'
            }">
                ${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)} 
                (${data.change_percent >= 0 ? '+' : ''}${data.change_percent.toFixed(2)}%)
            </div>
        </div>
    `;
    document.getElementById('quoteDisplay').classList.remove('hidden');
}

// Create trading rule
async function createRule() {
    if (!currentSymbol) return alert('Search a stock first');
    
    const ruleData = {
        symbol: currentSymbol,
        type: document.getElementById('ruleType').value,
        targetPrice: document.getElementById('targetPrice').value,
        quantity: document.getElementById('quantity').value
    };
    
    if (!ruleData.targetPrice || !ruleData.quantity) {
        return alert('Fill all fields');
    }
    
    const res = await fetch('/api/rules', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(ruleData)
    });
    
    const result = await res.json();
    if (result.success) {
        alert('✅ Rule created successfully!');
        document.getElementById('targetPrice').value = '';
        document.getElementById('quantity').value = '';
        loadRules();
    } else {
        alert('❌ Error: ' + result.error);
    }
}

// Load active rules
async function loadRules() {
    const res = await fetch('/api/rules');
    const rules = await res.json();
    const container = document.getElementById('rulesList');
    
    if (rules.length === 0) {
        container.innerHTML = '<p class="text-gray-400">No active rules</p>';
        return;
    }
    
    container.innerHTML = rules.map(rule => `
        <div class="bg-gray-700 p-3 rounded-lg border-l-4 ${
            rule['rule_type'] === 'buy' ? 'border-green-500' : 'border-red-500'
        }">
            <div class="flex justify-between">
                <span class="font-bold">${rule['symbol']}</span>
                <span class="text-sm ${
                    rule['rule_type'] === 'buy' ? 'text-green-400' : 'text-red-400'
                }">${rule['rule_type'].toUpperCase()}</span>
            </div>
            <div class="text-sm mt-1">
                Target: $${rule['target_price']} | Qty: ${rule['quantity']}
            </div>
        </div>
    `).join('');
}

// Load portfolio
async function loadPortfolio() {
    const res = await fetch('/api/portfolio');
    const portfolio = await res.json();
    const container = document.getElementById('portfolioList');
    
    if (portfolio.length === 0) {
        container.innerHTML = '<p class="text-gray-400">No holdings</p>';
        return;
    }
    
    container.innerHTML = portfolio.map(item => `
        <div class="bg-gray-700 p-3 rounded-lg">
            <div class="flex justify-between">
                <span class="font-bold">${item['symbol']}</span>
                <span>Qty: ${item['quantity']}</span>
            </div>
            <div class="text-sm mt-1">
                Avg Price: $${item['avg_buy_price'].toFixed(2)} | 
                Value: $${(item['quantity'] * item['avg_buy_price']).toFixed(2)}
            </div>
        </div>
    `).join('');
}

// Load transactions
async function loadTransactions() {
    const res = await fetch('/api/transactions');
    const txs = await res.json();
    const container = document.getElementById('transactionsList');
    
    if (txs.length === 0) {
        container.innerHTML = '<p class="text-gray-400">No transactions yet</p>';
        return;
    }
    
    container.innerHTML = `
        <table class="w-full text-sm">
            <thead>
                <tr class="text-gray-400">
                    <th class="text-left">Symbol</th>
                    <th>Action</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Total</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
                ${txs.map(tx => `
                    <tr class="border-t border-gray-700">
                        <td class="py-2">${tx['symbol']}</td>
                        <td class="text-center ${
                            tx['action'] === 'buy' ? 'text-green-400' : 'text-red-400'
                        }">${tx['action'].toUpperCase()}</td>
                        <td class="text-center">${tx['quantity']}</td>
                        <td class="text-center">$${tx['price'].toFixed(2)}</td>
                        <td class="text-center">$${tx['total_value'].toFixed(2)}</td>
                        <td class="text-center">${new Date(tx['executed_at']).toLocaleTimeString()}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Auto-refresh dashboard
setInterval(() => {
    loadRules();
    loadPortfolio();
    loadTransactions();
}, 5000);

// Initial load
loadRules();
loadPortfolio();
loadTransactions();