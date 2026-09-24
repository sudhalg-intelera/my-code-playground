# Quick viewer for the PII token map stored in the Redis container (see
# docker-compose.yml's `redis` service and backend/pii/guard.py).
#
# Usage:
#   .\view-token-map.ps1                    - lists every session currently in Redis
#   .\view-token-map.ps1 -SessionId <id>    - shows that session's token -> real value map
param(
    [string]$SessionId
)

if (-not $SessionId) {
    Write-Host "No -SessionId given - listing every session currently in Redis:`n"
    docker exec -it travel_agent_redis redis-cli KEYS "pii_token_map:*"
    Write-Host "`nCopy a session ID (from the sidebar in the app, or a key above) and re-run:"
    Write-Host "  .\view-token-map.ps1 -SessionId <id>"
    exit
}

docker exec -it travel_agent_redis redis-cli HGETALL "pii_token_map:$SessionId"
