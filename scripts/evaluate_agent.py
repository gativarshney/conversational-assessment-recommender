import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.core.logging import setup_logging
from app.retriever import CatalogRetriever
from app.agent import RecommendationAgent
from app.schemas.chat import Message

logger = logging.getLogger("evaluate_agent")

def parse_trace_file(filepath: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Parses a markdown conversation trace file.
    Returns:
      - list of user prompt strings
      - list of expected recommendations (each with 'name' and 'url')
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Extract User prompts by parsing Turn blocks
    turns = content.split("### Turn ")
    user_prompts = []
    
    # Simple regex to capture text inside quote blocks
    quote_regex = re.compile(r'^>\s*(.*)$', re.MULTILINE)
    
    for turn in turns[1:]:  # Skip header before Turn 1
        user_section_match = re.search(r'\*\*User\*\*([\s\S]*?)(?:\*\*Agent\*\*|$)', turn)
        if user_section_match:
            user_text = user_section_match.group(1)
            quotes = quote_regex.findall(user_text)
            if quotes:
                # Join multi-line quote prompts
                prompt = " ".join([q.strip() for q in quotes if q.strip()])
                user_prompts.append(prompt)

    # 2. Extract expected recommendations from the last markdown table in the file
    # Row format: | 1 | Assessment Name | Test Type | Keys | Duration | Languages | URL |
    row_regex = re.compile(r'^\s*\|\s*\d+\s*\|\s*([^|]+)\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|\s*[^|]+\|\s*([^|]+)\|')
    expected_recs = []
    
    # Scan from the bottom to find the last table rows
    lines = content.splitlines()
    for line in reversed(lines):
        match = row_regex.match(line)
        if match:
            name = match.group(1).strip()
            url_cell = match.group(2).strip()
            
            # Extract URL from link syntax e.g. <url> or [text](url)
            url = url_cell
            url_match = re.search(r'<(http[^>]+)>|\[[^\]]+\]\((http[^\)]+)\)', url_cell)
            if url_match:
                url = url_match.group(1) or url_match.group(2)
                
            expected_recs.append({"name": name, "url": url})
            
    # Since we scanned from the bottom, reverse to preserve original rank order
    expected_recs.reverse()
    return user_prompts, expected_recs

def calculate_recall(expected: List[Dict[str, str]], recommended: List[Dict[str, Any]], k: int = 10) -> float:
    """Computes Recall@K comparing expected shortlist items to recommended ones."""
    if not expected:
        return 1.0 if not recommended else 0.0
        
    expected_urls = {item["url"].lower().strip("/") for item in expected}
    recommended_urls = {item["url"].lower().strip("/") for item in recommended[:k]}
    
    matches = expected_urls.intersection(recommended_urls)
    return len(matches) / len(expected_urls)

def run_evaluation() -> None:
    setup_logging()
    
    traces_dir = r"C:\Users\gativ\.gemini\antigravity-ide\scratch\sample_conversations\GenAI_SampleConversations"
    
    if not os.path.exists(traces_dir):
        logger.error(f"Sample conversation traces directory not found at: {traces_dir}")
        return
        
    logger.info("Initializing vector DB retriever and agent...")
    retriever = CatalogRetriever(db_path=settings.VECTOR_DB_DIR)
    agent = RecommendationAgent(retriever=retriever)
    
    logger.info("Starting automated trace replay simulation...")
    trace_files = [f for f in os.listdir(traces_dir) if f.endswith(".md")]
    # Sort files numerically (C1, C2, C3, ... C10)
    trace_files.sort(key=lambda x: int(re.search(r'\d+', x).group()))
    
    total_recall = 0.0
    results_summary = []
    
    for filename in trace_files:
        filepath = os.path.join(traces_dir, filename)
        user_prompts, expected_recs = parse_trace_file(filepath)
        
        logger.info(f"\nReplaying trace '{filename}' ({len(user_prompts)} turns)...")
        logger.info(f"Expected Shortlist count: {len(expected_recs)}")
        
        # Simulate stateless multi-turn conversation
        conversation_history: List[Message] = []
        final_recs = []
        turn_count = 0
        schema_compliant = True
        turn_cap_honored = True
        
        for turn_idx, prompt in enumerate(user_prompts):
            turn_count += 1
            if turn_count > 8:
                turn_cap_honored = False
                
            conversation_history.append(Message(role="user", content=prompt))
            
            # Send message history (stateless)
            response = agent.process_conversation(conversation_history)
            
            # Schema checks
            if not isinstance(response.get("reply", ""), str) or not isinstance(response.get("recommendations", []), list):
                schema_compliant = False
                
            # Append assistant reply to history for subsequent turns
            conversation_history.append(Message(role="assistant", content=response.get("reply", "")))
            
            # Capture recommendations if provided
            if response.get("recommendations"):
                final_recs = response["recommendations"]
                
        # Calculate Recall@10
        recall_val = calculate_recall(expected_recs, final_recs, k=10)
        total_recall += recall_val
        
        logger.info(f"Trace {filename} completed. Final recommendations: {len(final_recs)} items. Recall@10: {recall_val:.2%}")
        
        results_summary.append({
            "trace": filename,
            "turns": turn_count,
            "expected_count": len(expected_recs),
            "rec_count": len(final_recs),
            "recall": recall_val,
            "schema_ok": schema_compliant,
            "turn_cap_ok": turn_cap_honored
        })
        
    # Run custom behavior probes
    logger.info("\n=== RUNNING BEHAVIOR PROBES ===")
    
    # Probe 1: Off-topic refusal probe
    off_topic_history = [Message(role="user", content="Can you write a template job offer letter for a Java dev?")]
    probe_response1 = agent.process_conversation(off_topic_history)
    probe1_ok = len(probe_response1.get("recommendations", [])) == 0 and not probe_response1.get("end_of_conversation", False)
    logger.info(f"Behavior Probe 1 (Off-topic refusal) passed: {probe1_ok}")
    
    # Probe 2: Turn-1 vague query clarification probe
    vague_history = [Message(role="user", content="I need an assessment for my hiring team.")]
    probe_response2 = agent.process_conversation(vague_history)
    probe2_ok = len(probe_response2.get("recommendations", [])) == 0 and not probe_response2.get("end_of_conversation", False)
    logger.info(f"Behavior Probe 2 (Turn-1 vague query clarification) passed: {probe2_ok}")
    
    mean_recall = total_recall / len(trace_files)
    
    # Output Markdown summary table
    print("\n\n=== EVALUATION REPORT SUMMARY ===")
    print("| Trace | Turns | Expected Items | Rec Items | Recall@10 | Schema OK | Turn Cap OK |")
    print("|-------|-------|----------------|-----------|-----------|-----------|-------------|")
    for r in results_summary:
        print(f"| {r['trace']:<5} | {r['turns']:<5} | {r['expected_count']:<14} | {r['rec_count']:<9} | {r['recall']:<9.1%} | {r['schema_ok']:<9} | {r['turn_cap_ok']:<11} |")
        
    print(f"\nMean Recall@10: {mean_recall:.2%}")
    print(f"Off-topic Refusal Probe: {'PASS' if probe1_ok else 'FAIL'}")
    print(f"Vague Clarification Probe: {'PASS' if probe2_ok else 'FAIL'}")

if __name__ == "__main__":
    run_evaluation()
