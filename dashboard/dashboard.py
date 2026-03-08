"""
dashboard.py - APEX TRADE LAB Dashboard (v2 — Light Theme Platform)

9 Pages: Dashboard | Trades | P&L | Trade Tools | Market Regime | Stress Test | AI Analyst | Learn | Community
Light theme. Educational tone. Human-readable trade descriptions.
"""

import json, logging
from datetime import datetime
from pathlib import Path
from typing import List
import numpy as np, pandas as pd

logger = logging.getLogger(__name__)

# =====================================================================
# MAIN GENERATOR
# =====================================================================

def generate_dashboard(equity_history, trade_log, signal_log, stats,
                       benchmark_data, config, stress_results=None, social_posts=None):
    D = [r["date"] for r in equity_history]
    EQ = [r["equity"] for r in equity_history]
    TA = [r.get("tqqq_alloc",0) for r in equity_history]
    SA = [r.get("sqqq_alloc",0) for r in equity_history]
    CA = [r.get("cash_alloc",100) for r in equity_history]
    NX = [r.get("ndx_close",0) for r in equity_history]
    S20 = [r.get("sma20") for r in equity_history]
    S250 = [r.get("sma250") for r in equity_history]
    RG = [r.get("regime","") for r in equity_history]
    RSI = [r.get("rsi",50) for r in equity_history]
    E20 = [r.get("ext_sma20",0) for r in equity_history]
    E250 = [r.get("ext_sma250",0) for r in equity_history]
    cap = stats.get("starting_capital",100000)
    BN = _nb(benchmark_data, D, cap)

    bd,bp,bl,sd,sp,sl=[],[],[],[],[],[]
    for t in trade_log:
        lb=f"{_human_trade(t)}<br>${t['value']:,.0f}"
        (bd if t["action"]=="BUY" else sd).append(t["date"])
        (bp if t["action"]=="BUY" else sp).append(t["ndx_close"])
        (bl if t["action"]=="BUY" else sl).append(lb)

    la = equity_history[-1] if equity_history else {}
    rstat = stats.get("regime_stats",{})
    trans = _rtrans(equity_history)
    br = config.get("branding",{})
    stress = stress_results or []
    social = social_posts or []
    rc = 'bull' if 'UP' in la.get('regime','') else 'bear'

    # Regime map data: date + regime color
    regime_map_data = json.dumps([{"d":D[i],"r":RG[i],"rsi":RSI[i],"e250":E250[i]} for i in range(len(D))])

    # Chat context
    cd = json.dumps({"latest":la,"stats":{k:v for k,v in stats.items() if k!="regime_stats"},
        "regime_stats":rstat,"transitions":trans[-10:],"recent_trades":trade_log[-20:],
        "equity_tail":equity_history[-15:]},default=str)

    # Trade descriptions humanized
    recent50 = trade_log[-50:]

    # P&L calculations
    pnl_data = _calc_pnl(equity_history, trade_log)

    return f'''{_css(br)}
<body>
<header>
    <div class="logo">&#9889; APEX TRADE LAB</div>
    <div class="tagline">Systematic Trading Research Platform</div>
    <div class="live-badge"><span class="dot"></span> Paper Trading &bull; {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</div>
</header>

<nav>
    <button class="on" onclick="go('dash',this)">Dashboard</button>
    <button onclick="go('trades',this)">Trades</button>
    <button onclick="go('pnl',this)">P&amp;L</button>
    <button onclick="go('tools',this)">Trade Tools</button>
    <button onclick="go('regime',this)">Market Regime</button>
    <button onclick="go('stress',this)">Stress Test</button>
    <button onclick="go('ai',this)">AI Analyst</button>
    <button onclick="go('learn',this)">Learn</button>
    <div class="dropdown">
        <button onclick="this.parentElement.classList.toggle('open')">Community &#9662;</button>
        <div class="dropdown-menu">
            <a onclick="go('community',document.querySelector('[onclick*=community]'));document.querySelector('.dropdown').classList.remove('open')">Subscribe</a>
            <a onclick="go('vip',document.querySelector('[onclick*=vip]'));document.querySelector('.dropdown').classList.remove('open')">VIP Access</a>
            <a onclick="go('services',document.querySelector('[onclick*=services]'));document.querySelector('.dropdown').classList.remove('open')">Services</a>
        </div>
    </div>
    <button onclick="go('community',this)" style="display:none"></button>
    <button onclick="go('vip',this)" style="display:none"></button>
    <button onclick="go('services',this)" style="display:none"></button>
</nav>

<!-- ===== DASHBOARD ===== -->
<div id="dash" class="pg on">

<!-- Current Signal Card -->
<div class="signal-card {rc}">
    <div class="signal-header">CURRENT SIGNAL</div>
    <div class="signal-grid">
        <div class="signal-regime">
            <div class="signal-label">Regime</div>
            <div class="signal-value {rc}">{la.get('regime','—')}</div>
        </div>
        <div class="signal-action">
            <div class="signal-label">Action</div>
            <div class="signal-value {rc}">{_action_text(la)}</div>
        </div>
        <div class="signal-alloc">
            <div class="alloc-bars">
                <div class="alloc-item"><span class="alloc-label">TQQQ</span><div class="alloc-bar"><div class="alloc-fill bull" style="width:{la.get('tqqq_alloc',0)}%"></div></div><span class="alloc-pct">{la.get('tqqq_alloc',0):.0f}%</span></div>
                <div class="alloc-item"><span class="alloc-label">SQQQ</span><div class="alloc-bar"><div class="alloc-fill bear" style="width:{la.get('sqqq_alloc',0)}%"></div></div><span class="alloc-pct">{la.get('sqqq_alloc',0):.0f}%</span></div>
                <div class="alloc-item"><span class="alloc-label">Cash</span><div class="alloc-bar"><div class="alloc-fill cash" style="width:{la.get('cash_alloc',100)}%"></div></div><span class="alloc-pct">{la.get('cash_alloc',100):.0f}%</span></div>
            </div>
        </div>
        <div class="signal-meta">
            <div class="signal-label">Active Strategies</div>
            <div style="font-size:13px;color:#444">{la.get('active_strategies','None')}</div>
            <div class="signal-label" style="margin-top:8px">NDX {la.get('ndx_close',0):,.0f} &bull; RSI {la.get('rsi',50):.0f} &bull; vs SMA250: {la.get('ext_sma250',0):+.1f}%</div>
        </div>
    </div>
    <div class="signal-reason">
        <strong>Why this signal:</strong> {_human_reason(la)}
    </div>
    <div class="signal-next">Next review: {_next_review_time()}</div>
</div>

<!-- Stats -->
<div class="stats-row">
    <div class="stat"><div class="stat-l">Portfolio {_tip('Current total value of the paper portfolio.')}</div><div class="stat-v bull">${stats.get('current_equity',0):,.0f}</div></div>
    <div class="stat"><div class="stat-l">Return {_tip('Total % gain/loss since simulation started.')}</div><div class="stat-v {'bull' if stats.get('total_return_pct',0)>=0 else 'bear'}">{stats.get('total_return_pct',0):+.1f}%</div></div>
    <div class="stat"><div class="stat-l">CAGR {_tip('Compound Annual Growth Rate — annualised return.')}</div><div class="stat-v">{stats.get('cagr_pct',0):+.1f}%</div></div>
    <div class="stat"><div class="stat-l">Sharpe {_tip('Risk-adjusted return. Above 1.0 is good. Above 2.0 is excellent.')}</div><div class="stat-v">{stats.get('sharpe_ratio',0):.2f}</div></div>
    <div class="stat"><div class="stat-l">Max DD {_tip('Largest peak-to-trough decline. Lower is better.')}</div><div class="stat-v bear">{stats.get('max_drawdown_pct',0):.1f}%</div></div>
    <div class="stat"><div class="stat-l">Win Rate {_tip('Percentage of closed trades that were profitable.')}</div><div class="stat-v">{stats.get('win_rate_pct',0):.0f}%</div></div>
</div>

<div class="card"><h2>Equity Curve vs QQQ Benchmark</h2><div id="eq-c"></div></div>
<div class="card"><h2>NDX Price Action — Signals &amp; Regime</h2>
    <p class="desc">Green triangles = buy entries. Red = sell exits. Background shading indicates market regime.</p>
    <div id="nx-c"></div>
    <div class="regime-strip" id="regime-strip"></div>
</div>
<div class="card"><h2>Portfolio Allocation</h2><div id="al-c"></div></div>
</div>

<!-- ===== TRADES ===== -->
<div id="trades" class="pg">
<div class="card"><h2>Trade History</h2>
<p class="desc">Every trade the system has made, with the strategy that triggered it and why.</p>
<div class="tbl-wrap"><table><thead><tr><th>Date</th><th>Type</th><th>Ticker</th><th>Side</th><th>Shares</th><th>Price</th><th>Value</th><th>P&amp;L</th><th>Strategy</th><th>What Happened</th><th>Regime</th></tr></thead>
<tbody>{''.join(_trade_row_human(t) for t in reversed(recent50))}</tbody></table></div></div></div>

<!-- ===== P&L ===== -->
<div id="pnl" class="pg">
<div class="card"><h2>Profit &amp; Loss Summary</h2>
<div class="stats-row">
    <div class="stat"><div class="stat-l">Total P&amp;L</div><div class="stat-v {'bull' if pnl_data['total_pnl']>=0 else 'bear'}">${pnl_data['total_pnl']:+,.0f}</div></div>
    <div class="stat"><div class="stat-l">Winning Trades</div><div class="stat-v bull">{stats.get('winning_trades',0)}</div></div>
    <div class="stat"><div class="stat-l">Losing Trades</div><div class="stat-v bear">{stats.get('losing_trades',0)}</div></div>
    <div class="stat"><div class="stat-l">Trades / Month</div><div class="stat-v">~{stats.get('trades_per_month',0):.0f}</div></div>
</div></div>
{_social_posts_section(social)}
</div>

<!-- ===== TRADE TOOLS ===== -->
<div id="tools" class="pg">
<div class="card"><h2>Position Sizing Calculator</h2>
<div class="calc-grid"><div class="calc-in">
<div class="fg"><label>Account ($)</label><input type="number" id="psa" value="15000"></div>
<div class="fg"><label>Risk %</label><input type="number" id="psr" value="2.0" step="0.5"></div>
<div class="fg"><label>Entry ($)</label><input type="number" id="pse" value="75" step="0.01"></div>
<div class="fg"><label>Stop ($)</label><input type="number" id="pss" value="71" step="0.01"></div>
<div class="fg"><label>Ticker</label><select id="psi"><option>TQQQ</option><option>SQQQ</option></select></div>
<button class="btn" onclick="cPos()">Calculate</button></div>
<div class="calc-out" id="pso"><div class="placeholder">Enter values and click Calculate</div></div></div></div>

<div class="card"><h2>Stop Loss Framework</h2>
<div class="grid-3">
<div class="card-inner"><h3>1. ATR Dynamic Stop</h3><p class="desc">Adapts to market volatility. Wider in volatile markets, tighter in calm ones.</p>
<div class="formula">Stop = Entry − (ATR × Multiplier)</div>
<div class="fg"><label>ATR</label><input type="number" id="sla" value="{round(la.get('ndx_close',20000)*0.012,2)}" step="0.01"></div>
<div class="fg"><label>Multiplier</label><select id="slam"><option value="1.5">1.5× Tight</option><option value="2.0" selected>2.0× Standard</option><option value="2.5">2.5× Wide</option></select></div>
<button class="btn-s" onclick="cATR()">Calculate</button><div id="slar" class="result"></div></div>

<div class="card-inner"><h3>2. Fixed % Stop</h3><p class="desc">Simple and predictable. Good for beginners.</p>
<div class="formula">Stop = Entry × (1 − %)</div>
<div class="fg"><label>Entry ($)</label><input type="number" id="slfe" value="75" step="0.01"></div>
<div class="fg"><label>Stop %</label><select id="slfp"><option value="3">3%</option><option value="5" selected>5%</option><option value="7">7%</option></select></div>
<button class="btn-s" onclick="cFix()">Calculate</button><div id="slfr" class="result"></div></div>

<div class="card-inner"><h3>3. Regime-Aware Stops</h3><p class="desc">Adjusts tightness based on market environment.</p>
<table class="mini-tbl"><thead><tr><th>Regime</th><th>Long ATR×</th><th>Short ATR×</th></tr></thead><tbody>
<tr><td class="bull">Strong Up</td><td>2.5-3.0</td><td>1.0-1.5</td></tr>
<tr><td class="bull">Uptrend</td><td>2.0-2.5</td><td>1.5</td></tr>
<tr><td class="bear">Downtrend</td><td>1.5</td><td>2.0-2.5</td></tr>
<tr><td class="bear">Strong Dn</td><td>1.0-1.5</td><td>2.5-3.0</td></tr></tbody></table>
<p class="desc" style="margin-top:8px">Current: <strong class="{rc}">{la.get('regime','')}</strong></p></div></div></div>
</div>

<!-- ===== MARKET REGIME ===== -->
<div id="regime" class="pg">
<div class="card">
    <h2>Current Market Regime {_tip('The regime is determined by where NDX sits relative to its 250-day moving average. This is the most important factor for which strategies are active.')}</h2>
    <div class="regime-badge-wrap">
        <div class="regime-badge {rc}">{la.get('regime','')}</div>
        <div class="regime-metas">
            <span>NDX: <strong>{la.get('ndx_close',0):,.0f}</strong></span>
            <span>vs SMA(250): <strong class="{rc}">{la.get('ext_sma250',0):+.1f}%</strong></span>
            <span>RSI: <strong>{la.get('rsi',50):.0f}</strong></span>
        </div>
    </div>
</div>
<div class="card"><h2>Regime Map</h2>
<p class="desc">A visual timeline of market regimes. Hover for details.</p>
<div class="regime-strip-full" id="regime-map"></div></div>

<div class="card"><h2>Regime Transitions</h2>
<p class="desc">Every time NDX crosses the SMA(250), the market regime changes. These are critical moments.</p>
<div class="tbl-wrap"><table><thead><tr><th>Date</th><th>From</th><th>To</th><th>NDX</th><th>Duration</th><th>What This Means</th></tr></thead>
<tbody>{''.join(_trow(t) for t in reversed(trans[-15:]))}</tbody></table></div></div>

<div class="card"><h2>Performance by Regime</h2>
<div class="grid-4">{_rcards(rstat)}</div></div>

<div class="card"><h2>Regime Playbook</h2>
<div class="grid-2">
<div class="card-inner" style="border-left:3px solid #22c55e"><h3 class="bull">Strong Uptrend</h3><p>NDX is well above its 250-day average. Bull market confirmed. The system runs maximum TQQQ exposure — up to 88%. Buy every dip to SMA(20). Bollinger Band width determines position size.</p><p><strong>Watch for:</strong> Extension &gt;8% above SMA(20) or RSI &gt;75 signals a potential short-term top.</p></div>
<div class="card-inner" style="border-left:3px solid #86efac"><h3 class="bull">Uptrend</h3><p>Above the 250-day average but not extended. Standard bull market behaviour. Mean reversion strategies (buying dips) work best here. Normal position sizes.</p><p><strong>Watch for:</strong> NDX approaching SMA(250) from above — could be the start of a regime flip.</p></div>
<div class="card-inner" style="border-left:3px solid #f97316"><h3 class="bear">Downtrend</h3><p>NDX has broken below its 250-day average. Bear market territory. All long strategies are turned OFF. Momentum short strategies activate — the system switches to SQQQ.</p><p><strong>Critical rule:</strong> Do not buy dips below SMA(250). The system disables long strategies for this reason.</p></div>
<div class="card-inner" style="border-left:3px solid #ef4444"><h3 class="bear">Strong Downtrend</h3><p>Deep bear market. NDX is far below its long-term average. Fear is high. The system scales up SQQQ position based on depth. In 2022, the system limited losses to -10.9% while TQQQ fell -79%.</p><p><strong>Watch for:</strong> RSI &lt;25 is extremely oversold. Often marks bottoms.</p></div>
</div></div>
</div>

<!-- ===== STRESS TEST ===== -->
<div id="stress" class="pg">
<div class="card"><h2>Stress Test Results</h2>
<p class="desc">How would this system have performed during the worst market crashes in history?<br>
<em>Leveraged ETFs can experience extreme losses during bear markets. If TQQQ existed during the Dot-com crash, $100,000 could have fallen to nearly $100. The system's regime detection aims to avoid the worst of these drawdowns by switching to SQQQ.</em></p>
{_stress_table(stress)}
<p class="desc" style="margin-top:12px"><strong>Note:</strong> Stress tests use synthetic 3x daily returns derived from NDX. Actual TQQQ performance would likely be worse due to volatility decay and expense ratios. Run <code>python main.py --stress-test</code> to generate fresh results.</p>
</div></div>

<!-- ===== AI ANALYST ===== -->
<div id="ai" class="pg">
<div class="card"><h2>AI Analyst</h2>
<p class="desc">The AI Analyst lets you ask questions about the system, signals, and performance. It has your latest simulation data pre-loaded.</p>
<div id="ai-s" style="max-width:480px">
<div class="fg"><label>AI Provider</label><select id="aip" onchange="document.getElementById('h1').style.display=this.value==='anthropic'?'block':'none';document.getElementById('h2').style.display=this.value==='openai'?'block':'none'">
<option value="anthropic">Anthropic (Claude Sonnet)</option><option value="openai">OpenAI (GPT-4o)</option></select></div>
<div class="fg"><label>API Key</label><input type="password" id="aik" placeholder="sk-..."></div>
<button class="btn" onclick="initAI()">Connect</button>
<div class="hint" id="h1"><a href="https://console.anthropic.com" target="_blank" rel="noopener">console.anthropic.com</a> → API Keys → Create. Add $5 credit (~$0.01 per question).</div>
<div class="hint" id="h2" style="display:none"><a href="https://platform.openai.com" target="_blank" rel="noopener">platform.openai.com</a> → API Keys → Create. Add $5 credit (~$0.01 per question).</div>
<p class="desc" style="margin-top:6px">&#128274; Your API key stays in your browser and is never stored.</p>
</div>
<div id="ai-b" style="display:none" class="chat-box">
<div class="chat-msgs" id="msgs"></div>
<div class="chat-suggest">
<button onclick="aQ('Why did the system buy today?')">Why this signal?</button>
<button onclick="aQ('Explain the last trade')">Last trade</button>
<button onclick="aQ('What is the current market regime?')">Regime?</button>
<button onclick="aQ('What is the risk exposure right now?')">Risk check</button>
<button onclick="aQ('Which strategy is currently active?')">Active strategy</button>
<button onclick="aQ('Position size for $15K account?')">Position size</button>
</div>
<div class="chat-input"><input id="ain" placeholder="Ask anything about the system..." onkeydown="if(event.key==='Enter')sAI()"><button onclick="sAI()" id="aib">Send</button></div>
</div></div></div>

<!-- ===== LEARN ===== -->
<div id="learn" class="pg">
<div class="card start-here">
<h2>&#128218; Start Here</h2>
<div class="grid-2">
<div>
<h3>What is Apex Trade Lab?</h3>
<p>This is a <strong>paper trading simulation</strong> — a virtual portfolio that trades TQQQ and SQQQ based on 7 algorithmic strategies. No real money is involved. The system makes one decision each day, 10 minutes before market close, and executes at the next day's open.</p>
<h3>What is paper trading?</h3>
<p>Paper trading means simulated trading with virtual money. It lets you test a strategy's performance without risking real capital. Think of it as a flight simulator for trading.</p>
</div>
<div>
<h3>How to read the dashboard</h3>
<p>The <strong>Current Signal card</strong> at the top tells you what the system is doing right now and why. The <strong>equity curve</strong> shows how the portfolio has performed over time compared to simply buying QQQ. The <strong>regime indicator</strong> tells you whether we are in a bull or bear market.</p>
<h3>Daily routine (Darwin time)</h3>
<ol>
<li>Check today's signal (7:00 AM)</li>
<li>Review the market regime</li>
<li>Read the reasoning</li>
<li>Place trade if allocation changed</li>
<li>Return tomorrow</li>
</ol>
</div></div></div>

<div class="card"><h2>Inside the System — 7 Strategies Explained</h2>
<p class="desc">The system runs 7 non-correlated strategies simultaneously. Each has different entry conditions, goals, and risk profiles. They combine to create a smoother equity curve than any single strategy alone.</p>
<div class="strat-grid">
{_strategies_explained()}
</div></div></div>

<!-- ===== COMMUNITY (Subscribe) ===== -->
<div id="community" class="pg">
<div class="card"><h2>&#128236; Subscribe to Weekly Reports</h2>
<p class="desc">Get a weekly email with: P&amp;L summary, trade entries and exits with reasoning, regime analysis, market outlook, and key learnings. Free. Unsubscribe anytime.</p>
<div id="mg1" class="math-gate"><p><strong>Quick verification:</strong></p><div id="mq1" class="mq"></div>
<div class="fg" style="max-width:180px"><label>Answer</label><input type="number" id="ma1"></div>
<button class="btn-s" onclick="cm(1)">Verify</button><div id="me1" class="bear" style="font-size:12px"></div></div>
<div id="sf1" style="display:none">
{('<a href="'+br.get("beehiiv_subscribe_url","")+'" target="_blank" rel="noopener" class="btn" style="display:inline-block;text-decoration:none;margin-top:8px">Open Newsletter Signup &rarr;</a>') if br.get("beehiiv_subscribe_url") else '<p class="desc">Newsletter launching soon.</p>'}
</div></div>
{_stripe_section(br)}
</div>

<!-- ===== VIP ===== -->
<div id="vip" class="pg">
<div class="card"><h2 style="color:#7c3aed">VIP Access</h2>
<p class="desc">VIP Access provides additional commentary and deeper insights for friends, supporters, and collaborators. This may include detailed trade explanations, strategy research notes, experimental strategies, and early feature previews.</p>
<div id="vip-gate"><div class="fg" style="max-width:280px"><label>Password</label><input type="password" id="vip-pw" placeholder="Enter VIP password"></div>
<button class="btn" onclick="checkVIP()" style="background:#7c3aed">Unlock</button><div id="vip-err" class="bear" style="font-size:12px;margin-top:4px"></div></div>
<div id="vip-c" style="display:none">{_vip_content(la, stats, trans, trade_log[-5:])}</div></div></div>

<!-- ===== SERVICES ===== -->
<div id="services" class="pg">
<div class="card"><h2>Services</h2>
<div class="grid-3">
<div class="card-inner" style="border-top:3px solid #22c55e"><h3>Custom Strategy Dashboard</h3><p>Your strategy coded, backtested, and deployed as a live autonomous dashboard — just like this one but for your rules.</p></div>
<div class="card-inner" style="border-top:3px solid #f59e0b"><h3>Backtest Report</h3><p>Send your trading rules and receive a comprehensive backtest including performance metrics, equity curve, regime analysis, and risk assessment.</p></div>
<div class="card-inner" style="border-top:3px solid #7c3aed"><h3>Advertising &amp; Collaboration</h3><p>Feature your product on this dashboard or collaborate on systematic trading research projects.</p></div></div></div>
<div class="card"><h2>Contact</h2>
{('<p class="desc">Email: <a href="mailto:'+br.get("contact_email","")+'">'+br.get("contact_email","")+'</a></p>') if br.get("contact_email") else ''}
<div id="mg2" class="math-gate"><p><strong>Verify you are human:</strong></p><div id="mq2" class="mq"></div>
<div class="fg" style="max-width:180px"><label>Answer</label><input type="number" id="ma2"></div>
<button class="btn-s" onclick="cm(2)">Verify</button><div id="me2" class="bear" style="font-size:12px"></div></div>
<div id="sf2" style="display:none">
{_contact_form(br)}
</div></div>
{_aff_html([a for a in br.get("affiliates",[]) if a.get("url")])}
</div>

<!-- FOOTER -->
<footer>
<p>APEX TRADE LAB — Paper trading simulation only. Not financial advice. Strategy reverse-engineered from @RealTQQQTrader public posts.</p>
<p>Built with Python, Plotly, and GitHub Actions. 100% free and open source.</p>
</footer>

<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script>
function go(id,b){{document.querySelectorAll('.pg').forEach(p=>p.classList.remove('on'));document.querySelectorAll('nav>button,nav .dropdown>button').forEach(x=>x.classList.remove('on'));document.getElementById(id).classList.add('on');if(b)b.classList.add('on');window.scrollTo(0,0)}}

// Math puzzles
let mv=[0,0,0,0];
function gm(q,i){{const a=5+Math.floor(Math.random()*20),b=3+Math.floor(Math.random()*15);document.getElementById(q).innerHTML='<span style="font-size:18px;font-weight:600;color:#4338ca">'+a+' + '+b+' = ?</span>';mv[i*2]=a;mv[i*2+1]=b}}
window.addEventListener('load',()=>{{gm('mq1',0);gm('mq2',1)}});
function cm(n){{const a=+document.getElementById('ma'+n).value;if(a===mv[(n-1)*2]+mv[(n-1)*2+1]){{document.getElementById('mg'+n).style.display='none';document.getElementById('sf'+n).style.display='block'}}else{{document.getElementById('me'+n).textContent='Incorrect. Try again.';gm('mq'+n,n-1)}}}}

// VIP
const VH='{br.get("vip_password_hash","")}';
async function checkVIP(){{const pw=document.getElementById('vip-pw').value;if(!VH){{document.getElementById('vip-err').textContent='VIP not configured.';return}}const h=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(pw)))).map(b=>b.toString(16).padStart(2,'0')).join('');if(h===VH){{document.getElementById('vip-gate').style.display='none';document.getElementById('vip-c').style.display='block'}}else{{document.getElementById('vip-err').textContent='Incorrect.'}}}}

// Regime strip
const RM={regime_map_data};
function buildRegimeStrip(id,full){{const el=document.getElementById(id);if(!RM.length)return;let html='';const w=full?'100%':'100%';RM.forEach((r,i)=>{{const c=r.r==='STRONG UPTREND'?'#22c55e':r.r==='UPTREND'?'#86efac':r.r==='DOWNTREND'?'#f97316':r.r==='STRONG DOWNTREND'?'#ef4444':'#d1d5db';html+=`<div title="${{r.d}}\\n${{r.r}}\\nRSI: ${{r.rsi?.toFixed?.(0)||'?'}}\\nvs SMA250: ${{r.e250?.toFixed?.(1)||'?'}}%" style="flex:1;height:${{full?'28px':'12px'}};background:${{c}}"></div>`}});el.innerHTML=html}}
window.addEventListener('load',()=>{{buildRegimeStrip('regime-strip',false);buildRegimeStrip('regime-map',true)}});

// Charts
const _D={json.dumps(D)},_EQ={json.dumps(EQ)},_BN={json.dumps(BN)};
const _TA={json.dumps(TA)},_SA={json.dumps(SA)},_CA={json.dumps(CA)};
const _NX={json.dumps(NX)},_S20={json.dumps(S20)},_S250={json.dumps(S250)};
const _BD={json.dumps(bd)},_BP={json.dumps(bp)},_BL={json.dumps(bl)};
const _SD={json.dumps(sd)},_SP={json.dumps(sp)},_SL={json.dumps(sl)};
const L={{paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{{color:'#374151',family:'Inter,sans-serif',size:12}},margin:{{t:8,r:20,b:35,l:55}},xaxis:{{gridcolor:'#f3f4f6'}},yaxis:{{gridcolor:'#f3f4f6'}},legend:{{bgcolor:'rgba(255,255,255,0.9)',x:0,y:1}},hovermode:'x unified'}};
window.addEventListener('load',()=>{{
Plotly.newPlot('eq-c',[{{x:_D,y:_EQ,name:'APEX',line:{{color:'#22c55e',width:2}}}},{{x:_D,y:_BN,name:'QQQ',line:{{color:'#f59e0b',width:1,dash:'dot'}}}}],{{...L,yaxis:{{...L.yaxis,title:'$'}},height:360}},{{responsive:true}});
const rs={_rshapes_light(D,RG)};
Plotly.newPlot('nx-c',[{{x:_D,y:_NX,name:'NDX',line:{{color:'#374151',width:1.5}}}},{{x:_D,y:_S20,name:'SMA(20)',line:{{color:'#f59e0b',width:1,dash:'dash'}}}},{{x:_D,y:_S250,name:'SMA(250)',line:{{color:'#ef4444',width:1.5,dash:'dash'}}}},{{x:_BD,y:_BP,name:'Buy',mode:'markers',text:_BL,marker:{{color:'#22c55e',size:8,symbol:'triangle-up'}},hoverinfo:'text'}},{{x:_SD,y:_SP,name:'Sell',mode:'markers',text:_SL,marker:{{color:'#ef4444',size:8,symbol:'triangle-down'}},hoverinfo:'text'}}],{{...L,yaxis:{{...L.yaxis,title:'NDX'}},shapes:rs,height:400}},{{responsive:true}});
Plotly.newPlot('al-c',[{{x:_D,y:_TA,name:'TQQQ%',fill:'tozeroy',fillcolor:'rgba(34,197,94,.2)',line:{{color:'#22c55e'}},stackgroup:'a'}},{{x:_D,y:_SA,name:'SQQQ%',fill:'tonexty',fillcolor:'rgba(239,68,68,.2)',line:{{color:'#ef4444'}},stackgroup:'a'}},{{x:_D,y:_CA,name:'Cash%',fill:'tonexty',fillcolor:'rgba(209,213,219,.15)',line:{{color:'#9ca3af'}},stackgroup:'a'}}],{{...L,yaxis:{{...L.yaxis,title:'%',range:[0,105]}},height:260}},{{responsive:true}});
}});

// Calculators
function cPos(){{const a=+document.getElementById('psa').value,r=+document.getElementById('psr').value/100,e=+document.getElementById('pse').value,s=+document.getElementById('pss').value,i=document.getElementById('psi').value;if(!a||!e||!s||s>=e){{document.getElementById('pso').innerHTML='<span class="bear">Entry must be above stop.</span>';return}};const rd=a*r,rps=Math.abs(e-s),sh=Math.floor(rd/rps),pv=sh*e,pp=pv/a*100;document.getElementById('pso').innerHTML='<div class="rr"><span>Risk Amount</span><span class="bear">$'+rd.toFixed(0)+'</span></div><div class="rr"><span>Shares</span><span class="bull">'+sh+' '+i+'</span></div><div class="rr"><span>Position Value</span><span>$'+pv.toFixed(0)+' ('+pp.toFixed(0)+'%)</span></div><div class="rr"><span>Max Loss</span><span class="bear">$'+(sh*rps).toFixed(0)+'</span></div><hr><div class="rr"><span>Target 1.5R</span><span class="bull">$'+(e+rps*1.5).toFixed(2)+'</span></div><div class="rr"><span>Target 2R</span><span class="bull">$'+(e+rps*2).toFixed(2)+'</span></div><div class="note">Sell 50% at Target 1, move stop to breakeven. Trail the rest.</div>'}}
function cATR(){{const a=+document.getElementById('sla').value,m=+document.getElementById('slam').value,e=+document.getElementById('pse')?.value||75,s=e-(a*m);document.getElementById('slar').textContent='Stop: $'+s.toFixed(2)+' ('+((e-s)/e*100).toFixed(1)+'% risk)'}}
function cFix(){{const e=+document.getElementById('slfe').value,p=+document.getElementById('slfp').value/100,s=e*(1-p);document.getElementById('slfr').textContent='Stop: $'+s.toFixed(2)+' ($'+(e-s).toFixed(2)+' per share)'}}

// AI
const CD={cd};
const SYS='You are APEX TRADE LAB AI Analyst. Analyze paper trading data from a 7-strategy TQQQ/SQQQ system. SMA20,SMA250,BB,RSI. Regime=NDX vs SMA250. Be educational and concise. This is PAPER TRADING only.\\nDATA:\\n'+JSON.stringify(CD);
let ak='',ah=[],ap='anthropic';
function initAI(){{ap=document.getElementById('aip').value;ak=document.getElementById('aik').value.trim();if(!ak||ak.length<10){{alert('Enter valid key');return}};document.getElementById('ai-s').style.display='none';document.getElementById('ai-b').style.display='flex';aM('a','Connected via '+(ap==='anthropic'?'Claude':'GPT-4o')+'. Your data is loaded. Ask me anything.')}}
function aM(r,t){{const d=document.getElementById('msgs'),m=document.createElement('div');m.className='chat-msg chat-'+(r==='u'?'u':'a');m.textContent=t;d.appendChild(m);d.scrollTop=d.scrollHeight}}
function aQ(q){{document.getElementById('ain').value=q;sAI()}}
async function sAI(){{const q=document.getElementById('ain').value.trim();if(!q)return;document.getElementById('ain').value='';aM('u',q);ah.push({{role:'user',content:q}});document.getElementById('aib').disabled=true;
try{{let r='';if(ap==='anthropic'){{const f=await fetch('https://api.anthropic.com/v1/messages',{{method:'POST',headers:{{'Content-Type':'application/json','x-api-key':ak,'anthropic-version':'2023-06-01','anthropic-dangerous-direct-browser-access':'true'}},body:JSON.stringify({{model:'claude-sonnet-4-20250514',max_tokens:1000,system:SYS,messages:ah.slice(-8)}})}});const d=await f.json();r=d.content?.map(c=>c.text||'').join('\\n')||d.error?.message||'Error'}}else{{const f=await fetch('https://api.openai.com/v1/chat/completions',{{method:'POST',headers:{{'Content-Type':'application/json','Authorization':'Bearer '+ak}},body:JSON.stringify({{model:'gpt-4o',max_tokens:1000,messages:[{{role:'system',content:SYS}},...ah.slice(-8)]}})}}); const d=await f.json();r=d.choices?.[0]?.message?.content||d.error?.message||'Error'}}
aM('a',r);ah.push({{role:'assistant',content:r}})}}catch(e){{aM('a','Error: '+e.message)}}document.getElementById('aib').disabled=false}}

// Tooltips
document.querySelectorAll('.tip').forEach(el=>{{el.addEventListener('mouseenter',e=>{{const t=el.getAttribute('data-tip');const d=document.createElement('div');d.className='tip-box';d.textContent=t;d.style.left=e.pageX+'px';d.style.top=(e.pageY-40)+'px';document.body.appendChild(d);el._tip=d}});el.addEventListener('mouseleave',()=>{{if(el._tip)el._tip.remove()}});}});
</script></body></html>'''


# =====================================================================
# HELPERS
# =====================================================================

def _tip(text):
    return f'<span class="tip" data-tip="{text}">&#9432;</span>'

def _action_text(la):
    t,s = la.get('tqqq_alloc',0), la.get('sqqq_alloc',0)
    if t > 50: return f"Buying TQQQ ({t:.0f}%)"
    elif t > 0: return f"Light long TQQQ ({t:.0f}%)"
    elif s > 50: return f"Shorting via SQQQ ({s:.0f}%)"
    elif s > 0: return f"Light short via SQQQ ({s:.0f}%)"
    return "Holding cash"

def _human_reason(la):
    details = la.get("strategy_details","")
    if not details: return "No active strategies. The system is in cash, waiting for the next opportunity."
    # Make it more readable
    return details.replace(";",". ").replace("MR Long","Mean Reversion Long").replace("Mom Short","Momentum Short")

def _human_trade(t):
    tt = t.get("trade_type","")
    strat = t.get("strategy","")
    reason = t.get("reasoning","")[:80]
    if tt == "NEW ENTRY": return f"New position opened. {strat} detected an opportunity."
    elif tt == "EXIT": return f"Position closed. {strat} signaled exit."
    elif tt == "ADD": return f"Added to position. {strat} sees continued strength."
    elif tt == "REDUCE": return f"Reduced position. Taking partial profits."
    return f"{tt}: {strat}"

def _next_review_time():
    """Next US market close in ACST."""
    from datetime import datetime
    now = datetime.utcnow()
    # Next weekday 21:30 UTC
    import calendar
    d = now.replace(hour=21, minute=30, second=0, microsecond=0)
    if now.hour >= 21:
        d = d + pd.Timedelta(days=1)
    while d.weekday() >= 5:
        d = d + pd.Timedelta(days=1)
    return f"{d.strftime('%A %d %b')} ~7:00 AM Darwin / 4:30 PM ET"

def _calc_pnl(eh, tl):
    total = sum(t.get("realized_pnl",0) for t in tl)
    return {"total_pnl": total}

def _trade_row_human(t):
    tt=t.get("trade_type","")
    tc={"NEW ENTRY":"te","EXIT":"tx","ADD":"ta","REDUCE":"tr"}.get(tt,"")
    pnl=t.get("realized_pnl",0)
    ps=f"${pnl:+,.0f}" if pnl else "—"
    pc="bull" if pnl>0 else "bear" if pnl<0 else ""
    desc = _human_trade(t)
    return f'<tr><td>{t["date"]}</td><td class="{tc}">{tt}</td><td>{t["ticker"]}</td><td class="{"bull" if t["action"]=="BUY" else "bear"}">{t["action"]}</td><td>{t["shares"]:.1f}</td><td>${t["price"]:,.2f}</td><td>${t["value"]:,.0f}</td><td class="{pc}">{ps}</td><td style="font-size:11px">{t.get("strategy","")}</td><td style="font-size:11px;color:#6b7280">{desc}</td><td>{t.get("regime","")}</td></tr>'

def _strategies_explained():
    strats = [
        ("Momentum Long","TQQQ","Uptrend (above SMA250)","NDX breaks above the upper Bollinger Band while above SMA(20).",
         "Capture strong upward momentum. Ride the trend.","Stops out if NDX closes below SMA(20).",
         "In a strong bull market, NDX pushes above the upper BB. The system goes heavily long TQQQ to maximise gains during the momentum phase."),
        ("Mean Reversion Long 1","TQQQ","Uptrend","NDX pulls back to within 1% of SMA(20) from above.",
         "Buy the dip during uptrends. Pullbacks to SMA(20) are buying opportunities.",
         "Exits if NDX extends more than 3% above SMA(20).","After a 2-3% pullback in a bull market, the system buys the dip, expecting NDX to bounce back to its trend."),
        ("Mean Reversion Long 2","TQQQ","Uptrend","NDX drops below the lower Bollinger Band while still above SMA(250).",
         "Buy deep pullbacks aggressively. The deeper the dip, the larger the position.","Exits when NDX recovers above the middle BB.",
         "A sharp 5%+ pullback in an uptrend. The system sees this as a sale, buying more aggressively."),
        ("Mean Reversion Long 3","TQQQ","Near SMA(250)","NDX is within 3% of SMA(250) and shows a bullish reversal candle.",
         "Catch bounces near the critical SMA(250) support level.","Exits if NDX extends more than 5% above SMA(20).",
         "NDX tests its 250-day average—a key level. A bullish candle here triggers a speculative long."),
        ("Mean Reversion Short","SQQQ","Uptrend (overextended)","NDX is more than 4% above SMA(20) AND above the upper BB.",
         "Short-term contrarian trade. Fade extreme overextension.","Exits when NDX reverts back to SMA(20).",
         "After a massive rally, NDX is stretched too far above its average. The system takes a small short position expecting a pullback."),
        ("Momentum Short 1","SQQQ","Downtrend (below SMA250)","NDX closes below SMA(250) and below the lower BB.",
         "Ride the downtrend. Position size scales with depth below SMA(250).","Exits when NDX reclaims SMA(250).",
         "NDX breaks below its 250-day average—a major bearish signal. The system switches to SQQQ."),
        ("Momentum Short 2","SQQQ","Downtrend","NDX bounced to SMA(20) but failed and closed back below it.",
         "Short failed bounces in a bear market. These are bull traps.","Exits if NDX stays above SMA(20) for 3 consecutive days.",
         "In a downtrend, a rally to SMA(20) that fails is a classic short entry. The system catches these bear market rallies."),
    ]
    html = ""
    for name,inst,regime,entry,goal,risk,example in strats:
        emoji = "🟢" if inst=="TQQQ" else "🔴"
        html += f'''<div class="strat-card"><div class="strat-head"><span>{emoji} {name}</span><span class="strat-inst">{inst}</span></div>
        <div class="strat-row"><strong>When:</strong> {regime}</div>
        <div class="strat-row"><strong>Entry:</strong> {entry}</div>
        <div class="strat-row"><strong>Goal:</strong> {goal}</div>
        <div class="strat-row"><strong>Risk:</strong> {risk}</div>
        <div class="strat-row"><strong>Example:</strong> <em>{example}</em></div></div>'''
    return html

def _stress_table(results):
    if not results:
        return '<p class="desc">No stress test data yet. Run <code>python main.py --stress-test</code> to generate.</p>'
    rows = ""
    for r in results:
        sys_c = "bull" if r.get("system_estimated_pct",0)>0 else "bear"
        rows += f'<tr><td><strong>{r["name"]}</strong></td><td>{r["start"]} to {r["end"]}</td><td class="bear">{r.get("ndx_return_pct",0):+.1f}%</td><td class="bear">{r.get("tqqq_estimated_pct",0):+.1f}%</td><td class="{sys_c}">{r.get("system_estimated_pct",0):+.1f}%</td><td class="bear">{r.get("max_drawdown_pct",0):.1f}%</td><td>{r.get("recovery_days","?")}d</td></tr>'
    return f'<div class="tbl-wrap"><table><thead><tr><th>Scenario</th><th>Period</th><th>NDX</th><th>TQQQ (est.)</th><th>System (est.)</th><th>Max DD</th><th>Recovery</th></tr></thead><tbody>{rows}</tbody></table></div>'

def _social_posts_section(posts):
    if not posts: return ""
    html = '<div class="card"><h2>Social Posts (Ready to Copy)</h2><p class="desc">Copy-paste these to your social media. Review before posting.</p>'
    for p in posts:
        html += f'<div class="card-inner" style="margin-bottom:8px"><h3>{p.get("type","").title()} — {p.get("date","")}</h3>'
        html += f'<div style="margin-top:6px"><strong>Twitter/X:</strong><pre style="background:#f9fafb;padding:8px;border-radius:4px;font-size:11px;white-space:pre-wrap;border:1px solid #e5e7eb">{p.get("twitter","")}</pre></div>'
        html += f'<div style="margin-top:4px"><strong>Facebook:</strong><pre style="background:#f9fafb;padding:8px;border-radius:4px;font-size:11px;white-space:pre-wrap;border:1px solid #e5e7eb">{p.get("facebook","")}</pre></div></div>'
    return html + '</div>'

def _vip_content(la, stats, trans, recent):
    r = la.get("regime",""); ret = stats.get("total_return_pct",0); dd = stats.get("max_drawdown_pct",0)
    lt = trans[-1] if trans else {}; lt2 = recent[-1] if recent else {}
    return f'''<div class="card-inner" style="border-left:3px solid #7c3aed">
    <h3 style="color:#7c3aed">Analyst Notes — {la.get('date','')}</h3>
    <p><strong>Regime:</strong> {r}. NDX {la.get('ext_sma250',0):+.1f}% from SMA(250), {la.get('ext_sma20',0):+.1f}% from SMA(20). RSI {la.get('rsi',50):.0f}.</p>
    <p><strong>Performance:</strong> {ret:+.1f}% total, {dd:.1f}% max drawdown.</p>
    <p><strong>Last regime shift:</strong> {lt.get('from','?')} → {lt.get('to','?')} on {lt.get('date','')}. {lt.get('m','')}</p>
    <p><strong>Last trade:</strong> {lt2.get('action','')} {lt2.get('ticker','')} on {lt2.get('date','')} — {lt2.get('strategy','')}</p>
    <p><strong>Allocation:</strong> TQQQ {la.get('tqqq_alloc',0):.0f}% / SQQQ {la.get('sqqq_alloc',0):.0f}% / Cash {la.get('cash_alloc',100):.0f}%</p></div>'''

def _stripe_section(br):
    url = br.get("stripe_payment_url","")
    if not url: return ""
    return f'<div class="card"><h2>Support This Project</h2><p class="desc">If the research is useful, consider a small contribution. 100% goes toward keeping the platform running.</p><div style="text-align:center;padding:12px"><a href="{url}" target="_blank" rel="noopener" class="btn" style="display:inline-block;text-decoration:none">&#9889; Support ($5) via Stripe</a></div></div>'

def _contact_form(br):
    fs = br.get("formspree_endpoint","")
    if not fs: return f'<p class="desc">Contact form coming soon.{" Email: "+br.get("contact_email","") if br.get("contact_email") else ""}</p>'
    return f'''<form action="{fs}" method="POST" style="max-width:500px">
    <div class="fg"><label>I am a...</label><select name="user_type"><option>Individual Investor</option><option>Institutional Investor</option><option>Trading Beginner</option><option>Quant / Developer</option><option>Content Creator</option></select></div>
    <div class="fg"><label>What interests you most?</label><select name="interest"><option>Daily Signals</option><option>Strategy Research</option><option>Learning Systematic Trading</option><option>Backtesting Tools</option><option>Collaboration Opportunities</option></select></div>
    <div class="fg"><label>Inquiry Type</label><select name="service"><option>Custom Strategy Dashboard</option><option>Backtest Report</option><option>Advertising &amp; Collaboration</option><option>General Question</option></select></div>
    <div class="fg"><label>Name</label><input type="text" name="name" required></div>
    <div class="fg"><label>Email</label><input type="email" name="email" required></div>
    <div class="fg"><label>Message</label><textarea name="message" rows="3" style="width:100%;padding:6px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;resize:vertical"></textarea></div>
    <input type="text" name="_gotcha" style="display:none">
    <button type="submit" class="btn">Send Message</button></form>'''

def _aff_html(affs):
    if not affs: return ''
    cards=''.join(f'<div class="card-inner"><h3>{a["name"]}</h3><p class="desc">{a.get("tagline","")}</p><a href="{a["url"]}" target="_blank" rel="noopener noreferrer" class="btn-s" style="display:inline-block;text-decoration:none">Open Account &rarr;</a></div>' for a in affs)
    return f'<div class="card"><h2>Recommended Brokers</h2><p class="desc" style="font-size:11px">Affiliate links — we may earn a commission at no extra cost to you.</p><div class="grid-3">{cards}</div></div>'

def _nb(bd,D,cap):
    if bd is None or bd.empty: return [None]*len(D)
    bs=bd["Close"].iloc[0]
    return [round(bd.loc[bd.index<=pd.Timestamp(d)].iloc[-1]["Close"]/bs*cap,2) if not bd.loc[bd.index<=pd.Timestamp(d)].empty else None for d in D]

def _rshapes_light(D,RG):
    if not D: return "[]"
    sh,i=[],0
    while i<len(D):
        rg,s=RG[i],D[i]
        while i<len(D) and RG[i]==rg: i+=1
        c={"STRONG UPTREND":"rgba(34,197,94,.08)","UPTREND":"rgba(134,239,172,.06)","DOWNTREND":"rgba(249,115,22,.06)","STRONG DOWNTREND":"rgba(239,68,68,.08)"}.get(rg,"rgba(209,213,219,.04)")
        sh.append(f'{{"type":"rect","xref":"x","yref":"paper","x0":"{s}","x1":"{D[i-1]}","y0":0,"y1":1,"fillcolor":"{c}","line":{{"width":0}}}}')
    return "["+",".join(sh)+"]"

def _rtrans(eh):
    tr,prev,pd_=[],None,None
    for r in eh:
        rg=r.get("regime","")
        if rg!=prev and prev:
            dur=0
            if pd_:
                try: dur=(pd.Timestamp(r["date"])-pd.Timestamp(pd_)).days
                except: pass
            m={"STRONG UPTREND,UPTREND":"Momentum is fading. Still bullish but reducing size.","UPTREND,STRONG UPTREND":"Acceleration! Scaling up TQQQ position.","UPTREND,DOWNTREND":"Critical shift. NDX broke below SMA(250). Switching from TQQQ to SQQQ.","DOWNTREND,UPTREND":"Recovery signal. NDX reclaimed SMA(250). Switching from SQQQ to TQQQ.","DOWNTREND,STRONG DOWNTREND":"Sell-off deepening. Increasing SQQQ exposure.","STRONG DOWNTREND,DOWNTREND":"Pressure easing. Beginning to reduce short positions.","STRONG UPTREND,DOWNTREND":"Sharp reversal. Closing long positions immediately.","STRONG DOWNTREND,UPTREND":"V-shaped recovery. Aggressive long entry opportunity."}.get(f"{prev},{rg}",f"Regime shifted from {prev} to {rg}.")
            tr.append({"date":r["date"],"from":prev,"to":rg,"ndx":r.get("ndx_close",0),"dur":dur,"m":m})
        if rg!=prev: pd_=r["date"]
        prev=rg
    return tr

def _trow(t):
    return f'<tr><td>{t["date"]}</td><td class="{"bull" if "UP" in t["from"] else "bear"}">{t["from"]}</td><td class="{"bull" if "UP" in t["to"] else "bear"}">{t["to"]}</td><td>{t["ndx"]:,.0f}</td><td>{t["dur"]} days</td><td style="font-size:12px;color:#6b7280">{t["m"]}</td></tr>'

def _rcards(rs):
    if not rs: return '<p class="desc">Not enough data yet.</p>'
    cards=[]
    for r in ["STRONG UPTREND","UPTREND","DOWNTREND","STRONG DOWNTREND"]:
        if r not in rs: continue
        s=rs[r]; bc={"STRONG UPTREND":"#22c55e","UPTREND":"#86efac","DOWNTREND":"#f97316","STRONG DOWNTREND":"#ef4444"}[r]
        rc="bull" if s["total_return_pct"]>0 else "bear"
        cards.append(f'<div class="card-inner" style="border-top:3px solid {bc}"><h3>{r}</h3><div class="mini-stats"><div><span class="desc">Time</span><br><strong>{s["pct_of_time"]}%</strong></div><div><span class="desc">Days</span><br><strong>{s["days"]}</strong></div><div><span class="desc">Return</span><br><strong class="{rc}">{s["total_return_pct"]:+.1f}%</strong></div><div><span class="desc">Trades</span><br><strong>{s["trades"]}</strong></div></div></div>')
    return "".join(cards)


# =====================================================================
# CSS
# =====================================================================

def _css(br):
    return f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>APEX TRADE LAB — Systematic Trading Research</title>
<meta name="description" content="Free autonomous paper trading dashboard. 7-strategy TQQQ/SQQQ system with AI analyst, regime analysis, stress testing.">
<meta property="og:title" content="APEX TRADE LAB"><meta property="og:description" content="Systematic trading research platform. Live paper trading, regime analysis, AI chat.">
<meta name="theme-color" content="#22c55e">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#9889;</text></svg>">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Code+Pro:wght@400;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#f8fafc;color:#1e293b;line-height:1.6;font-size:14px}}
::selection{{background:#22c55e;color:#fff}}

header{{text-align:center;padding:24px 20px 12px;background:#fff;border-bottom:1px solid #e2e8f0}}
.logo{{font-family:'Source Code Pro',monospace;font-size:24px;font-weight:700;color:#1e293b;letter-spacing:1px}}
.tagline{{color:#64748b;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin-top:2px}}
.live-badge{{font-size:11px;color:#64748b;margin-top:4px}}
.dot{{display:inline-block;width:7px;height:7px;background:#22c55e;border-radius:50%;margin-right:3px;animation:p 2s infinite}}
@keyframes p{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}

nav{{display:flex;gap:2px;justify-content:center;padding:8px 12px;background:#fff;border-bottom:1px solid #e2e8f0;flex-wrap:wrap;position:sticky;top:0;z-index:100}}
nav button{{background:none;border:none;color:#64748b;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:500;transition:.15s}}
nav button:hover{{color:#1e293b;background:#f1f5f9}}
nav button.on{{color:#22c55e;background:#f0fdf4;font-weight:600}}
.dropdown{{position:relative;display:inline-block}}
.dropdown-menu{{display:none;position:absolute;top:100%;left:0;background:#fff;border:1px solid #e2e8f0;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.08);min-width:160px;z-index:200;padding:4px}}
.dropdown.open .dropdown-menu{{display:block}}
.dropdown-menu a{{display:block;padding:8px 14px;color:#374151;font-size:13px;cursor:pointer;border-radius:4px}}
.dropdown-menu a:hover{{background:#f0fdf4;color:#22c55e}}

.pg{{display:none;padding:16px;max-width:1200px;margin:0 auto}}.pg.on{{display:block}}

.card{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.card h2{{font-size:16px;font-weight:600;color:#1e293b;margin-bottom:10px}}
.card h3{{font-size:14px;font-weight:600;margin-bottom:6px}}
.card-inner{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px}}
.desc{{color:#64748b;font-size:13px;margin-bottom:8px}}

.bull{{color:#16a34a}}.bear{{color:#dc2626}}.te{{color:#16a34a;font-weight:600}}.tx{{color:#dc2626;font-weight:600}}.ta{{color:#2563eb}}.tr{{color:#d97706}}

/* Signal Card */
.signal-card{{background:#fff;border:2px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.signal-card.bull{{border-color:#22c55e}}.signal-card.bear{{border-color:#ef4444}}
.signal-header{{font-family:'Source Code Pro',monospace;font-size:12px;letter-spacing:2px;color:#64748b;text-transform:uppercase;margin-bottom:14px}}
.signal-grid{{display:grid;grid-template-columns:1fr 1fr 2fr 2fr;gap:16px;align-items:start}}
.signal-label{{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}}
.signal-value{{font-family:'Source Code Pro',monospace;font-size:18px;font-weight:700}}.signal-value.bull{{color:#16a34a}}.signal-value.bear{{color:#dc2626}}
.alloc-bars{{display:flex;flex-direction:column;gap:6px}}.alloc-item{{display:flex;align-items:center;gap:8px}}.alloc-label{{width:40px;font-size:11px;color:#64748b}}.alloc-bar{{flex:1;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden}}.alloc-fill{{height:100%;border-radius:4px}}.alloc-fill.bull{{background:#22c55e}}.alloc-fill.bear{{background:#ef4444}}.alloc-fill.cash{{background:#94a3b8}}.alloc-pct{{width:36px;font-size:12px;font-weight:600;text-align:right}}
.signal-reason{{margin-top:14px;padding:10px;background:#f8fafc;border-radius:6px;font-size:13px;color:#475569;border-left:3px solid #22c55e}}
.signal-card.bear .signal-reason{{border-left-color:#ef4444}}
.signal-next{{margin-top:8px;font-size:12px;color:#94a3b8}}

/* Stats */
.stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:16px}}
.stat{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center}}.stat-l{{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.3px}}.stat-v{{font-family:'Source Code Pro',monospace;font-size:20px;font-weight:700;margin-top:2px}}

/* Regime */
.regime-strip,.regime-strip-full{{display:flex;border-radius:4px;overflow:hidden;margin-top:8px}}
.regime-badge-wrap{{display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
.regime-badge{{font-family:'Source Code Pro',monospace;font-size:18px;font-weight:700;padding:10px 24px;border-radius:8px;border:2px solid}}.regime-badge.bull{{color:#16a34a;border-color:#22c55e;background:#f0fdf4}}.regime-badge.bear{{color:#dc2626;border-color:#ef4444;background:#fef2f2}}
.regime-metas{{display:flex;gap:16px;font-size:13px;color:#64748b}}

/* Grids */
.grid-2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}
.grid-3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}
.grid-4{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}}
.mini-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:8px;text-align:center;font-size:13px}}

/* Tables */
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#f8fafc;color:#64748b;padding:8px 6px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.3px;font-weight:600;border-bottom:2px solid #e2e8f0}}
td{{padding:6px;border-bottom:1px solid #f1f5f9}}tr:hover td{{background:#f8fafc}}
.tbl-wrap{{overflow-x:auto}}.mini-tbl{{font-size:12px}}.mini-tbl th{{font-size:9px}}

/* Calculators */
.calc-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.calc-in{{display:flex;flex-direction:column;gap:6px}}.calc-out{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px}}
.fg{{margin-bottom:6px}}.fg label{{display:block;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.3px;margin-bottom:2px}}.fg input,.fg select{{width:100%;padding:8px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;font-family:'Source Code Pro',monospace;background:#fff}}
.btn{{background:#22c55e;color:#fff;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;font-weight:600;font-size:13px}}.btn:hover{{background:#16a34a}}
.btn-s{{background:#f59e0b;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-weight:600;font-size:11px}}.btn-s:hover{{background:#d97706}}
.rr{{display:flex;justify-content:space-between;margin:3px 0;font-size:13px}}.rr span:first-child{{color:#64748b}}
.rr span:last-child{{font-family:'Source Code Pro',monospace;font-weight:600}}.note{{color:#d97706;font-size:11px;margin-top:6px}}
.formula{{background:#f0fdf4;padding:6px 10px;border-radius:4px;font-family:'Source Code Pro',monospace;font-size:12px;margin:6px 0;color:#16a34a;border:1px solid #dcfce7}}
.result{{margin-top:6px;font-family:'Source Code Pro',monospace;font-size:13px;color:#1e293b}}.placeholder{{color:#94a3b8;text-align:center;padding:20px}}
.hint{{font-size:12px;color:#64748b;margin-top:6px}}.hint a{{color:#2563eb}}

/* Strategy cards */
.strat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
.strat-card{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px}}
.strat-head{{display:flex;justify-content:space-between;font-weight:600;margin-bottom:8px;font-size:14px}}
.strat-inst{{font-size:12px;padding:2px 8px;border-radius:4px;background:#f0fdf4;color:#16a34a}}
.strat-row{{font-size:12px;margin:4px 0;color:#475569}}.strat-row strong{{color:#1e293b}}

/* Chat */
.chat-box{{display:flex;flex-direction:column;height:460px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden}}
.chat-msgs{{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:6px}}
.chat-msg{{padding:8px 12px;border-radius:8px;font-size:12px;max-width:85%;white-space:pre-wrap;line-height:1.5}}
.chat-u{{background:#f0fdf4;align-self:flex-end;border:1px solid #dcfce7}}
.chat-a{{background:#fff;align-self:flex-start;border:1px solid #e2e8f0}}
.chat-suggest{{display:flex;flex-wrap:wrap;gap:4px;padding:6px;border-top:1px solid #e2e8f0}}
.chat-suggest button{{background:#fff;border:1px solid #d1d5db;color:#374151;padding:4px 10px;border-radius:14px;cursor:pointer;font-size:10px}}.chat-suggest button:hover{{border-color:#22c55e;color:#16a34a}}
.chat-input{{display:flex;gap:4px;padding:6px;border-top:1px solid #e2e8f0}}
.chat-input input{{flex:1;padding:8px 12px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;outline:none}}
.chat-input button{{background:#22c55e;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:600}}

/* Subscribe */
.sub-cols{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.sub-box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px}}
.math-gate{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px;max-width:340px}}.mq{{margin:6px 0}}

/* Tooltips */
.tip{{color:#94a3b8;cursor:help;font-size:14px;margin-left:4px}}
.tip-box{{position:absolute;background:#1e293b;color:#fff;padding:6px 10px;border-radius:6px;font-size:11px;max-width:240px;z-index:300;pointer-events:none;box-shadow:0 2px 8px rgba(0,0,0,.15)}}

/* Start Here */
.start-here{{border:2px solid #22c55e;background:#f0fdf4}}
.start-here h2{{color:#16a34a}}.start-here ol{{margin:8px 0 8px 20px;color:#475569}}.start-here ol li{{margin:4px 0}}

footer{{text-align:center;padding:20px;color:#94a3b8;font-size:11px;border-top:1px solid #e2e8f0;margin-top:20px}}
footer p{{margin:3px 0}}

@media(max-width:768px){{
.signal-grid{{grid-template-columns:1fr 1fr}}.stats-row{{grid-template-columns:repeat(2,1fr)}}
.calc-grid,.grid-2,.grid-3,.grid-4,.sub-cols,.strat-grid{{grid-template-columns:1fr}}
nav{{gap:1px}}nav button{{padding:6px 8px;font-size:11px}}
}}
</style></head>'''


# =====================================================================
# OUTPUT
# =====================================================================

def save_dashboard(html, config):
    d=Path(config["outputs"]["html_dir"]); d.mkdir(parents=True,exist_ok=True)
    p=d/config["outputs"]["dashboard_html"]
    with open(p,"w") as f: f.write(html)
    logger.info(f"Dashboard: {p}"); return p

def save_csvs(portfolio, config):
    d=Path(config["outputs"]["csv_dir"]); d.mkdir(parents=True,exist_ok=True)
    if portfolio.equity_history: pd.DataFrame(portfolio.equity_history).to_csv(d/config["outputs"]["equity_csv"],index=False)
    if portfolio.trade_log: pd.DataFrame(portfolio.trade_log).to_csv(d/config["outputs"]["trades_csv"],index=False)
    if portfolio.signal_log: pd.DataFrame(portfolio.signal_log).to_csv(d/config["outputs"]["signals_csv"],index=False)
