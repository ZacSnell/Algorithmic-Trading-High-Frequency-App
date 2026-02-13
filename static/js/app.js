let priceChart = null;
let pnlChart = null;
let selectedSymbol = 'AAPL';
let priceData = {};
let isRunning = true;

function initCharts() {
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Price',
                data: [],
                borderColor: '#00d4aa',
                borderWidth: 2,
                fill: false,
                pointRadius: 0,
                tension: 0.3
            }, {
                label: 'Prediction',
                data: [],
                borderColor: '#ffc107',
                borderWidth: 2,
                borderDash: [5, 5],
                fill: false,
                pointRadius: 0,
                tension: 0.3
            }, {
                label: 'SMA 20',
                data: [],
                borderColor: 'rgba(138, 43, 226, 0.5)',
                borderWidth: 1,
                fill: false,
                pointRadius: 0,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            plugins: {
                legend: {
                    labels: { color: '#8892a0', font: { size: 11 } }
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    grid: { color: 'rgba(30, 42, 58, 0.5)' },
                    ticks: { color: '#5a6577', font: { size: 10 } }
                }
            }
        }
    });

    const pnlCtx = document.getElementById('pnlChart').getContext('2d');
    pnlChart = new Chart(pnlCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
                data: [],
                borderColor: '#00d4aa',
                borderWidth: 2,
                fill: true,
                backgroundColor: 'rgba(0, 212, 170, 0.05)',
                pointRadius: 0,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            plugins: {
                legend: {
                    labels: { color: '#8892a0', font: { size: 11 } }
                }
            },
            scales: {
                x: { display: false },
                y: {
                    grid: { color: 'rgba(30, 42, 58, 0.5)' },
                    ticks: {
                        color: '#5a6577',
                        font: { size: 10 },
                        callback: v => '$' + v.toLocaleString()
                    }
                }
            }
        }
    });
}

function selectSymbol(symbol) {
    selectedSymbol = symbol;
    document.querySelectorAll('.ticker-item').forEach(el => {
        el.classList.toggle('active', el.dataset.symbol === symbol);
    });
    updatePriceChart();
}

function updatePriceChart() {
    fetch('/api/history/' + selectedSymbol)
        .then(r => r.json())
        .then(data => {
            const history = data.history;
            const pred = data.prediction;

            const labels = history.map((_, i) => i);
            const prices = history.map(h => h.price);

            let predData = new Array(prices.length).fill(null);
            predData[predData.length - 1] = prices[prices.length - 1];
            if (pred.prediction) {
                pred.prediction.forEach(p => {
                    predData.push(p);
                    labels.push(labels.length);
                });
            }

            let smaData = [];
            for (let i = 0; i < prices.length; i++) {
                if (i >= 19) {
                    let sum = 0;
                    for (let j = i - 19; j <= i; j++) sum += prices[j];
                    smaData.push(sum / 20);
                } else {
                    smaData.push(null);
                }
            }

            priceChart.data.labels = labels;
            priceChart.data.datasets[0].data = prices;
            priceChart.data.datasets[0].label = selectedSymbol + ' Price';
            priceChart.data.datasets[1].data = predData;
            priceChart.data.datasets[2].data = smaData;
            priceChart.update();
        });
}

function updateDashboard() {
    if (!isRunning) return;

    fetch('/api/tick')
        .then(r => r.json())
        .then(data => {
            updateTickers(data.ticks);
            updatePortfolio(data.portfolio);
            updatePredictions(data.predictions);
            updateTrades(data.trades);
            updatePriceChart();
            updatePnlChart();
        })
        .catch(err => console.error('Update error:', err));
}

function updateTickers(ticks) {
    const grid = document.getElementById('tickerGrid');
    grid.innerHTML = '';
    ticks.forEach(tick => {
        const changeClass = tick.change >= 0 ? 'positive' : 'negative';
        const changeSign = tick.change >= 0 ? '+' : '';
        const div = document.createElement('div');
        div.className = `ticker-item ${tick.symbol === selectedSymbol ? 'active' : ''}`;
        div.dataset.symbol = tick.symbol;
        div.onclick = () => selectSymbol(tick.symbol);
        div.innerHTML = `
            <div class="ticker-symbol">${tick.symbol}</div>
            <div class="ticker-price ${changeClass}">$${tick.price.toFixed(2)}</div>
            <div class="ticker-change ${changeClass}">${changeSign}${tick.change.toFixed(2)} (${changeSign}${tick.change_pct.toFixed(2)}%)</div>
        `;
        grid.appendChild(div);
    });
}

function updatePortfolio(portfolio) {
    document.getElementById('totalValue').textContent = '$' + portfolio.total_value.toLocaleString(undefined, {minimumFractionDigits: 2});
    document.getElementById('cashBalance').textContent = '$' + portfolio.cash.toLocaleString(undefined, {minimumFractionDigits: 2});
    document.getElementById('positionsValue').textContent = '$' + portfolio.positions_value.toLocaleString(undefined, {minimumFractionDigits: 2});

    const pnlEl = document.getElementById('pnl');
    const pnlPctEl = document.getElementById('pnlPct');
    const sign = portfolio.pnl >= 0 ? '+' : '';
    pnlEl.textContent = sign + '$' + portfolio.pnl.toLocaleString(undefined, {minimumFractionDigits: 2});
    pnlEl.className = 'stat-value ' + (portfolio.pnl >= 0 ? 'positive' : 'negative');
    pnlPctEl.textContent = sign + portfolio.pnl_pct.toFixed(2) + '%';
    pnlPctEl.className = 'stat-value ' + (portfolio.pnl_pct >= 0 ? 'positive' : 'negative');
}

function updatePredictions(predictions) {
    const grid = document.getElementById('predictionsGrid');
    grid.innerHTML = '';
    Object.entries(predictions).forEach(([symbol, pred]) => {
        const div = document.createElement('div');
        div.className = 'pred-item';
        div.innerHTML = `
            <div class="pred-symbol">${symbol}</div>
            <span class="signal-badge signal-${pred.signal}">${pred.signal}</span>
            <div style="margin-top:6px;font-size:13px;color:#e0e6ed">Confidence: ${pred.confidence}%</div>
            <div class="pred-indicators">
                <span>RSI: ${pred.indicators.rsi}</span>
                <span>Vol: ${pred.indicators.volatility.toFixed(2)}%</span>
                <span>SMA5: $${pred.indicators.sma_5}</span>
            </div>
        `;
        grid.appendChild(div);
    });
}

function updateTrades(trades) {
    const tbody = document.getElementById('tradesBody');
    tbody.innerHTML = '';
    trades.slice(0, 15).forEach(trade => {
        const tr = document.createElement('tr');
        const time = new Date(trade.timestamp * 1000).toLocaleTimeString();
        const pnl = trade.pnl !== undefined ? (trade.pnl >= 0 ? '+' : '') + '$' + trade.pnl.toFixed(2) : '-';
        tr.innerHTML = `
            <td>${trade.id}</td>
            <td class="action-${trade.action}">${trade.action}</td>
            <td>${trade.symbol}</td>
            <td>${trade.qty}</td>
            <td>$${trade.price.toFixed(2)}</td>
            <td class="${trade.pnl >= 0 ? 'positive' : 'negative'}">${pnl}</td>
            <td>${time}</td>
        `;
        tbody.appendChild(tr);
    });
}

function updatePnlChart() {
    fetch('/api/pnl')
        .then(r => r.json())
        .then(data => {
            const history = data.pnl_history;
            pnlChart.data.labels = history.map((_, i) => i);
            pnlChart.data.datasets[0].data = history;
            const color = history.length > 0 && history[history.length - 1] >= 100000 ? '#00d4aa' : '#ff4757';
            pnlChart.data.datasets[0].borderColor = color;
            pnlChart.data.datasets[0].backgroundColor = color.replace(')', ', 0.05)').replace('rgb', 'rgba');
            pnlChart.update();
        });
}

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    updateDashboard();
    setInterval(updateDashboard, 2000);
});
