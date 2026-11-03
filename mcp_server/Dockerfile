FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Python environment configuration
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Copy root dependency configuration
COPY pyproject.toml uv.lock ./

# Install only MCP dependencies
RUN uv sync --frozen --no-dev --no-install-project --group mcp

# Copy application source code
COPY knowledge/ ./knowledge/
COPY mcp_server/ ./mcp_server/

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8070

# Start MCP server
CMD ["python", "-m", "mcp_server.server"]