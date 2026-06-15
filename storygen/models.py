from typing import List, Optional
from pydantic import BaseModel, Field

class Chapter(BaseModel):
    number: int
    title: str
    text: str = ""

class Structure(BaseModel):
    name: str
    description: str

class Morale(BaseModel):
    name: str
    description: str = ""

class TimePeriod(BaseModel):
    name: str
    description: str = ""

class Protagonist(BaseModel):
    name: str
    voice: str
    type: str
    gender: str
    size: str
    age: str

class Villain(BaseModel):
    name: str
    description: str
    voice: str
    visual_look: str
    backstory: str

class Problem(BaseModel):
    chapter_number_int: int
    chapter_name: str
    issues_array_string: List[str]

class Villains(BaseModel):
    """Wrapper for list of Villains returned by structured output."""
    villains: List["Villain"]

class Problems(BaseModel):
    """Wrapper for list of Problems returned by structured output."""
    problems: List["Problem"]


class Suggestions(BaseModel):
    """Wrapper for list of Suggestions returned by structured output."""
    suggestions: List["Suggestion"]


class Protagonists(BaseModel):
    """Wrapper for list of Protagonists returned by structured output."""
    protagonists: List["Protagonist"]


class Suggestion(BaseModel):
    chapter_number_int: int
    chapter_name: str
    suggestions_array_string: List[str]

class Story(BaseModel):
    story_prompt: str = ""
    structure: Optional[Structure] = None
    time_period: Optional[TimePeriod] = None
    length: str = ""
    morales: List[Morale] = Field(default_factory=list)
    protagonists: List[Protagonist] = Field(default_factory=list)
    villain: Optional[Villain] = None
    plan: str = ""
    location: str = ""
    summary: str = ""
    chapters: List[Chapter] = Field(default_factory=list)
    title: str = ""

    def build_content(self, chapter_label: str = "Chapter", the_end: str = "The End.") -> str:
        content = []
        if self.title:
            content.extend([self.title.replace("*", "").replace("#", ""), "..."])
        
        for i, c in enumerate(self.chapters):
            title_clean = c.title.replace("*", "").replace("#", "").strip()
            
            # If the chapter title is exactly the story title (common in 1-chapter stories), don't repeat it
            if title_clean and title_clean.lower() != self.title.lower():
                header = f"{chapter_label} {c.number}.\n{title_clean}"
            else:
                header = f"{chapter_label} {c.number}."
                
            content.append(header)
            if c.text:
                content.append(c.text.replace("*", "").replace("#", "").strip())
            if i < len(self.chapters) - 1:
                content.append("...")
                
        content.extend(["...", the_end])
        return "\n\n".join(content)
