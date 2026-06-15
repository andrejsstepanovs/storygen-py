import json
import random
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

from storygen.config import settings
from storygen.models import Story, Protagonist, Villain, Problem, Suggestion, Structure, TimePeriod, Morale, Chapter, Protagonists, Problems, Suggestions, Villains
from storygen.utils import get_chapter_count_and_length, get_chapter_word_counts, remove_emojis, vprint
from storygen.prompts import (
    CHAPTER_PROMPT_INSTRUCTIONS, FORCE_JSON, GENERAL_INSTRUCTION,
    IDEAS_PROMPT, SUGGEST_FIXES_PROMPT, ADJUST_CHAPTER_PROMPT, FIGURE_LOGICAL_PROBLEMS_PROMPT,
    FIGURE_PROTAGONISTS_PROMPT, FIGURE_MORALES_PROMPT,
    FIGURE_VILLAIN_PROMPT, FIGURE_PLAN_PROMPT, FIGURE_TIME_PERIOD_PROMPT,
    FIGURE_CHAPTER_TITLES_PROMPT, FIGURE_SUMMARY_PROMPT, FIGURE_TITLE_PROMPT,
    FIGURE_CHAPTER_PROMPT, FIGURE_LOCATION_PROMPT, COMPARE_STORIES_PROMPT
)

llm = ChatOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    model=settings.model_name,
    temperature=0.7
)

def generate_ideas(count: int) -> List[str]:
    chain = IDEAS_PROMPT | llm | JsonOutputParser()
    return chain.invoke({
        "count": count,
        "audience": settings.audience,
        "general_instruction": GENERAL_INSTRUCTION,
        "force_json": FORCE_JSON
    })

def build_story(suggestion: str) -> Story:
    # 1. Base Setup
    chap_count, max_words, length_txt = get_chapter_count_and_length()
    vprint(f"[bold cyan]Story Length:[/bold cyan] {length_txt}")
    story = Story(story_prompt=suggestion.strip(), length=length_txt)

    available_time_periods = [{"name": "Once upon a time", "description": "Fairy-tale setting"}]
    available_morales = [{"name": "Kindness and Compassion", "description": "Treat others with care"}]
    story.structure = Structure(name="Three-Act Structure", description="Setup, Primary action, Resolution")

    # 2. Time Period
    tp_chain = FIGURE_TIME_PERIOD_PROMPT | llm | JsonOutputParser()
    tp_names = tp_chain.invoke({
        "audience": settings.audience,
        "story_json": story.model_dump_json(),
        "time_periods_json": json.dumps(available_time_periods),
        "general_instruction": GENERAL_INSTRUCTION,
        "force_json": FORCE_JSON,
        "example_json": '["Once upon a time"]'
    })
    if tp_names:
        random.shuffle(tp_names)
        story.time_period = TimePeriod(name=tp_names[0], description="")
    else:
        story.time_period = TimePeriod(**available_time_periods[0])
    vprint(f"[bold cyan]Selected Time Period:[/bold cyan] {story.time_period.name}")

    # 3. Morales
    m_chain = FIGURE_MORALES_PROMPT | llm | JsonOutputParser()
    morale_names = m_chain.invoke({
        "audience": settings.audience,
        "story_json": story.model_dump_json(),
        "morales_json": json.dumps(available_morales),
        "general_instruction": GENERAL_INSTRUCTION,
        "force_json": FORCE_JSON,
        "example_json": '["Kindness and Compassion"]'
    })
    if morale_names:
        random.shuffle(morale_names)
        morale_names = morale_names[:2]
    story.morales = [Morale(name=m, description="") for m in morale_names]
    vprint(f"[bold cyan]Selected Morales:[/bold cyan] {', '.join([m.name for m in story.morales])}")

    # 4. Protagonists
    p_chain_struct = FIGURE_PROTAGONISTS_PROMPT | llm.with_structured_output(Protagonists)
    p_chain_json = FIGURE_PROTAGONISTS_PROMPT | llm | JsonOutputParser()
    try:
        try:
            result = p_chain_struct.invoke({
                "audience": settings.audience,
                "story_json": story.model_dump_json(),
                "general_instruction": GENERAL_INSTRUCTION,
                "force_json": FORCE_JSON,
                "example_json": '[{"name": "Max", "voice": "Squeaky, energetic, and slightly breathless young boy", "type": "human", "gender": "male", "size": "small", "age": "child"}]'
            })
            protagonists_list = result.protagonists if result else []
        except Exception as struct_e:
            vprint(f"[bold yellow]Structured output failed for protagonists: {struct_e}. Falling back to JsonOutputParser.[/bold yellow]")
            result = p_chain_json.invoke({
                "audience": settings.audience,
                "story_json": story.model_dump_json(),
                "general_instruction": GENERAL_INSTRUCTION,
                "force_json": FORCE_JSON,
                "example_json": '[{"name": "Max", "voice": "Squeaky, energetic, and slightly breathless young boy", "type": "human", "gender": "male", "size": "small", "age": "child"}]'
            })
            protagonists_list = [Protagonist(**p) for p in result] if result and isinstance(result, list) else []

        if protagonists_list:
            random.shuffle(protagonists_list)
            num_protagonists = random.randint(1, min(2, len(protagonists_list)))
            story.protagonists = protagonists_list[:num_protagonists]
        else:
            story.protagonists = []
        for p in story.protagonists:
            vprint(f"[bold cyan]Protagonist:[/bold cyan] {p.name} ({p.type}, {p.gender}, {p.age}, voice: {p.voice})")
    except Exception as e:
        vprint(f"[bold red]Failed to generate protagonists:[/bold red] {e}")
        story.protagonists = []

    # 5. Villain
    v_chain_struct = FIGURE_VILLAIN_PROMPT | llm.with_structured_output(Villains)
    v_chain_json = FIGURE_VILLAIN_PROMPT | llm | JsonOutputParser()
    try:
        try:
            result = v_chain_struct.invoke({
                "audience": settings.audience,
                "story_json": story.model_dump_json(),
                "general_instruction": GENERAL_INSTRUCTION,
                "force_json": FORCE_JSON,
                "example_json": '{"villains": [{"name": "Captain Hookbeak", "description": "A pterosaur pirate captain", "voice": "A screechy, gravelly voice", "visual_look": "Wears a tiny pirate hat", "backstory": "Lost his treasure"}]}'
            })
            villains_list = result.villains if result else []
        except Exception as struct_e:
            vprint(f"[bold yellow]Structured output failed for villains: {struct_e}. Falling back to JsonOutputParser.[/bold yellow]")
            result = v_chain_json.invoke({
                "audience": settings.audience,
                "story_json": story.model_dump_json(),
                "general_instruction": GENERAL_INSTRUCTION,
                "force_json": FORCE_JSON,
                "example_json": '{"villains": [{"name": "Captain Hookbeak", "description": "A pterosaur pirate captain", "voice": "A screechy, gravelly voice", "visual_look": "Wears a tiny pirate hat", "backstory": "Lost his treasure"}]}'
            })
            v_list_raw = result.get("villains", []) if isinstance(result, dict) else result
            villains_list = [Villain(**v) for v in v_list_raw] if isinstance(v_list_raw, list) else []

        if villains_list:
            random.shuffle(villains_list)
            story.villain = villains_list[0]
        if story.villain:
            vprint(f"[bold cyan]Villain:[/bold cyan] {story.villain.name} - {story.villain.description} (voice: {story.villain.voice})")
    except Exception as e:
        vprint(f"[bold red]Failed to generate villain:[/bold red] {e}")
        story.villain = None

    # 6. Location & Plan & Summary
    loc_chain = FIGURE_LOCATION_PROMPT | llm | JsonOutputParser()
    try:
        locations = loc_chain.invoke({
            "audience": settings.audience,
            "story_json": story.model_dump_json(),
            "general_instruction": GENERAL_INSTRUCTION,
            "force_json": FORCE_JSON
        })
        if locations and isinstance(locations, list):
            random.shuffle(locations)
            story.location = remove_emojis(locations[0])
        else:
            story.location = "A mysterious place"
    except Exception as e:
        vprint(f"[bold red]Failed to generate location:[/bold red] {e}")
        story.location = "A mysterious place"

    plan_chain = FIGURE_PLAN_PROMPT | llm
    story.plan = remove_emojis(plan_chain.invoke({
        "audience": settings.audience,
        "story_json": story.model_dump_json(),
        "general_instruction": GENERAL_INSTRUCTION
    }).content.strip())

    sum_chain = FIGURE_SUMMARY_PROMPT | llm
    story.summary = remove_emojis(sum_chain.invoke({
        "audience": settings.audience,
        "story_json": story.model_dump_json(),
        "general_instruction": GENERAL_INSTRUCTION
    }).content.strip())
    vprint(f"[bold cyan]Location:[/bold cyan] {story.location}")
    vprint(f"[bold cyan]Plan:[/bold cyan] {story.plan}")
    vprint(f"[bold cyan]Summary:[/bold cyan] {story.summary}")

    # 7. Chapters Titles
    ct_chain = FIGURE_CHAPTER_TITLES_PROMPT | llm | JsonOutputParser()
    chapter_titles = ct_chain.invoke({
        "audience": settings.audience,
        "story_json": story.model_dump_json(),
        "chapter_count": chap_count,
        "general_instruction": GENERAL_INSTRUCTION,
        "force_json": FORCE_JSON
    })

    word_counts = get_chapter_word_counts(chap_count, max_words)
    
    for i, title in enumerate(chapter_titles, 1):
        target_words = word_counts.get(i, max_words)
        vprint(f"[bold cyan]Chapter {i} (target: ~{target_words} words):[/bold cyan] {title}")
        story.chapters.append(Chapter(number=i, title=title, text=""))

    # 8. Chapters Text
    ch_chain = FIGURE_CHAPTER_PROMPT | llm | JsonOutputParser()

    for chapter in story.chapters:
        vprint(f"[bold yellow]Writing Chapter {chapter.number}...[/bold yellow]")
        is_last = chapter.number == len(story.chapters)
        chapter_intent = (
            "to finish the story with satisfying ending. This is the last chapter of the story so make sure that you end open story topics and end them with good conclusions." 
            if is_last else "to proceed the storyline."
        )
        
        try:
            variations = ch_chain.invoke({
                "audience": settings.audience,
                "story_json": story.model_dump_json(),
                "chapter_number": chapter.number,
                "chapter_title": chapter.title,
                "chapter_intent": chapter_intent,
                "word_count": word_counts[chapter.number],
                "general_instruction": GENERAL_INSTRUCTION,
                "chapter_prompt_instructions": CHAPTER_PROMPT_INSTRUCTIONS,
                "force_json": FORCE_JSON
            })
            if variations and isinstance(variations, list):
                random.shuffle(variations)
                text = variations[0]
            else:
                text = str(variations)
        except Exception as e:
            vprint(f"[bold red]Failed to generate chapter {chapter.number} text:[/bold red] {e}")
            text = "An error occurred while generating this chapter."
        
        chapter.text = remove_emojis(text.strip())

    # 9. Story Title
    title_chain = FIGURE_TITLE_PROMPT | llm | JsonOutputParser()
    try:
        titles = title_chain.invoke({
            "audience": settings.audience,
            "story_json": story.model_dump_json(),
            "general_instruction": GENERAL_INSTRUCTION,
            "force_json": FORCE_JSON
        })
        if titles and isinstance(titles, list):
            random.shuffle(titles)
            story.title = remove_emojis(titles[0].strip().strip('"'))
        else:
            story.title = "A New Adventure"
    except Exception as e:
        vprint(f"[bold red]Failed to generate story title:[/bold red] {e}")
        story.title = "A New Adventure"

    return story

def refine_story(story: Story) -> Story:
    if settings.preread_loops == 0:
        return story

    prob_chain_struct = FIGURE_LOGICAL_PROBLEMS_PROMPT | llm.with_structured_output(Problems)
    prob_chain_json = FIGURE_LOGICAL_PROBLEMS_PROMPT | llm | JsonOutputParser()
    sug_chain = SUGGEST_FIXES_PROMPT | llm | JsonOutputParser()
    adj_chain = ADJUST_CHAPTER_PROMPT | llm

    chap_count, max_words, _ = get_chapter_count_and_length()
    word_counts = get_chapter_word_counts(chap_count, max_words)

    all_addressed_suggestions = []

    for loop in range(1, settings.preread_loops + 1):
        content = story.build_content()
        try:
            try:
                result = prob_chain_struct.invoke({
                    "audience": settings.audience,
                    "story_text": content,
                    "story_json": story.model_dump_json(),
                    "loop": loop,
                    "max_loops": settings.preread_loops,
                    "general_instruction": GENERAL_INSTRUCTION,
                    "force_json": FORCE_JSON,
                    "example_json": '[{"chapter_number_int": 1, "chapter_name": "Title", "issues_array_string": ["Issue 1"]}]'
                })
                problems = result.problems if result else []
            except Exception as struct_e:
                vprint(f"[bold yellow]Structured output failed for logical problems: {struct_e}. Falling back to JsonOutputParser.[/bold yellow]")
                result = prob_chain_json.invoke({
                    "audience": settings.audience,
                    "story_text": content,
                    "story_json": story.model_dump_json(),
                    "loop": loop,
                    "max_loops": settings.preread_loops,
                    "general_instruction": GENERAL_INSTRUCTION,
                    "force_json": FORCE_JSON,
                    "example_json": '[{"chapter_number_int": 1, "chapter_name": "Title", "issues_array_string": ["Issue 1"]}]'
                })
                problems = [Problem(**p) for p in result] if result and isinstance(result, list) else []
        except Exception as e:
            vprint(f"[bold red]Failed to identify problems in loop {loop}:[/bold red] {e}")
            break
        
        if not problems:
            vprint(f"[bold magenta]Loop {loop}: No problems found, finishing refinement.[/bold magenta]")
            break

        all_suggestions = []
        chapter_suggestions = {}

        for problem in problems:
            vprint(f"[bold magenta]Loop {loop}: Finding fixes for {problem.chapter_name}...[/bold magenta]")
            if problem.chapter_number_int > len(story.chapters):
                continue

            trimmed_story = story.model_copy(deep=True)
            trimmed_story.chapters = trimmed_story.chapters[:problem.chapter_number_int]

            try:
                raw_sugs = sug_chain.invoke({
                    "audience": settings.audience,
                    "chapter_number": problem.chapter_number_int,
                    "chapter_name": problem.chapter_name,
                    "problem_json": problem.model_dump_json(),
                    "story_json": trimmed_story.model_dump_json(),
                    "addressed_suggestions_json": json.dumps([s.model_dump() for s in all_addressed_suggestions])
                })
                suggestions = [Suggestion(**s) for s in raw_sugs]
            except Exception as e:
                vprint(f"[bold red]Failed to generate suggestions for chapter {problem.chapter_number_int}:[/bold red] {e}")
                continue
            
            if not suggestions:
                continue

            all_suggestions.extend(suggestions)
            for sug in suggestions:
                chapter_suggestions.setdefault(sug.chapter_number_int, []).append(sug)

        for chapter_idx in sorted(chapter_suggestions.keys()):
            vprint(f"[bold magenta]Loop {loop}: Applying fixes for Chapter {chapter_idx}...[/bold magenta]")
            for problem in problems:
                if problem.chapter_number_int != chapter_idx:
                    continue

                for j, ch in enumerate(story.chapters):
                    if ch.number != chapter_idx:
                        continue
                    
                    trimmed_story = story.model_copy(deep=True)
                    trimmed_story.chapters = trimmed_story.chapters[:chapter_idx]

                    fixed_text = adj_chain.invoke({
                        "audience": settings.audience,
                        "chapter_number": chapter_idx,
                        "chapter_name": problem.chapter_name,
                        "addressed_suggestions_json": json.dumps([s.model_dump() for s in all_addressed_suggestions]),
                        "suggestions_json": json.dumps([s.model_dump() for s in chapter_suggestions[chapter_idx]]),
                        "story_json": trimmed_story.model_dump_json(),
                        "word_count": word_counts.get(chapter_idx, max_words),
                        "general_instruction": GENERAL_INSTRUCTION,
                        "chapter_prompt_instructions": CHAPTER_PROMPT_INSTRUCTIONS
                    }).content

                    story.chapters[j].text = remove_emojis(fixed_text.strip())

        all_addressed_suggestions.extend(all_suggestions)

    return story

def compare_stories(story_a: Story, story_b: Story) -> Story:
    chain = COMPARE_STORIES_PROMPT | llm
    result = chain.invoke({
        "audience": settings.audience,
        "story_a_json": story_a.model_dump_json(),
        "story_b_json": story_b.model_dump_json(),
        "general_instruction": GENERAL_INSTRUCTION
    }).content.strip()

    try:
        if int(result) == 1:
            return story_a
    except ValueError:
        pass
    return story_b
