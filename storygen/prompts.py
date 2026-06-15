from langchain_core.prompts import ChatPromptTemplate

CHAPTER_PROMPT_INSTRUCTIONS = """# Content writing instructions:
- Analyze previous chapters (if exists) before writing the next one.
- If story is for children then use shorter sentences, simple language and avoid complex words.
- If story is for children then write with respect for young readers. Include proper story development, meaningful plot progression, and clever twists.
- Avoid talking down or using overly childish language.
- Dont be cringe, skip overly childish and safe content.
- Avoid sugar-coating and predictable storylines.
- Proceed the storyline in a way that fits the chapter's place in the story.
- Use all provided story details (characters, setting, plot, morals, etc.) to create a rich, imaginative, and engaging chapter.
- Ensure the chapter aligns with the story's structure, timeline, themes, protagonist, villain, and overall plan.
- Take into consideration Story Suggestion.
- Write it using funny interactions between characters.
- Move plot forward without diving into surrounding details.
- Use Time-Related Transitions:
-- Instead of 'and then,' try:
-- After that
-- Meanwhile
-- Later
-- Shortly afterward
-- Moments later
-- Subsequently
-- In the meantime
- Use Cause-and-Effect Connections:
-- As a result
-- Consequently
-- Therefore
-- This led to
-- Because of this
- Replace with Action Verbs:
-- Instead of: 'She opened the door and then walked inside'
-- Try: 'She opened the door, stepping cautiously inside'
- Use Subordinate Clauses:
-- Instead of: 'He finished his homework and then he went to play'
-- Try: 'After finishing his homework, he went to play'
- Introduce Simultaneous Actions
-- Instead of: 'She heard the noise and then she turned around'
-- Try: 'Hearing the noise, she turned around'
- Connect Settings to Characters: make locations matter to your characters
- Be Specific About Location, Time and Weather
- Use minimal amount of adjectives.
- Restrain yourself from using cliché things like 'Whispering Woods', 'misty meadow', etc.
- Always place speaker name before quoting what they say. 
-- Example: Max said "That's amazing!" NOT "That's amazing!" Max said.
-- Example: Johnny insisted "I don't believe you" NOT "I don't believe you," Johnny insisted.
- Tell what happened and what happened next moving plot forward.

# Writing style Adjustments:
You often use descriptive phrases or clauses to extend sentences. While they add great imagery, they can feel repetitive if overused. Try mixing it up with shorter, punchier sentences or different ways of describing actions and settings! It'll help keep the pacing fresh and engaging!Another thing - laughing and dancing is nice but too much is cringe."""

FORCE_JSON = "No yapping. Answer **only with raw JSON**. Dont wrap json with tags or quotes or anything else. Answer only with RAW JSON."
GENERAL_INSTRUCTION = ""

SUGGEST_FIXES_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a story editor suggesting fixes for story chapters to resolve issues. Your suggestions will be used to re-write chapters later. Return ONLY raw JSON without any markdown formatting or code blocks."),
    ("user", """Analyze chapter {chapter_number} ({chapter_name}) of this {audience} story and suggest fixes for the following issues:

**Issues to fix:**
{problem_json}

**Story context (chapters 1-{chapter_number}):**
```json
{story_json}

```

**Already addressed suggestions (ignore these):**

```json
{addressed_suggestions_json}

```

**Instructions:**

1. Suggest specific, actionable changes to fix the issues
2. Identify which chapter(s) need changes (current or earlier chapters)
3. Keep suggestions practical - minimal text changes preferred
4. Focus on major plot holes and inconsistencies, not minor details
5. Maximum 5 suggestions total (or return empty array if no fixes needed)
6. Do not suggest creating new chapters
7. Maintain the existing {audience} story writing style

**CRITICAL: Response format requirements:**

* Return ONLY a JSON array, nothing else
* Do NOT wrap the JSON in markdown code blocks (no `json or `)
* Do NOT add any explanatory text before or after the JSON
* Start your response with [ and end with ]
* Each object in the array must have: chapter_number_int (integer), chapter_name (string), suggestions_array_string (array of strings)
* Return empty array [] if no important fixes are needed

Example valid response: [{{"chapter_number_int": 1, "chapter_name": "Title", "suggestions_array_string": ["Fix X", "Change Y"]}}]""")
])

ADJUST_CHAPTER_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are story writer that is fixing story issues before it goes to publishing."),
("user", """Re-write the {audience} Story chapter {chapter_number} {chapter_name}. Analyze full {audience} Story and adjust the problematic chapter {chapter_number} {chapter_name}.
Here are all already addressed suggestions:
<already_addressed_suggestions>
{addressed_suggestions_json}
</already_addressed_suggestions>
**IMPORTANT**: Suggestions how to fix the issues at hand:
<fix_suggestions>
{suggestions_json}
</fix_suggestions>
Use and rely only on these suggestions provided!
For reference, here is full story until this chapter ```json
{story_json}

```.
# Orders:
- There are maybe more chapters but lets focus on story until this moment.
- Fix only this chapter so story is coherent, entertaining and makes sense (use given suggestions). 
- Use suggestions from fix_suggestions tag to re-write the story chapter {chapter_number} {chapter_name} as suggested. 
- Make sure you don't break out of suggestions that were fixed before (see json in: already_addressed_suggestions tags). 
- Answer with only one chapter text. Do NOT include the chapter number or chapter title in your output. Start the text directly with the story narrative. We are fixing it one chapter at the time. 
- Be creative to fix the issue at hand. Be swift and decisive. No need for long texts, we just need to fix these issues and move on. 
- Small text extensions are OK, but we should try to keep this chapter withing a limit of {word_count} words. 
{general_instruction} {chapter_prompt_instructions}""")
])

FIGURE_LOGICAL_PROBLEMS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are helping to pre-read a story and your output will help us to fix the story flaws."),
    ("user", """Create a JSON problem list for {audience} story we need to check (pre-read):
<story_text>
{story_text}
</story_text>

**This is the original story setup and plan**:
```json
{story_json}
```

Find problems and flaws in the plot and answer with formatted output as mentioned in examples.
Carefully read the story text chapter by chapter and analyze it for logical flaws in the story in each chapter. Also ensure that the story accurately follows the original plan, characters, and other details provided in the JSON.
This is cycle {loop} of pre-reading. Reduce strictness and issue count proportionally to the number of cycles completed. Max cycles: {max_loops}.

{general_instruction} {force_json}
If no flaws are found, do not include the chapter in your output. Example format: {example_json}""")
])

FIGURE_PROTAGONISTS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are helping to prepare a story ideas that will be used later on."),
    ("user", """Create a JSON protagonists list that will fit the {audience} story we will write. Story:
```json
{story_json}

```

Please generate 3 to 6 protagonists. We will randomly select from this list to keep things fresh.
Pick good simple but memorable protagonist names.
Be creative with your picks. We want a vibrant, exciting story and protagonists are/is important and needs to be suitable and interesting.
For the `voice` property, DO NOT use vague terms like "medium", "high", or "low". Be highly descriptive, specific, and creative! Examples of good voices: "Deep grumpy and sad old male voice", "Overly excited and jumpy female kid voice", "Raspy and mysterious whisper".
Don't specify protagonists sexual orientations, that type of info is mostly irrelevant in {audience} stories.
{general_instruction} {force_json}
Example format: {example_json}""")
])

FIGURE_MORALES_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story ideas that will be used later on."),
("user", """Create a list of morale names that will fit the {audience} story we will write. Story:

```json
{story_json}

```

Pick 4 to 6 morales (`name`) from list of available morales:

```json
{morales_json}

```

Be flexible with your picks. We want creative choices for exciting story. The more the better.
{general_instruction} {force_json}
No yapping. Answer with a list of morale names as strings (as simple array list with no key(s)) in JSON format.
Example: {example_json}""")
])

IDEAS_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story ideas that will be used later on."),
("user", """Create a list of {count} story ideas that will fit the {audience}
Be creative and funny.
{general_instruction} {force_json}
No yapping. Answer with a list of story ideas as strings (as simple array list with no key(s)) in JSON format.""")
])

FIGURE_VILLAIN_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story book. Villain that you are building (writing) will be used later on when story itself will be written."),
("user", """Create a JSON Villains object containing 3 different villains for this {audience} story:

```json
{story_json}

```

Create 3 distinct villains that fit the story. Think about their name, description, voice, visual_look, and backstory. Try to be creative and find a villain that is more down to earth (but still evil, bad, annoying, etc.) with his/her own backstory, skills and agenda that we can work with in the story.
Villain can also be elements of nature or unmovable objects and that kind of stuff. Depends on the story we're building. Be creative if possible.
For the `voice` property, DO NOT use vague terms like "medium", "high", or "low". Be highly descriptive, specific, and creative! Examples of good voices: "Deep grumpy and sad old male voice", "Overly excited and jumpy female kid voice", "Raspy and mysterious whisper".

{general_instruction} {force_json}
Example: {example_json}""")
])

FIGURE_PLAN_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story book."),
("user", """Create and {audience} story plan about the story. **This is the Story you need to work with**:

```json
{story_json}

```

Follow main ideas that are already prepared for the story. Be careful building story plan in a way that existing story you are working with (from json above) fits good. Make sure you work with Story structure that was picked. We want our plan to align with picked story structure. Keep in mind story length. Take into consideration Story Suggestion. Same goes for picked story morales. Summary and plan should match picked story morales. Story plan should be quite brief and short list of things that will happen in the story with no specifics. Details will be written later on. Write the plan in a way that the writer later on will not be much constrained with. We want to keep story plan loose and flexible (no details). Be creative and make sure that this {audience} story is moving forward fast so it is engaging and fun to read. Plan a story in a way where there are no boring parts and plot is moving forward fast. Don't forget to include ending to the story you're planning so there is satisfying conclusions is built into the story properly. Consider adding some plot twists and funny interactions between characters.
{general_instruction}
Story summary and story plan to help the writer later on when they will write the story. No yapping. Don't explain your choice or add any other notes and explenations.""")
])

FIGURE_TIME_PERIOD_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story ideas that will be used later on."),
("user", """Create a list of 3 different time periods that will fit the {audience} story we will write. Story:

```json
{story_json}

```

Pick 3 time periods (`name`) from list of available time periods:

```json
{time_periods_json}

```

Be flexible with your picks. We want a vibrant, exciting story and time period is important and needs to be suitable and interesting. {general_instruction} {force_json}
Example: {example_json}""")
])

FIGURE_CHAPTER_TITLES_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story content chapter titles."),
("user", """Create a list of story chapter titles that will be used for this {audience} story:

```json
{story_json}

```

Make sure that chapter titles align with existing story details. Take into consideration Story Suggestion. Make sure that story have a clear ending. Be mindful about the chapter count so it aligns good with story length. Usually there is no need for more than {chapter_count} chapters. Write chapter titles in a way that the plot is naturally moving forward and is aligned with defined {audience} story structure requirements.
{general_instruction} {force_json} Make sure your answer starts with [ and list of json array values.
Example: ["The Mysterious Map", "The Magic Paintbrush", "The Rainbow Bridge", "The Final Battle", "The Return to Home Sweet Home"]""")
])

FIGURE_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are summarizing a story book."),
("user", """Create 1 sentence story summary for this story. **This is the {audience} story you need to work with**:

```json
{story_json}

```

If exists, take into consideration Story Suggestion.
{general_instruction}
Answer only with the summary. No yapping. No other explanations, comments, notes or anything else. Answer only with the story summary text (content).""")
])

FIGURE_TITLE_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are writing a story book title."),
("user", """Write 3 book names (titles) for this {audience} story. **This is the {audience} Story you need to work with**:

```json
{story_json}

```

Titles must be 3-5 words long. Do not explain your choices, no explanation, notes or anything else is necessary.
{general_instruction} {force_json}
Examples: ["The Secret Library of Wishes", "The Brave Little Firefly", "The girl and the Talking Tree"]
Answer only with a JSON array of 3 short titles (3-5 words each).""")
])

FIGURE_CHAPTER_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are writing a story book chapter by chapter. Expand the story with one chapter. You are creative and decisive story writer."),
("user", """Write 3 variations of the single full chapter text, ensuring it flows naturally and keeps the reader engaged. **This is the {audience} story you need to work with**:

```json
{story_json}

```

You need to write a chapter: "{chapter_number}) - {chapter_title}" content (text) {chapter_intent} Make sure to strictly follow the story `plan` from the JSON and cover the events intended for this chapter. Chapter should be written (should fit within) with approximately {word_count} words.
Take your time to think about well-crafted chapter variations that fit the plot, enhance the narrative, and make logical sense.
{general_instruction} {force_json}
{chapter_prompt_instructions}
Answer only with a JSON array containing 3 strings, where each string is a full variation of the chapter content. Do NOT include the chapter number or chapter title in your output strings. Start the text directly with the story narrative. No yapping. No other explanations or unrelated text is necessary.""")
])

FIGURE_LOCATION_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to prepare a story book. Story location that you are building (writing) will be used later on when story itself will be written."),
("user", """Create a list of 3 different locations where the story could take place. **This is the {audience} Story you need to work with**:

```json
{story_json}

```

Be creative while creating this story world. Do not mention protagonist or villain. Take into consideration Story Suggestion. Keep the world within time period that the story is taking place in. Keep the world size in line with story length. We will not be able to cram huge world into 2 minute story. Same applies other way around, we should have big enough world for longer stories. Specific details are good. Where who lives and other places around the protagonist(s) and villain are important as there most often the action (story) will happen. Dont be afraid to expand the world with more locations if you see that will benefit the upcoming story. Make the world so it is easy to imagine for {audience}. If writing for children then make interesting but not excessively complicated, so that little readers have no problem understanding it.
{general_instruction} {force_json}
Answer only with a JSON array of 3 strings (locations). No yapping. No other explanations or unrelated to title text is necessary. Dont explain yourself.
Example: ["Location 1 description", "Location 2 description", "Location 3 description"]""")
])

COMPARE_STORIES_PROMPT = ChatPromptTemplate.from_messages([
("system", "You are helping to compare 2 story books."),
("user", """Analyze these 2 {audience} stories and answer with number which story is better.
**Story Nr. 1**:

```json
{story_a_json}

```

**Story Nr. 2**:

```json
{story_b_json}

```

Compare these 2 stories and answer with number which story is better. This is really important task, be careful. Your answer matters a lot! Best story author will get $ 1000000 cash prize.
Consider story plot, engagement and how fun it would be to read. Analyze also story plot logical issues. If one story plot is logically broken (do not make sense), then that is really bad. Answer with single word that is a number in INTEGER format. Do not explain why you picked one over the other. If story 1 is better then answer with 1, if story 2 is better then answer with 2.
{general_instruction}""")
])

GENERATE_TOPICS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert story critic."),
    ("user", """Generate 3 to 5 rating topics (criteria) to evaluate a {audience} story.
    
Think about what we value most in a good story. Align that with world's best stories in this genre. For example, if it is a children's story, compare how Disney or Brother Grimm they are, along with storyline and consistency.
Return ONLY a JSON array of strings, where each string is a rating topic.
{general_instruction} {force_json}
Example: ["Disney-like magic and wonder", "Storyline consistency", "Engagement and pacing", "Creative characters"]""")
])

PAIRWISE_RATING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert story critic comparing two stories."),
    ("user", """You will be given two {audience} stories. Rate both stories from 1 to 5 on the provided rating topics.

**Rating Topics:**
{topics_json}

**Story 1:**
```json
{story_1_json}
```

**Story 2:**
```json
{story_2_json}
```

Evaluate both stories carefully. Return ONLY a JSON object with this exact structure:
{{
  "story_1_scores": {{ "topic name": score, ... }},
  "story_2_scores": {{ "topic name": score, ... }}
}}
{general_instruction} {force_json}""")
])
