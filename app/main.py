import asyncio
import logging
import os
import sys
import time
from multiprocessing import Process
from dotenv import load_dotenv

load_dotenv()

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import db_manager
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_server_a():
    """Run Server A"""
    os.environ['SERVER_NAME'] = 'server_a'
    import server_a
    port = int(os.getenv('PORT_A', 3001))
    logger.info(f"🚀 Starting MCP Server A on port {port}")
    uvicorn.run(server_a.app, host="0.0.0.0", port=port)

def run_server_b():
    """Run Server B"""
    os.environ['SERVER_NAME'] = 'server_b'
    import server_b
    port = int(os.getenv('PORT_B', 3002))
    logger.info(f"🚀 Starting MCP Server B on port {port}")
    uvicorn.run(server_b.app, host="0.0.0.0", port=port)

def run_frontend_api():
    """Run Frontend API"""
    # Add current directory to Python path for imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    import frontend_api
    logger.info("🚀 Starting MCP Frontend API on port 3000")
    uvicorn.run(frontend_api.app, host="0.0.0.0", port=3000)

def initialize_database():
    """Initialize database with default tools if needed"""
    logger.info("🔧 Initializing database...")

    # Test connection
    if not db_manager.test_connection():
        logger.error("❌ Cannot connect to database")
        return False

    logger.info("✅ Database connected successfully")

    # Check existing servers and tools
    try:
        # Check Server A (finance-server)
        server_a = db_manager.get_server_by_name('server_a')
        if server_a:
            tools_count = db_manager.get_server_tools_count(server_a['id'])
            logger.info(f"📊 Server A found: {server_a['name']} with {tools_count} tools")

            if tools_count > 0:
                tools = db_manager.get_tools_by_server(server_a['id'])
                logger.info(f"🔧 Server A tools: {[tool['name'] for tool in tools]}")
        else:
            logger.warning("⚠️ Server A not found in database")

        # Check Server B (weather-server)
        server_b = db_manager.get_server_by_name('server_b')
        if server_b:
            tools_count = db_manager.get_server_tools_count(server_b['id'])
            logger.info(f"📊 Server B found: {server_b['name']} with {tools_count} tools")

            if tools_count > 0:
                tools = db_manager.get_tools_by_server(server_b['id'])
                logger.info(f"🔧 Server B tools: {[tool['name'] for tool in tools]}")
        else:
            logger.warning("⚠️ Server B not found in database")

        logger.info("✅ Database initialization completed")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main function to run both servers"""
    logger.info("🎯 Starting MCP Multi-Server System")

    # Initialize database
    if not initialize_database():
        logger.error("❌ Failed to initialize database. Exiting...")
        sys.exit(1)

    # Run servers in parallel processes
    try:
        logger.info("🚀 Starting both MCP servers...")

        # Create processes for all servers
        process_a = Process(target=run_server_a)
        process_b = Process(target=run_server_b)
        process_frontend = Process(target=run_frontend_api)

        # Start all servers
        process_a.start()
        process_b.start()
        process_frontend.start()

        logger.info("✅ All servers started successfully!")
        logger.info("📊 Server A: http://localhost:3001")
        logger.info("📊 Server B: http://localhost:3002")
        logger.info("🌐 Frontend API: http://localhost:3000")
        logger.info("🏥 Health check A: http://localhost:3001/health")
        logger.info("🏥 Health check B: http://localhost:3002/health")
        logger.info("📋 Frontend API: http://localhost:3000/servers")

        # Wait for all processes
        process_a.join()
        process_b.join()
        process_frontend.join()

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down servers...")
        process_a.terminate()
        process_b.terminate()
        process_frontend.terminate()
        process_a.join()
        process_b.join()
        process_frontend.join()
        logger.info("✅ All servers shut down successfully")

    except Exception as e:
        logger.error(f"❌ Error running servers: {e}")
        process_a.terminate()
        process_b.terminate()
        process_frontend.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()