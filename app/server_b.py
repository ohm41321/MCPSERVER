import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import uvicorn

# Add current directory to Python path for imports
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server B", description="MCP Server B running on port 3002")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class MCPServerB:
    def __init__(self, server_id: str):
        self.server_id = server_id
        self.clients = set()

    async def handle_sse_connection(self, request: Request):
        """Handle SSE connection for MCP client"""
        async def generate_events():
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'server': 'server_b'})}\n\n"

            # Keep connection alive
            try:
                while True:
                    # Check if client disconnected
                    if await request.is_disconnected():
                        break
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass

        return HTMLResponse(
            content="".join([chunk async for chunk in generate_events()]),
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    async def list_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List available tools for this server"""
        try:
            tools = db_manager.get_active_tools_by_server(self.server_id)

            mcp_tools = []
            for tool in tools:
                mcp_tool = {
                    'id': tool['id'],
                    'name': tool['name'],
                    'description': tool['description'] or f"Tool: {tool['name']}",
                    'parameters': tool['parameters'],
                    'api_url': tool['api_url'],
                    'http_method': tool['http_method'],
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'operation': {
                                'type': 'string',
                                'description': 'Operation to perform',
                                'enum': ['execute', 'info']
                            }
                        },
                        'required': ['operation']
                    }
                }

                # Add tool parameters to schema
                for param in tool['parameters']:
                    mcp_tool['inputSchema']['properties'][param['name']] = {
                        'type': param['type'],
                        'description': param['description']
                    }
                    if param['required']:
                        mcp_tool['inputSchema']['required'].append(param['name'])

                mcp_tool['server_name'] = 'server_b'
                mcp_tools.append(mcp_tool)

            return {'tools': mcp_tools}

        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {'tools': []}

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""
        start_time = datetime.now()

        try:
            # Find the tool in database
            tool = db_manager.get_tool_by_name(self.server_id, tool_name)
            if not tool:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

            # Execute the tool based on its name
            result = await self._execute_tool_logic(tool, args)
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log successful execution
            db_manager.log_tool_execution(
                tool['id'],
                self.server_id,
                args,
                result,
                'success',
                int(execution_time)
            )

            return {
                'content': [json.dumps(result, indent=2)],
                'success': True
            }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log failed execution
            tool = db_manager.get_tool_by_name(self.server_id, tool_name)
            if tool:
                db_manager.log_tool_execution(
                    tool['id'],
                    self.server_id,
                    args,
                    {'error': str(e)},
                    'error',
                    int(execution_time)
                )

            return {
                'content': [f"Error: {str(e)}"],
                'success': False,
                'isError': True
            }

    async def _execute_tool_logic(self, tool: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool-specific logic"""
        if tool.get('api_url'):
            import httpx
            api_url = tool['api_url'].format(**args)
            async with httpx.AsyncClient() as client:
                if tool['http_method'] == 'GET':
                    response = await client.get(api_url, params=args)
                elif tool['http_method'] == 'POST':
                    response = await client.post(api_url, json=args)
                else:
                    raise ValueError(f"Unsupported HTTP method: {tool['http_method']}")
                response.raise_for_status()
                return response.json()
        else:
            operation = args.get('operation', 'execute')
            if tool['name'] == 'get_weather':
                return await self._handle_weather(operation, args)
            elif tool['name'] == 'get_time':
                return await self._handle_time(operation, args)
            elif tool['name'] == 'data_processor':
                return await self._handle_data_processor(operation, args)
            elif tool['name'] == 'text_analyzer':
                return await self._handle_text_analyzer(operation, args)
            elif tool['name'] == 'api_client':
                return await self._handle_api_client(operation, args)
            else:
                raise ValueError(f"Unknown tool: {tool['name']}")

    async def _handle_weather(self, operation: str, args: Any) -> Dict[str, Any]:
        """Handle weather operations"""
        if operation == 'execute':
            return {
                'operation': 'get_weather',
                'location': args.get('location', 'Bangkok'),
                'temperature': 28,
                'condition': 'Sunny',
                'humidity': 65,
                'server': 'Server B'
            }
        else:
            raise ValueError(f"Unknown weather operation: {operation}")

    async def _handle_time(self, operation: str, args: Any) -> Dict[str, Any]:
        """Handle time operations"""
        if operation == 'execute':
            return {
                'operation': 'get_time',
                'location': args.get('location', 'UTC'),
                'current_time': datetime.now().isoformat(),
                'timezone': 'UTC',
                'server': 'Server B'
            }
        else:
            raise ValueError(f"Unknown time operation: {operation}")

    async def _handle_data_processor(self, operation: str, args: Any) -> Dict[str, Any]:
        """Handle data processing operations"""
        if operation == 'execute':
            return {
                'operation': 'data_processor',
                'action': args.get('action', 'process'),
                'data_size': len(str(args.get('data', {}))),
                'processed': True,
                'server': 'Server B'
            }
        else:
            raise ValueError(f"Unknown data processor operation: {operation}")

    async def _handle_text_analyzer(self, operation: str, args: Any) -> Dict[str, Any]:
        """Handle text analysis operations"""
        if operation == 'execute':
            text = args.get('text', '')
            return {
                'operation': 'text_analyzer',
                'text_length': len(text),
                'word_count': len(text.split()) if text else 0,
                'language': 'en',
                'server': 'Server B'
            }
        else:
            raise ValueError(f"Unknown text analyzer operation: {operation}")

    async def _handle_api_client(self, operation: str, args: Any) -> Dict[str, Any]:
        """Handle API client operations"""
        if operation == 'execute':
            return {
                'operation': 'api_client',
                'url': args.get('url', 'https://api.example.com'),
                'method': args.get('method', 'GET'),
                'status': 'mock_response',
                'server': 'Server B'
            }
        else:
            raise ValueError(f"Unknown API client operation: {operation}")

# Global MCP server instance
mcp_server_b = None

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    global mcp_server_b

    # Test database connection
    if db_manager.test_connection():
        logger.info("✅ Database connected successfully")

        # Get or create server info
        server_info = db_manager.get_server_by_name('server_b')
        if server_info:
            mcp_server_b = MCPServerB(server_info['id'])
            logger.info(f"🚀 MCP Server B initialized with server_id: {server_info['id']}")
        else:
            logger.error("❌ Server B not found in database")
    else:
        logger.error("❌ Database connection failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_connected = db_manager.test_connection()
    return {
        'status': 'healthy',
        'server': 'Server B',
        'port': 3002,
        'database': 'connected' if db_connected else 'disconnected',
        'timestamp': datetime.now().isoformat()
    }

@app.get("/info")
async def server_info():
    """Server information endpoint"""
    try:
        server = db_manager.get_server_by_name('server_b')
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        tools_count = db_manager.get_server_tools_count(server['id'])

        return {
            'server': server,
            'tools_count': tools_count,
            'active_tools': db_manager.get_active_tools_by_server(server['id'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch server info: {str(e)}")

@app.get("/tools")
async def list_tools_endpoint():
    """List all tools for this server"""
    if not mcp_server_b:
        raise HTTPException(status_code=500, detail="MCP Server B not initialized")
    return await mcp_server_b.list_tools()

@app.get("/check-tools")
async def check_tools_endpoint():
    """Check all available tools for this server"""
    if not mcp_server_b:
        raise HTTPException(status_code=500, detail="MCP Server B not initialized")
    
    tools_data = await mcp_server_b.list_tools()
    
    # Simplify the output to only include essential information
    simplified_tools = []
    for tool in tools_data.get("tools", []):
        simplified_tools.append({
            "name": tool.get("name"),
            "description": tool.get("description"),
            "api_url": tool.get("api_url"),
            "http_method": tool.get("http_method"),
        })
        
    return {
        "server": "Server B",
        "tools": simplified_tools
    }

@app.post("/tools")
async def register_tool(tool_data: Dict[str, Any]):
    """Register a new tool"""
    try:
        server = db_manager.get_server_by_name('server_b')
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        # Add server_id to tool data
        tool_data['id'] = str(uuid.uuid4())
        tool_data['server_id'] = server['id']

        tool = db_manager.register_tool(tool_data)
        return {'tool': tool}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")

@app.put("/tools/{tool_id}")
async def update_tool(tool_id: str, tool_data: Dict[str, Any]):
    """Update an existing tool"""
    try:
        updated_tool = db_manager.update_tool(tool_id, tool_data)
        if not updated_tool:
            raise HTTPException(status_code=404, detail="Tool not found or could not be updated")
        return updated_tool
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")

@app.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool"""
    try:
        success = db_manager.delete_tool(tool_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found or could not be deleted")
        return {"message": "Tool deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP client connections"""
    if mcp_server_b:
        return await mcp_server_b.handle_sse_connection(request)
    else:
        raise HTTPException(status_code=500, detail="MCP Server B not initialized")

@app.post("/tools/call")
async def call_tool(request: Dict[str, Any]):
    """Call/execute a tool"""
    if not mcp_server_b:
        raise HTTPException(status_code=500, detail="MCP Server B not initialized")

    tool_name = request.get('name')
    args = request.get('arguments', {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="Tool name is required")

    result = await mcp_server_b.execute_tool(tool_name, args)
    return result

if __name__ == "__main__":
    port = int(os.getenv('PORT_B', 3002))
    logger.info(f"🚀 Starting MCP Server B on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)