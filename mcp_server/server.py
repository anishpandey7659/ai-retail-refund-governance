from fastmcp import FastMCP
from mcp_server.tools import register_tools

mcp = FastMCP("ReturnGuard")

# Register your tools here
register_tools(mcp)

app = mcp.http_app(
    transport="streamable-http",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8070)

# uv run fastmcp dev inspector mcp_server/server.py