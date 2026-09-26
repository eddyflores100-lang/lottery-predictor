# NLAB-04: MCP Authorization Model

## Per-Tool Permission Matrix

Each MCP tool declares required permissions. The server checks
authorization before executing any tool.

| Tool              | Permission  | Side Effects | Network | Filesystem |
|-------------------|-------------|--------------|---------|------------|
| list_lotteries    | readonly    | none         | no      | read-only  |
| describe_lottery  | readonly    | none         | no      | read-only  |
| list_engines      | readonly    | none         | no      | no         |
| predict           | execute     | none         | no      | read-only  |
| backtest          | readonly    | none         | no      | read-only  |
| get_latest_results| network     | none         | yes*    | no         |

*network only to allowlisted domains (quicklotto.io)

## Permission Hierarchy

```
anonymous → denied (all tools)
   ↓
readonly token → list_lotteries, describe_lottery, list_engines, backtest
   ↓
execute token → above + predict
   ↓
admin token → above + get_latest_results (network access)
```

## Implementation

The MCP server checks `MCP_AUTH_TOKEN` environment variable.
Clients pass their token in the `Authorization: Bearer <token>` header.

```python
PERMISSIONS = {
    'readonly': ['list_lotteries', 'describe_lottery', 'list_engines', 'backtest'],
    'execute': ['list_lotteries', 'describe_lottery', 'list_engines', 'predict', 'backtest'],
    'admin': ['list_lotteries', 'describe_lottery', 'list_engines', 'predict', 'backtest', 'get_latest_results'],
}

def check_permission(token: str, tool: str) -> bool:
    # In production: lookup token → permission level from DB/vault
    # For now: single token from env, maps to 'execute' level
    expected = os.environ.get('MCP_AUTH_TOKEN', '')
    if not expected or token != expected:
        return False
    return tool in PERMISSIONS.get('execute', [])
```

## Tool Declaration Schema

Each tool must declare its full security surface:

```json
{
  "name": "predict",
  "description": "Generate prediction",
  "inputSchema": { ... },
  "permissions": {
    "required_level": "execute",
    "side_effects": false,
    "network_access": false,
    "filesystem_access": "read-only",
    "cpu_intensive": true,
    "max_duration_seconds": 60
  }
}
```
