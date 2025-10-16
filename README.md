# MCP Multi-Server System

A multi-server system for the Model Context Protocol (MCP), featuring a unified frontend and two specialized backend servers for different toolsets.

## 🏗️ Architecture

The system consists of three main components:

-   **Frontend API (Port 3000):** A FastAPI application that serves the web interface for managing agents and tools, and acts as a gateway to the backend MCP servers.
-   **MCP Server A (Port 3001):** A FastAPI application that provides finance-related tools.
-   **MCP Server B (Port 3002):** A FastAPI application that provides general utility tools.
-   **PostgreSQL Database:** A central database for storing information about servers, tools, and agents.

## 🚀 Getting Started

### 1. Prerequisites

-   Python 3.8+
-   PostgreSQL

### 2. Installation

1.  Clone the repository.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

1.  Create a `.env` file in the root directory of the project.
2.  Add the following environment variables to the `.env` file, adjusting the values as needed:

    ```env
    # Database Configuration
    DATABASE_URL=postgresql://user:password@localhost/mcp_config

    # Server Ports
    PORT_A=3001
    PORT_B=3002
    ```

### 4. Running the System

You can run the entire system with a single command:

```bash
python app/main.py
```

This will start the Frontend API on port 3000, MCP Server A on port 3001, and MCP Server B on port 3002.

You can access the web interface by navigating to `http://localhost:3000` in your web browser.

Alternatively, you can run each server individually:

```bash
# Terminal 1: Start the Frontend API
uvicorn app.frontend_api:app --port 3000 --reload

# Terminal 2: Start MCP Server A
uvicorn app.server_a:app --port 3001 --reload

# Terminal 3: Start MCP Server B
uvicorn app.server_b:app --port 3002 --reload
```

## 🔗 API Endpoints

### Frontend API (Port 3000)

-   `/`: The main web interface for managing agents and tools.
-   `/servers`: Get a list of all available MCP servers.
-   `/agents`: Manage agents (create, list, update, delete).
-   `/manage-tools/{server_name}`: A web interface for managing the tools of a specific server.

### MCP Servers (Ports 3001 & 3002)

-   `/health`: Check the health of the server.
-   `/tools`: List all available tools on the server.
-   `/check-tools`: A simplified endpoint to check the available tools.
-   `/tools/call`: Execute a tool on the server.

#### Example: Check the tools on Server A

```bash
curl http://localhost:3001/check-tools
```

#### Example: Execute the `get_stock_price` tool on Server A

```bash
curl -X POST http://localhost:3001/tools/call \
  -H "Content-Type: application/json" \
  -d 
{
    "name": "get_stock_price",
    "arguments": {
      "symbol": "AAPL"
    }
  }
```

## 🛠️ Development

### Adding a New Tool

1.  Add the tool's logic to the appropriate server (`app/server_a.py` or `app/server_b.py`).
2.  Register the tool in the database using the web interface or by calling the `/tools` endpoint.

### Database

The database schema is defined by the SQLAlchemy models in `app/database.py`. The database is initialized with some default data when the system starts up.

## 📝 License

This project is licensed under the MIT License.
