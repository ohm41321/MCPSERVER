import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from urllib.parse import urlparse, unquote

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env
    pass

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection_params = self._parse_database_url()

    def _parse_database_url(self) -> dict:
        """Parse DATABASE_URL and return connection parameters"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Parse the URL
        parsed = urlparse(database_url)

        # Decode URL-encoded components
        username = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        hostname = parsed.hostname
        port = parsed.port
        database = parsed.path.lstrip('/') if parsed.path else None

        return {
            'host': hostname,
            'port': port,
            'user': username,
            'password': password,
            'database': database
        }

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def get_server_by_name(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get server information by name"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if server_name == 'server_a':
                        # Look for finance server
                        cursor.execute(
                            'SELECT * FROM mcp_servers WHERE name LIKE %s OR id = %s',
                            ['%finance%', 'finance-server-001']
                        )
                    else:
                        # Look for weather/general server
                        cursor.execute(
                            'SELECT * FROM mcp_servers WHERE name LIKE %s OR id = %s',
                            ['%MCP Server 2%', 'f2f47d1f-3fcd-4cee-b560-2a89f510a6f2']
                        )

                    result = cursor.fetchone()
                    if result:
                        return {
                            'id': result['id'],
                            'name': result['name'],
                            'url': result['url'],
                            'status': result['status'],
                            'enabled': result['enabled'],
                            'server_name': server_name,
                            'port': 3001 if server_name == 'server_a' else 3002,
                            'is_active': result['enabled']
                        }
        except Exception as e:
            logger.error(f"Error getting server {server_name}: {e}")
        return None

    def get_server_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get server information by URL"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM mcp_servers WHERE url = %s', [url])
                    result = cursor.fetchone()
                    return result
        except Exception as e:
            logger.error(f"Error getting server by url {url}: {e}")
        return None

    def create_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new server"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        '''INSERT INTO mcp_servers (id, name, url, status, enabled)
                           VALUES (%s, %s, %s, %s, %s) RETURNING *''',
                        [
                            server_data['id'],
                            server_data['name'],
                            server_data['url'],
                            server_data['status'],
                            server_data['enabled']
                        ]
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    return row
        except Exception as e:
            logger.error(f"Error creating server: {e}")
            raise

    def get_all_servers(self) -> List[Dict[str, Any]]:
        """Get all servers"""
        servers = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM mcp_servers ORDER BY name')
                    results = cursor.fetchall()

                    logger.info(f"Found {len(results)} servers in database")

                    for result in results:
                        logger.info(f"Processing server: {result['name']} (ID: {result['id']})")

                        # Map existing servers to our naming convention
                        if 'finance' in result['name'].lower() or result['id'] == 'finance-server-001':
                            server_name = 'server_a'
                            port = 3001
                        elif 'test' in result['name'].lower() or result['id'] == '3d24c70b-7e99-4bb2-8c18-54caa48e5c6e':
                            server_name = 'server_b'
                            port = 3002
                        else:
                            # For unknown servers, assign as server_b or create generic mapping
                            server_name = 'server_b'
                            port = 3002

                        servers.append({
                            'id': result['id'],
                            'name': result['name'],
                            'url': result['url'],
                            'status': result['status'],
                            'enabled': result['enabled'],
                            'server_name': server_name,
                            'port': port,
                            'is_active': result['enabled']
                        })

                    logger.info(f"Returning {len(servers)} mapped servers")
        except Exception as e:
            logger.error(f"Error getting all servers: {e}")
        return servers

    def get_tools_by_server(self, server_id: str) -> List[Dict[str, Any]]:
        """Get all tools for a specific server"""
        logger.info(f"Fetching tools for server_id: {server_id}")
        tools = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM tools WHERE server_id = %s ORDER BY name', [server_id])
                    results = cursor.fetchall()
                    logger.info(f"Found {len(results)} tools for server_id: {server_id}")

                    for row in results:
                        parameters = []
                        if row['parameters']:
                            if isinstance(row['parameters'], str):
                                try:
                                    parameters = json.loads(row['parameters'])
                                except json.JSONDecodeError:
                                    parameters = [] # Or handle error appropriately
                            elif isinstance(row['parameters'], list):
                                parameters = row['parameters']

                        tools.append({
                            'id': row['id'],
                            'name': row['name'],
                            'description': row['description'],
                            'parameters': parameters,
                            'server_id': row['server_id'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                            'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                            'api_url': row['api_url'],
                            'http_method': row['http_method'],
                            'request_headers': row['request_headers'],
                            'request_body': row['request_body']
                        })
        except Exception as e:
            logger.error(f"Error getting tools for server {server_id}: {e}")
        return tools

    def get_active_tools_by_server(self, server_id: str) -> List[Dict[str, Any]]:
        """Get active tools for a specific server"""
        # Since existing table doesn't have status, return all tools
        return self.get_tools_by_server(server_id)

    def get_tool_by_name(self, server_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool by name"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        'SELECT * FROM tools WHERE server_id = %s AND name = %s',
                        [server_id, tool_name]
                    )
                    row = cursor.fetchone()

                    if row:
                        # Parse parameters - handle both string and already parsed JSON
                        parameters = []
                        if row['parameters']:
                            try:
                                # Try to parse as JSON string first
                                if isinstance(row['parameters'], str):
                                    param_data = json.loads(row['parameters'])
                                    if isinstance(param_data, list):
                                        parameters = param_data
                                    else:
                                        parameters = [param_data]
                                else:
                                    # Already parsed
                                    parameters = row['parameters'] if isinstance(row['parameters'], list) else []
                            except:
                                # If parsing fails, treat as simple string
                                parameters = [{"name": "input", "type": "string", "description": "Input parameter", "required": true}]
                        else:
                            parameters = []

                        return {
                            'id': row['id'],
                            'name': row['name'],
                            'description': row['description'],
                            'parameters': parameters,
                            'server_id': row['server_id'],
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                            'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                            'api_url': row['api_url'],
                            'http_method': row['http_method'],
                            'request_headers': row['request_headers'],
                            'request_body': row['request_body']
                        }
        except Exception as e:
            logger.error(f"Error getting tool {tool_name}: {e}")
        return None

    def register_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new tool"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        '''INSERT INTO tools (id, name, description, parameters, server_id, api_url, http_method)
                           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *''',
                        [
                            tool_data['id'],
                            tool_data['name'],
                            tool_data['description'],
                            json.dumps(tool_data['parameters']),
                            tool_data['server_id'],
                            tool_data['api_url'],
                            tool_data['http_method']
                        ]
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    return row
        except Exception as e:
            logger.error(f"Error registering tool: {e}")
            raise

    def get_server_tools_count(self, server_id: str) -> int:
        """Get count of tools for a server"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT COUNT(*) as count FROM tools WHERE server_id = %s', [server_id])
                    result = cursor.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting tools count for server {server_id}: {e}")
            return 0

    def add_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new tool to the tools table"""
        return self.register_tool(tool_data)

    def update_tool(self, tool_id: str, tool_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing tool"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        '''UPDATE tools SET name = %s, description = %s, parameters = %s, api_url = %s, http_method = %s
                           WHERE id = %s RETURNING *''',
                        [
                            tool_data['name'],
                            tool_data['description'],
                            json.dumps(tool_data['parameters']),
                            tool_data['api_url'],
                            tool_data['http_method'],
                            tool_id
                        ]
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    return row
        except Exception as e:
            logger.error(f"Error updating tool {tool_id}: {e}")
            return None

    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('DELETE FROM tools WHERE id = %s', [tool_id])
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting tool {tool_id}: {e}")
            return False

    def log_tool_execution(self, tool_id: str, server_id: str, params: Dict[str, Any],
                          result: Dict[str, Any], status: str, execution_time_ms: int):
        """Log tool execution (simplified for existing structure)"""
        logger.info(f"[{datetime.now().isoformat()}] Tool {tool_id} execution: {status} ({execution_time_ms}ms)")

    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        '''INSERT INTO agents (name, description)
                           VALUES (%s, %s) RETURNING *''',
                        [
                            agent_data['name'],
                            agent_data['description']
                        ]
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    return row
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            raise

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM agents ORDER BY name')
                    results = cursor.fetchall()
                    return results
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            return []

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information by id"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM agents WHERE id = %s', [agent_id])
                    result = cursor.fetchone()
                    return result
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
        return None

    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing agent"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        '''UPDATE agents SET name = %s, description = %s, updated_at = CURRENT_TIMESTAMP
                           WHERE id = %s RETURNING *''',
                        [
                            agent_data['name'],
                            agent_data['description'],
                            agent_id
                        ]
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    return row
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            return None

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('DELETE FROM agents WHERE id = %s', [agent_id])
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting agent {agent_id}: {e}")
            return False

    def add_server_to_agent(self, agent_id: str, server_id: str) -> bool:
        """Add a server to an agent"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        '''INSERT INTO agent_mcp_servers (agent_id, server_id)
                           VALUES (%s, %s)''',
                        [agent_id, server_id]
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding server {server_id} to agent {agent_id}: {e}")
            return False

    def remove_server_from_agent(self, agent_id: str, server_id: str) -> bool:
        """Remove a server from an agent"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        '''DELETE FROM agent_mcp_servers
                           WHERE agent_id = %s AND server_id = %s''',
                        [agent_id, server_id]
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing server {server_id} from agent {agent_id}: {e}")
            return False

    def get_servers_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all servers for a specific agent"""
        servers = []
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(
                        '''SELECT s.* FROM mcp_servers s
                           JOIN agent_mcp_servers ams ON s.id = ams.server_id
                           WHERE ams.agent_id = %s''',
                        [agent_id]
                    )
                    results = cursor.fetchall()

                    for result in results:
                        if 'finance' in result['name'].lower() or result['id'] == 'finance-server-001':
                            server_name = 'server_a'
                            port = 3001
                        elif 'test' in result['name'].lower() or result['id'] == '3d24c70b-7e99-4bb2-8c18-54caa48e5c6e':
                            server_name = 'server_b'
                            port = 3002
                        else:
                            server_name = 'server_b'
                            port = 3002

                        servers.append({
                            'id': result['id'],
                            'name': result['name'],
                            'url': result['url'],
                            'status': result['status'],
                            'enabled': result['enabled'],
                            'server_name': server_name,
                            'port': port,
                            'is_active': result['enabled']
                        })
        except Exception as e:
            logger.error(f"Error getting servers for agent {agent_id}: {e}")
        return servers

# Global database manager instance
db_manager = DatabaseManager()