import json
import itertools
import os
from typing import List
from langchain_core.output_parsers import JsonOutputParser
from storygen.chains import llm, GENERAL_INSTRUCTION, FORCE_JSON
from storygen.prompts import GENERATE_TOPICS_PROMPT, PAIRWISE_RATING_PROMPT
from storygen.models import Story
from storygen.config import settings
from rich import print as vprint

def generate_rating_topics() -> List[str]:
    vprint("[bold yellow]Generating evaluation topics...[/bold yellow]")
    chain = GENERATE_TOPICS_PROMPT | llm | JsonOutputParser()
    try:
        topics = chain.invoke({
            "audience": settings.audience,
            "general_instruction": GENERAL_INSTRUCTION,
            "force_json": FORCE_JSON
        })
        if isinstance(topics, list):
            return topics
    except Exception as e:
        vprint(f"[bold red]Failed to generate topics: {e}[/bold red]")
    
    return ["Storyline consistency", "Engagement and pacing", "Creative characters"]

def evaluate_stories(stories: List[Story]) -> Story:
    if len(stories) == 1:
        return stories[0]

    topics = generate_rating_topics()
    vprint(f"[bold cyan]Using topics for evaluation:[/bold cyan] {', '.join(topics)}")

    # Initialize scores
    scores = {id(s): 0 for s in stories}
    
    chain = PAIRWISE_RATING_PROMPT | llm | JsonOutputParser()

    # Pairwise comparison
    for s1, s2 in itertools.combinations(stories, 2):
        vprint(f"Comparing [bold cyan]{s1.title}[/bold cyan] vs [bold cyan]{s2.title}[/bold cyan]...")
        try:
            result = chain.invoke({
                "audience": settings.audience,
                "topics_json": json.dumps(topics),
                "story_1_json": s1.model_dump_json(),
                "story_2_json": s2.model_dump_json(),
                "general_instruction": GENERAL_INSTRUCTION,
                "force_json": FORCE_JSON
            })
            
            s1_scores = result.get("story_1_scores", {})
            s2_scores = result.get("story_2_scores", {})
            
            s1_total = sum(s1_scores.values()) if isinstance(s1_scores, dict) else 0
            s2_total = sum(s2_scores.values()) if isinstance(s2_scores, dict) else 0
            
            scores[id(s1)] += s1_total
            scores[id(s2)] += s2_total
            vprint(f"  Match Result: {s1.title} ({s1_total} pts) vs {s2.title} ({s2_total} pts)")
            
        except Exception as e:
            vprint(f"[bold red]Failed to evaluate pair:[/bold red] {e}")

    # Find winner
    winner = max(stories, key=lambda s: scores[id(s)])
    
    vprint("\n[bold green]--- FINAL SCORES ---[/bold green]")
    for s in stories:
        vprint(f"{s.title}: {scores[id(s)]} pts")
    
    vprint(f"\n[bold magenta]🏆 WINNER: {winner.title} 🏆[/bold magenta]")
    return winner
