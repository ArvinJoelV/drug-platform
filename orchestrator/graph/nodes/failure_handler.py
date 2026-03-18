import functools
from orchestrator.utils.logger import logger

def safe_node(node_name: str):
    """
    Decorator to wrap LangGraph nodes securely.
    Ensures that unexpected exceptions do not crash the entire graph execution.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(state, *args, **kwargs):
            try:
                return await func(state, *args, **kwargs)
            except Exception as e:
                logger.error(f"Unexpected global failure in {node_name}: {str(e)}")
                return {
                    f"{node_name}_data": None, 
                    "errors": {node_name: f"Unhandled Exception: {str(e)}"}, 
                    "status": {node_name: "crash_recovered"}
                }
        return wrapper
    return decorator
