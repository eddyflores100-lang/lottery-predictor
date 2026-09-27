"""
LotteryPredictor MCP Server — exposes our 10-engine predictor as an MCP server
that other AI agents (Claude Desktop, Cursor, etc.) can consume.

This makes US a producer in the MCP ecosystem, not just a consumer.

Protocol: MCP 2025-06-18 (Streamable HTTP)
Endpoint: http://localhost:8787/mcp

Tools exposed:
1. list_lotteries — List all 47 available lotteries (38 quicklotto + 9 deep history)
2. describe_lottery — Get details of a specific lottery (format, draws, last result)
3. list_engines — List all 10 prediction engines
4. predict — Generate a prediction for a lottery using a specific engine
5. predict_with_explanation — Same as predict but with detailed justification per number
6. backtest — Get backtest results for a lottery (cached)
7. get_latest_results — Get latest results for all quicklotto lotteries (live)
"""
import sys
import os
import json
import asyncio
from pathlib import Path

# Add predictor to path
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

try:
    from mcp.server import Server
    from mcp.server.streamable_http import StreamableHTTPServerTransport
    from mcp.types import Tool, TextContent
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    print("MCP SDK not installed. Install with: pip install mcp")
    print("Falling back to simple JSON-RPC server...")


# ============================================================
# Tool implementations (reusing our predictor)
# ============================================================

def tool_list_lotteries():
    """List all available lotteries."""
    from cli_json import cmd_lotteries
    lots = cmd_lotteries()
    
    lines = [f"LotteryPredictor supports {len(lots)} lotteries ({sum(1 for l in lots if l['has_data'])} with data):\n"]
    for l in lots:
        format_str = f"{l['main_picks']}/{l['main_pool_size']}"
        if l.get('bonus_picks'):
            format_str += f"+{l['bonus_picks']}/{l['bonus_pool_size']}"
        marker = '✓' if l['has_data'] else '✗'
        lines.append(f"- {marker} {l['key']} ({l['name']}, {l['country']}): {format_str}, odds 1:{l['odds_jackpot']:,}")
    return '\n'.join(lines)


def tool_describe_lottery(lottery_key: str):
    """Get details of a specific lottery."""
    from cli_json import cmd_describe
    info = cmd_describe(lottery_key)
    
    lines = [f"📊 {info['name']} ({info['country']})"]
    lines.append(f"   Format: {info['main_picks']}/{info['main_pool_size']}",)
    if info.get('bonus_picks'):
        lines.append(f"   Bonus: {info['bonus_picks']}/{info['bonus_pool_size']}")
    lines.append(f"   Total draws loaded: {info['total_draws']}")
    lines.append(f"   Date range: {info.get('date_range', ['?', '?'])[0]} → {info.get('date_range', ['?', '?'])[1]}")
    lines.append(f"   Jackpot odds: 1 in {info['odds_jackpot']:,}")
    lines.append(f"   Min jackpot: {info['currency']} {info['min_jackpot']:,}")
    if info.get('last_draw'):
        ld = info['last_draw']
        nums = ' '.join(f'{n:02d}' for n in ld['main_numbers'])
        lines.append(f"   Last draw #{ld['draw_number']} ({ld['date']}): {nums}")
    return '\n'.join(lines)


def tool_list_engines():
    """List all prediction engines."""
    from cli_json import cmd_engines
    engines = cmd_engines()
    
    lines = [f"LotteryPredictor has {len(engines)} engines:\n"]
    for e in engines:
        lines.append(f"- {e['key']}: {e['description']}")
    return '\n'.join(lines)


def tool_predict(lottery_key: str, engine: str = 'ensemble'):
    """Generate prediction."""
    from cli_json import cmd_predict
    result = cmd_predict(lottery_key, engine)
    
    pred_str = ' '.join(f'{n:02d}' for n in result['prediction'])
    lines = [
        f"🎯 Prediction for {result['lottery']} using {result['engine']}:",
        f"   Numbers: {pred_str}",
    ]
    if result.get('last_draw'):
        ld = result['last_draw']
        last_str = ' '.join(f'{n:02d}' for n in ld['main_numbers'])
        lines.append(f"   Last draw #{ld['draw_number']} ({ld['date']}): {last_str}")
    if result.get('explanations'):
        lines.append("\n   Justification per number:")
        for exp in result['explanations']:
            reasons = ', '.join(exp['top_reasons'])
            lines.append(f"   #{exp['rank']}: {exp['number']:02d} (score {exp['combined_score']:.2f}) — {reasons}")
    return '\n'.join(lines)


def tool_backtest(lottery_key: str):
    """Get cached backtest results."""
    from cli_json import cmd_backtest
    result = cmd_backtest(lottery_key)
    
    if 'error' in result:
        return f"No backtest available for {lottery_key}. Run: python3 main.py --lottery {lottery_key} --backtest all"
    
    lines = [f"📊 Backtest for {lottery_key} ({result['comparison'][0]['tested']} draws tested):\n"]
    bl = result['random_baseline']
    lines.append(f"🎲 Random baseline: {bl['avg_hits']:.3f} avg hits, max {bl['max_hits']}")
    lines.append("")
    lines.append("Engine results (sorted by avg hits):")
    for c in result['comparison']:
        diff = c['avg_hits'] - bl['avg_hits']
        pct = (diff / bl['avg_hits']) * 100 if bl['avg_hits'] > 0 else 0
        marker = '⭐' if pct > 30 else '✅' if pct > 10 else '⚠️' if pct > 0 else '❌'
        lines.append(f"  {marker} {c['engine']:<22} avg={c['avg_hits']:.3f} max={c['max_hits']} {pct:+.1f}%")
    return '\n'.join(lines)


def tool_get_latest_results():
    """Get latest results for all quicklotto lotteries (live)."""
    sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor/data_fetcher')
    from quicklotto_client import get_latest_results
    
    latest = get_latest_results()
    lines = [f"Live latest results from quicklotto.io ({len(latest)} lotteries):\n"]
    for name, draw in list(latest.items())[:20]:
        nums = ', '.join(str(n) for n in draw['main_numbers'])
        bonus = f" + bonus: {draw['bonus_numbers']}" if draw['bonus_numbers'] else ""
        lines.append(f"- {name} ({draw['date']}): {nums}{bonus}")
    return '\n'.join(lines)


# ============================================================
# Simple JSON-RPC server (fallback when MCP SDK not available)
# ============================================================

async def handle_jsonrpc(request: dict) -> dict:
    """Handle a JSON-RPC request."""
    method = request.get('method', '')
    params = request.get('params', {})
    id_ = request.get('id')
    
    if method == 'initialize':
        return {
            'jsonrpc': '2.0',
            'id': id_,
            'result': {
                'protocolVersion': '2025-06-18',
                'capabilities': {'tools': {}},
                'serverInfo': {
                    'name': 'LotteryPredictor MCP',
                    'version': '3.0.0',
                },
                'instructions': 'LotteryPredictor MCP — 47 lotteries, 10 engines, 22K+ historical draws. Tools: list_lotteries, describe_lottery, list_engines, predict, predict_with_explanation, backtest, get_latest_results.',
            }
        }
    
    if method == 'tools/list':
        tools = [
            {
                'name': 'list_lotteries',
                'description': 'List all 47 available lotteries with format, country, and odds.',
                'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
            },
            {
                'name': 'describe_lottery',
                'description': 'Get details of a specific lottery (format, total draws, last result).',
                'inputSchema': {
                    'type': 'object',
                    'properties': {'lottery': {'type': 'string', 'description': 'Lottery key (e.g. euromillions, ql_superenalotto)'}},
                    'required': ['lottery'],
                    'additionalProperties': False,
                },
            },
            {
                'name': 'list_engines',
                'description': 'List all 10 prediction engines available.',
                'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
            },
            {
                'name': 'predict',
                'description': 'Generate a prediction for a lottery using a specific engine.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'lottery': {'type': 'string', 'description': 'Lottery key'},
                        'engine': {'type': 'string', 'description': 'Engine key (default: ensemble)', 'default': 'ensemble'},
                    },
                    'required': ['lottery'],
                    'additionalProperties': False,
                },
            },
            {
                'name': 'backtest',
                'description': 'Get cached backtest results for a lottery.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {'lottery': {'type': 'string'}},
                    'required': ['lottery'],
                    'additionalProperties': False,
                },
            },
            {
                'name': 'get_latest_results',
                'description': 'Get latest results for all quicklotto lotteries (live from quicklotto.io).',
                'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
            },
        ]
        return {'jsonrpc': '2.0', 'id': id_, 'result': {'tools': tools}}
    
    if method == 'tools/call':
        tool_name = params.get('name', '')
        args = params.get('arguments', {})
        
        try:
            if tool_name == 'list_lotteries':
                text = tool_list_lotteries()
            elif tool_name == 'describe_lottery':
                text = tool_describe_lottery(args.get('lottery', ''))
            elif tool_name == 'list_engines':
                text = tool_list_engines()
            elif tool_name == 'predict':
                text = tool_predict(args.get('lottery', ''), args.get('engine', 'ensemble'))
            elif tool_name == 'backtest':
                text = tool_backtest(args.get('lottery', ''))
            elif tool_name == 'get_latest_results':
                text = tool_get_latest_results()
            else:
                return {'jsonrpc': '2.0', 'id': id_, 'error': {'code': -32601, 'message': f'Unknown tool: {tool_name}'}}
            
            return {
                'jsonrpc': '2.0',
                'id': id_,
                'result': {'content': [{'type': 'text', 'text': text}]},
            }
        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': id_,
                'error': {'code': -32603, 'message': f'Internal error: {str(e)}'},
            }
    
    return {'jsonrpc': '2.0', 'id': id_, 'error': {'code': -32601, 'message': f'Unknown method: {method}'}}


# ============================================================
# HTTP server using aiohttp
# ============================================================

async def main():
    """Run the MCP server."""
    try:
        from aiohttp import web
    except ImportError:
        print("aiohttp not installed. Install with: pip install aiohttp")
        return
    
    async def handle_mcp(request):
        """Handle MCP request."""
        try:
            body = await request.json()
            
            # Handle batch requests
            if isinstance(body, list):
                responses = []
                for req in body:
                    resp = await handle_jsonrpc(req)
                    responses.append(resp)
                return web.json_response(responses)
            else:
                response = await handle_jsonrpc(body)
                return web.json_response(response)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    app = web.Application()
    app.router.add_post('/mcp', handle_mcp)
    
    port = int(os.environ.get('MCP_PORT', 8787))
    print(f"\n🎲 LotteryPredictor MCP Server v3.0")
    print(f"   Endpoint: http://localhost:{port}/mcp")
    print(f"   Tools: list_lotteries, describe_lottery, list_engines, predict, backtest, get_latest_results")
    print(f"   Lotteries: 47 | Engines: 10 | Total historical draws: 22,692")
    print(f"\n   Press Ctrl+C to stop.\n")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)  # nosec B104 — intentional: MCP server accepts LAN/container connections
    await site.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
