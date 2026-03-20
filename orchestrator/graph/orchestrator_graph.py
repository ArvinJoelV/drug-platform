from langgraph.graph import StateGraph, START, END

from orchestrator.graph.state import OrchestratorState
from orchestrator.graph.nodes.pre_agentic_node import pre_agentic_node
from orchestrator.graph.nodes.input_node import input_node
from orchestrator.graph.nodes.clinical_node import clinical_node
from orchestrator.graph.nodes.patent_node import patent_node
from orchestrator.graph.nodes.regulatory_node import regulatory_node
from orchestrator.graph.nodes.market_node import market_node
from orchestrator.graph.nodes.literature_node import literature_node
from orchestrator.graph.nodes.aggregator_node import aggregator_node
from orchestrator.graph.nodes.intelligence_node import intelligence_node
from orchestrator.graph.nodes.contradiction_layer_node import contradiction_layer_node
from orchestrator.graph.nodes.regulatory_postcheck_node import regulatory_postcheck_node
from orchestrator.graph.nodes.llm_report_node import llm_report_node
from orchestrator.graph.nodes.finalizer_node import finalizer_node

def build_graph():
    builder = StateGraph(OrchestratorState)
    
    # 1. Define nodes
    builder.add_node("pre_agentic", pre_agentic_node)
    builder.add_node("input", input_node)
    builder.add_node("clinical", clinical_node)
    builder.add_node("patent", patent_node)
    builder.add_node("regulatory", regulatory_node)
    builder.add_node("market", market_node)
    builder.add_node("literature", literature_node)
    builder.add_node("aggregator", aggregator_node)
    builder.add_node("intelligence", intelligence_node)
    builder.add_node("contradiction_layer", contradiction_layer_node)
    builder.add_node("regulatory_postcheck", regulatory_postcheck_node)
    builder.add_node("llm_report", llm_report_node)
    builder.add_node("finalizer", finalizer_node)
    
    # 2. Define edges and topology
    
    # Start -> Pre-agentic -> Input
    builder.add_edge(START, "pre_agentic")
    builder.add_edge("pre_agentic", "input")
    
    # Flow out into Layer 1 parallel nodes
    builder.add_edge("input", "clinical")
    builder.add_edge("input", "patent")
    builder.add_edge("input", "regulatory")
    builder.add_edge("input", "market")
    
    # Layer 2 Dependency (clinical -> literature)
    builder.add_edge("clinical", "literature")
    
    # Sync barrier: Wait for layer 1 independent + layer 2 literature to finish
    # LangGraph automatically joins state on these edges
    builder.add_edge("patent", "aggregator")
    builder.add_edge("regulatory", "aggregator")
    builder.add_edge("market", "aggregator")
    builder.add_edge("literature", "aggregator")
    
    builder.add_edge("aggregator", "intelligence")
    builder.add_edge("intelligence", "contradiction_layer")
    builder.add_edge("contradiction_layer", "regulatory_postcheck")
    builder.add_edge("regulatory_postcheck", "llm_report")
    builder.add_edge("llm_report", "finalizer")
    
    # Final Output
    builder.add_edge("finalizer", END)
    
    return builder.compile()

# Instantiated graph module
graph = build_graph()
