import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import google.generativeai as genai
import re
import uuid

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup templates and static files
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # Go up one level to project root
templates_dir = os.path.join(current_dir, "web", "templates")
static_dir = os.path.join(current_dir, "web", "static")

# Create directories if they don't exist
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)

app = FastAPI(title="MCP Frontend API", description="Unified API for both MCP Servers")

# Add middleware to prevent caching for all responses
@app.middleware("http")
async def add_cache_control_headers(request, call_next):
    response = await call_next(request)

    # Add cache control headers to all responses
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

# Mount static files with cache control
class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send):
        response = await super().__call__(scope, receive, send)

        # Add no-cache headers to static files
        if hasattr(response, 'headers'):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

app.mount("/static", NoCacheStaticFiles(directory=static_dir), name="static")


@app.get("/api")
async def root():
    """Root endpoint with API information"""
    response_data = {
        "name": "MCP Frontend API",
        "description": "Unified API for MCP Server A and Server B",
        "servers": {
            "server_a": {
                "port": 3001,
                "tools": "finance_tools",
                "url": "http://localhost:3001"
            },
            "server_b": {
                "port": 3002,
                "tools": "utility_tools",
                "url": "http://localhost:3002"
            }
        },
        "endpoints": {
            "home": "/",
            "chat": "/chat/{server_name}",
            "manage_tools": "/manage-tools/{server_name}",
            "servers": "/servers",
            "all_tools": "/tools",
            "create_tool": "POST /tools",
            "update_tool": "PUT /tools/{tool_id}",
            "delete_tool": "DELETE /tools/{tool_id}",
            "execute_tool": "/tools/execute",
            "server_tools": "/servers/{server_name}/tools",
            "ask_question": "/ask",
            "ask_get": "/ask?question=your_question&server_name=server_a",
            "server_status": "/servers/{server_name}/status",
            "select_server": "/select-server"
        }
    }

    # Add cache control headers to prevent caching of API info
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return JSONResponse(content=response_data, headers=headers)




@app.post("/tools/execute")
async def execute_tool(request: Dict[str, Any]):
    """Execute tool on specified server"""
    try:
        tool_name = request.get('tool_name')
        server_name = request.get('server')
        args = request.get('arguments', {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        if not server_name:
            raise HTTPException(status_code=400, detail="server is required")

        # Validate server
        server = db_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")

        # Validate tool exists on the server
        tool = db_manager.get_tool_by_name(server['id'], tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found on server '{server_name}'")

        # Route to appropriate server
        if server_name == 'server_a':
            # Call Server A
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:3001/tools/call",
                    json={"name": tool_name, "arguments": args},
                    timeout=30.0
                )
                response_data = {
                    "tool": tool_name,
                    "server": server_name,
                    "result": response.json(),
                    "status": "success"
                }
        else:
            # Call Server B
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:3002/tools/call",
                    json={"name": tool_name, "arguments": args},
                    timeout=30.0
                )
                response_data = {
                    "tool": tool_name,
                    "server": server_name,
                    "result": response.json(),
                    "status": "success"
                }

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")

@app.get("/tools/{tool_name}/execute")
async def execute_tool_get(tool_name: str, server: str, **kwargs):
    """Execute tool using GET request (for simple tools)"""
    try:
        # Convert query parameters to arguments
        args = kwargs

        # Use POST endpoint
        result = await execute_tool({
            "tool_name": tool_name,
            "server": server,
            "arguments": args
        })

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=result, headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")

@app.post("/ask")
async def ask_question(request: Dict[str, Any]):
    """Ask question to selected agent with AI assistance"""
    try:
        question = request.get('question')
        agent_id = request.get('agent_id')

        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")

        servers = db_manager.get_servers_for_agent(agent_id)
        if not servers:
            raise HTTPException(status_code=404, detail="No servers found for this agent")

        all_tools = []
        for server in servers:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    tools_response = await client.get(f"{server['url']}/tools", timeout=10.0)
                    tools_response.raise_for_status()
                    tools_data = tools_response.json()
                    all_tools.extend(tools_data.get('tools', []))
            except (httpx.TimeoutException, httpx.ConnectError):
                logger.error(f"Could not connect to server {server['name']}")

        if not all_tools:
            response_data = {"answer": "There are no tools available for this agent."}
            headers = {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
            return JSONResponse(content=response_data, headers=headers)

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        tools_for_prompt = [{k: v for k, v in tool.items() if k in ['name', 'description', 'inputSchema', 'server_name']} for tool in all_tools]

        prompt_select_tool = f"""
        You are an expert at selecting the correct tool to answer a user's question.
        Here is the user's question: "{question}"
        Here is a list of available tools:
        {json.dumps(tools_for_prompt, indent=2)}

        Based on the user's question, which tool should be used?
        You must respond with a JSON object with three keys: "tool_name", "arguments", and "server_name".
        "tool_name" must be the name of the selected tool.
        "arguments" must be an object containing the arguments for the tool. If the tool has parameters, you must extract the values from the user's question.
        "server_name" must be the name of the server where the tool is located.
        If no tool is suitable, respond with {{"tool_name": "none", "arguments": {{}}, "server_name": "none"}}.
        """
        response_select_tool = model.generate_content(prompt_select_tool)
        logger.info(f"Gemini tool selection response: {response_select_tool.text}")

        try:
            json_str = response_select_tool.text
            match = re.search(r"```json\n({.*?})\n```", json_str, re.DOTALL)
            if match:
                json_str = match.group(1)

            tool_selection = json.loads(json_str)
            tool_name = tool_selection.get("tool_name")
            arguments = tool_selection.get("arguments", {})
            server_name = tool_selection.get("server_name")
        except (json.JSONDecodeError, AttributeError):
            raise HTTPException(status_code=500, detail="Gemini did not return a valid tool selection.")

        if tool_name == "none" or not tool_name:
            response_data = {"answer": "I'm sorry, I don't have a tool that can answer that question."}
            headers = {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
            return JSONResponse(content=response_data, headers=headers)

        target_server = next((s for s in servers if s['server_name'] == server_name), None)
        if not target_server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found for this agent.")

        try:
            async with httpx.AsyncClient() as client:
                tool_response = await client.post(
                    f"{target_server['url']}/tools/call",
                    json={"name": tool_name, "arguments": {"operation": "execute", **arguments}},
                    timeout=30.0
                )
                tool_response.raise_for_status()
                tool_result = tool_response.json()
        except (httpx.TimeoutException, httpx.ConnectError):
            raise HTTPException(status_code=503, detail=f"Could not execute tool '{tool_name}'.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error executing tool: {e.response.text}")

        prompt_summarize = f"""
        You are an expert at summarizing technical information for a user.
        The user asked: "{question}"
        To answer this, the tool "{tool_name}" on server "{server_name}" was used.
        The result from the tool is:
        {json.dumps(tool_result, indent=2)}

        Based on this information, generate a friendly and concise answer for the user.
        You MUST mention the tool and the server in your answer. Start your answer with "Using the '{tool_name}' tool on the '{server_name}' server, ...".
        """
        response_summarize = model.generate_content(prompt_summarize)

        response_data = {
            "answer": response_summarize.text,
            "question": question,
            "server": server_name,
            "selected_tool": tool_name,
            "tool_result": tool_result,
            "status": "success"
        }

        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")
@app.get("/ask")
async def ask_question_get(question: str, server_url: str = None, server_name: str = None):
    """Ask question using GET request"""
    try:
        if not server_url and not server_name:
            raise HTTPException(status_code=400, detail="server_url or server_name parameter is required")

        result = await ask_question({
            "question": question,
            "server_url": server_url,
            "server_name": server_name
        })

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=result, headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@app.get("/servers")
async def get_all_servers():
    """Get all available servers"""
    try:
        servers = db_manager.get_all_servers()

        response_data = {
            "servers": [
                {
                    "id": server['id'],
                    "name": server['name'],
                    "server_name": server['server_name'],
                    "port": server['port'],
                    "url": server['url'] or f"http://localhost:{server['port']}",
                    "status": server['status'],
                    "enabled": server['enabled'],
                    "is_active": server['is_active']
                }
                for server in servers
            ],
            "total_servers": len(servers),
            "timestamp": datetime.now().isoformat()
        }

        # Add cache control headers to prevent caching
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except Exception as e:
        logger.error(f"Error getting all servers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get servers: {str(e)}")


@app.get("/servers/{server_name}/status")
async def get_server_status(server_name: str):
    """Get detailed status of a specific server including tools"""
    try:
        server = db_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")

        # Get tools for this server
        tools = db_manager.get_tools_by_server(server['id'])

        # Check if server is responding
        import httpx
        server_url = f"http://localhost:{3001 if server_name == 'server_a' else 3002}"
        status = "unknown"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{server_url}/health", timeout=5.0)
                if response.status_code == 200:
                    health_data = response.json()
                    status = health_data.get('status', 'unknown')
                else:
                    status = f"error_{response.status_code}"
        except:
            status = "unreachable"

        response_data = {
            "server": {
                "id": server['id'],
                "name": server['name'],
                "server_name": server_name,
                "port": 3001 if server_name == 'server_a' else 3002,
                "url": server_url,
                "status": status,
                "enabled": server['enabled'],
                "database_status": "connected" if db_manager.test_connection() else "disconnected"
            },
            "tools": [
                {
                    "id": tool['id'],
                    "name": tool['name'],
                    "description": tool['description'],
                    "parameters": tool['parameters'],
                    "api_url": tool['api_url'],
                    "http_method": tool['http_method'],
                    "ready": True  # Assuming all tools are ready if server is up
                }
                for tool in tools
            ],
            "tools_count": len(tools),
            "timestamp": datetime.now().isoformat()
        }

        # Add cache control headers to prevent caching
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server status: {str(e)}")

@app.post("/select-server")
async def select_server(request: Dict[str, Any]):
    """Select a server and get its information with tools"""
    try:
        server_name = request.get('server_name')
        server_url = request.get('server_url')

        if not server_name and not server_url:
            raise HTTPException(status_code=400, detail="server_name or server_url is required")

        # If only URL provided, try to determine server name
        if server_url and not server_name:
            if "3001" in server_url:
                server_name = "server_a"
            elif "3002" in server_url:
                server_name = "server_b"
            else:
                raise HTTPException(status_code=400, detail="Cannot determine server name from URL")

        # Get server info and tools
        server = db_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")

        tools = db_manager.get_tools_by_server(server['id'])

        response_data = {
            "selected_server": {
                "id": server['id'],
                "name": server['name'],
                "server_name": server_name,
                "port": 3001 if server_name == 'server_a' else 3002,
                "url": server_url or f"http://localhost:{3001 if server_name == 'server_a' else 3002}",
                "status": server['status'],
                "enabled": server['enabled']
            },
            "available_tools": [
                {
                    "id": tool['id'],
                    "name": tool['name'],
                    "description": tool['description'],
                    "parameters": tool['parameters'],
                    "can_execute": True
                }
                for tool in tools
            ],
            "total_tools": len(tools),
            "message": f"เลือก Server {server_name} สำเร็จแล้ว"
        }

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select server: {str(e)}")

# Tools Management API
@app.post("/tools")
async def create_tool(request: Dict[str, Any]):
    """Create a new tool"""
    try:
        tool_data = request
        server_name = request.get('server_name')

        if not server_name:
            raise HTTPException(status_code=400, detail="server_name is required")

        # Get server info
        server = db_manager.get_server_by_name(server_name)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")

        # Add server_id to tool data
        tool_data['server_id'] = server['id']

        # Create tool in database
        tool = db_manager.register_tool(tool_data)

        response_data = {
            "tool": tool,
            "message": "Tool created successfully"
        }

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}")

# Agent Management API
@app.post("/agents")
async def create_agent(request: Dict[str, Any]):
    """Create a new agent"""
    try:
        agent_data = request
        agent = db_manager.create_agent(agent_data)
        return {"agent": agent, "message": "Agent created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@app.get("/agents")
async def get_all_agents():
    """Get all agents"""
    try:
        agents = db_manager.get_all_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent"""
    try:
        agent = db_manager.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        agent['servers'] = db_manager.get_servers_for_agent(agent_id)
        return {"agent": agent}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@app.put("/agents/{agent_id}")
async def update_agent(agent_id: str, request: Dict[str, Any]):
    """Update an existing agent"""
    try:
        agent_data = request
        agent = db_manager.update_agent(agent_id, agent_data)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"agent": agent, "message": "Agent updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        deleted = db_manager.delete_agent(agent_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@app.post("/agents/{agent_id}/servers")
async def add_server_to_agent(agent_id: str, request: Dict[str, Any]):
    """Add a server to an agent"""
    try:
        server_id = request.get('server_id')
        if not server_id:
            raise HTTPException(status_code=400, detail="server_id is required")
        added = db_manager.add_server_to_agent(agent_id, server_id)
        if not added:
            raise HTTPException(status_code=500, detail="Failed to add server to agent")
        return {"message": "Server added to agent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add server to agent: {str(e)}")

@app.post("/agents/{agent_id}/servers/by_url")
async def add_server_to_agent_by_url(agent_id: str, request: Dict[str, Any]):
    """Add a server to an agent by URL"""
    try:
        url = request.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="url is required")

        server = db_manager.get_server_by_url(url)
        if not server:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{url}/tools", timeout=5.0)
                    response.raise_for_status()
                    # Assuming the server has a name property in its /tools response
                    # This part might need adjustment based on the actual server implementation
                    server_name = response.json().get("name", "Unnamed Server")
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError):
                raise HTTPException(status_code=400, detail="Could not connect to the server or it is not a valid MCP server.")

            server_data = {
                "id": str(uuid.uuid4()),
                "name": server_name,
                "url": url,
                "status": "connected",
                "enabled": True
            }
            server = db_manager.create_server(server_data)

        added = db_manager.add_server_to_agent(agent_id, server['id'])
        if not added:
            raise HTTPException(status_code=500, detail="Failed to add server to agent")

        return {"message": "Server added to agent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add server to agent: {str(e)}")

@app.delete("/agents/{agent_id}/servers/{server_id}")
async def remove_server_from_agent(agent_id: str, server_id: str):
    """Remove a server from an agent"""
    try:
        removed = db_manager.remove_server_from_agent(agent_id, server_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Server not found for this agent")
        return {"message": "Server removed from agent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove server from agent: {str(e)}")

@app.get("/agents/{agent_id}/servers")
async def get_servers_for_agent(agent_id: str):
    """Get all servers for a specific agent"""
    try:
        servers = db_manager.get_servers_for_agent(agent_id)
        return {"servers": servers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get servers for agent: {str(e)}")



@app.put("/tools/{tool_id}")
async def update_tool(tool_id: str, request: Dict[str, Any]):
    """Update an existing tool"""
    try:
        tool_data = request

        # Update tool in database
        updated_tool = db_manager.updateTool(tool_id, tool_data)

        response_data = {
            "tool": updated_tool,
            "message": "Tool updated successfully"
        }

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except Exception as e:
        logger.error(f"Error updating tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")

@app.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool"""
    try:
        # Delete tool from database
        deleted = db_manager.deleteTool(tool_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Tool not found")

        response_data = {
            "message": "Tool deleted successfully"
        }

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page for agent selection"""
    try:
        # Get all agents from database
        agents = db_manager.get_all_agents()

        return templates.TemplateResponse("index.html", {
            "request": request,
            "agents": agents
        })

    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "agents": [],
            "error": f"Error loading agents: {str(e)}"
        })

@app.get("/chat/{agent_id}", response_class=HTMLResponse)
async def chat_page(request: Request, agent_id: str):
    """Chat page for selected agent"""
    try:
        agent = db_manager.get_agent_by_id(agent_id)
        if not agent:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": f"Agent '{agent_id}' not found"
            })

        servers = db_manager.get_servers_for_agent(agent_id)
        all_tools = []
        for server in servers:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    tools_response = await client.get(f"{server['url']}/tools", timeout=10.0)
                    tools_response.raise_for_status()
                    tools_data = tools_response.json()
                    server['tools'] = tools_data.get('tools', [])
                    all_tools.extend(server['tools'])
            except (httpx.TimeoutException, httpx.ConnectError):
                logger.error(f"Could not connect to server {server['name']}")
                server['tools'] = []

        return templates.TemplateResponse("chat.html", {
            "request": request,
            "agent": agent,
            "servers": servers,
            "all_tools": all_tools
        })

    except Exception as e:
        logger.error(f"Error loading chat page: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error loading chat: {str(e)}"
        })

@app.get("/manage/{agent_id}", response_class=HTMLResponse)
async def agent_manage_page(request: Request, agent_id: str):
    """Agent management page"""
    try:
        agent = db_manager.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_servers = db_manager.get_servers_for_agent(agent_id)
        all_servers = db_manager.get_all_servers()

        return templates.TemplateResponse("agent_manage.html", {
            "request": request,
            "agent": agent,
            "agent_servers": agent_servers,
            "all_servers": all_servers
        })
    except Exception as e:
        logger.error(f"Error loading agent management page: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error loading agent management page: {str(e)}"
        })

@app.get("/manage-tools/{server_name}", response_class=HTMLResponse)
async def manage_tools_page(request: Request, server_name: str):
    """Tools management page for selected server"""
    try:
        # Validate server exists
        server = db_manager.get_server_by_name(server_name)
        if not server:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": f"Server '{server_name}' not found"
            })

        # Get server status and tools (extract data from JSONResponse)
        status_response = await get_server_status(server_name)
        status_data = json.loads(status_response.body.decode())
        status_json = status_data

        return templates.TemplateResponse("tools.html", {
            "request": request,
            "server_name": server_name,
            "server_info": status_json,
            "tools": status_json.get("tools", [])
        })

    except Exception as e:
        logger.error(f"Error loading tools management page: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Error loading tools management: {str(e)}"
        })

# Gemini AI Integration
@app.get("/api/gemini/status")
async def gemini_status():
    """Check Gemini API status"""
    gemini_api_key = os.getenv('GOOGLE_API_KEY')

    response_data = {
        "available": True,
        "api_key": gemini_api_key[:10] + "..." if len(gemini_api_key) > 10 else "configured"
    } if gemini_api_key else {
        "available": False,
        "error": "GOOGLE_API_KEY not configured"
    }

    # Add cache control headers
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    return JSONResponse(content=response_data, headers=headers)

@app.post("/api/gemini/chat")
async def gemini_chat(request: Dict[str, Any]):
    """Chat with Gemini AI"""
    try:
        message = request.get('message')
        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        # Import here to avoid issues if not installed
        import google.generativeai as genai

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content(message)

        response_data = {
            "response": response.text,
            "model": "gemini-2.5-flash",
            "status": "success"
        }

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except ImportError:
        raise HTTPException(status_code=500, detail="Google Generative AI not installed")
    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

@app.get("/api/gemini/models")
async def list_gemini_models():
    """List available Gemini models"""
    try:
        import google.generativeai as genai
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        genai.configure(api_key=api_key)

        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        response_data = {"models": models}

        # Add cache control headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

        return JSONResponse(content=response_data, headers=headers)

    except ImportError:
        raise HTTPException(status_code=500, detail="Google Generative AI not installed")
    except Exception as e:
        logger.error(f"Error listing Gemini models: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing Gemini models: {str(e)}")

if __name__ == "__main__":
    logger.info("🚀 Starting MCP Frontend API on port 3000")
    uvicorn.run(app, host="0.0.0.0", port=3000)