FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MCP_TRANSPORT=streamable-http
ENV MCP_PORT=8501
EXPOSE 8501
CMD ["python", "mcp_server.py"]
