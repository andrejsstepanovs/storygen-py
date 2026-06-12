import typer
from storygen.chains import generate_ideas, build_story, refine_story
from storygen.tts import compile_audiobook
from storygen.utils import save_json, load_json, sanitize_filename
from storygen.config import settings, VoiceName
from storygen.models import Story

app = typer.Typer(help="Children Story Generator")
story_app = typer.Typer()
app.add_typer(story_app, name="story")

@story_app.callback()
def story_callback(
    target_dir: str = typer.Option(None, help=f"Target directory for mp3 (default: {settings.target_dir})"),
    tmp_dir: str = typer.Option(None, help=f"Temporary directory (default: {settings.tmp_dir})"),
    language: str = typer.Option(None, help=f"Story language (default: {settings.language})"),
    readspeed: int = typer.Option(None, help=f"Read speed in words per minute (default: {settings.readspeed})"),
    audience: str = typer.Option(None, help=f"Target audience (default: {settings.audience})"),
    length_in_min: int = typer.Option(None, help=f"Story length in minutes (default: {settings.length_in_min})"),
    chapters: int = typer.Option(None, help=f"Number of chapters (default: {settings.chapters})"),
    preread_loops: int = typer.Option(None, help=f"Number of pre-read loops for grooming (default: {settings.preread_loops})"),
    voice: VoiceName = typer.Option(None, help=f"Default TTS voice (default: {settings.voice.value})"),
    voice_male: VoiceName = typer.Option(None, help=f"Male TTS voice (default: {settings.voice_male.value})"),
    voice_female: VoiceName = typer.Option(None, help=f"Female TTS voice (default: {settings.voice_female.value})"),
    speech_speed: float = typer.Option(None, help=f"Speech speed multiplier (default: {settings.speech_speed})"),
    debug: bool = typer.Option(False, "--debug", help=f"Enable debug mode (default: {settings.debug})"),
    verbose: bool = typer.Option(False, "--verbose", help=f"Enable verbose mode (default: {settings.verbose})"),
):
    """Global configuration for story generation."""
    if target_dir is not None: settings.target_dir = target_dir
    if tmp_dir is not None: settings.tmp_dir = tmp_dir
    if language is not None: settings.language = language
    if readspeed is not None: settings.readspeed = readspeed
    if audience is not None: settings.audience = audience
    if length_in_min is not None: settings.length_in_min = length_in_min
    if chapters is not None: settings.chapters = chapters
    if preread_loops is not None: settings.preread_loops = preread_loops
    if voice is not None: settings.voice = voice
    if voice_male is not None: settings.voice_male = voice_male
    if voice_female is not None: settings.voice_female = voice_female
    if speech_speed is not None: settings.speech_speed = speech_speed
    if debug: settings.debug = True
    if verbose: settings.verbose = True

@story_app.command("voices")
def list_voices():
    """List all available TTS voices and their descriptions."""
    from rich.table import Table
    from rich.console import Console
    
    table = Table(title="Available Gemini TTS Voices")
    table.add_column("Voice Name", style="cyan", no_wrap=True)
    table.add_column("Gender", style="magenta")
    table.add_column("Description", style="green")
    
    table.add_row("Puck", "Male", "Young and energetic")
    table.add_row("Kore", "Female", "Bright and clear")
    table.add_row("Aoede", "Female", "Warm and authoritative")
    table.add_row("Charon", "Male", "Deep and authoritative")
    table.add_row("Fenrir", "Male", "Gritty and deep")
    table.add_row("Leda", "Female", "Soft and gentle")
    
    console = Console()
    console.print(table)

@story_app.command("ideas")
def ideas(count: int = typer.Option(6, help="Provide list of ideas for stories")):
    """Provide list of ideas for stories"""
    result = generate_ideas(count)
    typer.echo(f"Ideas: {len(result)}")
    for idea in result:
        typer.echo(idea)

@story_app.command("create")
def create(suggestion: str):
    """Creates a Story from a suggestion string"""
    typer.echo("Starting to work on a new story...")
    story = build_story(suggestion)
    save_json(story, story.title)
    typer.echo("JSON saved.")

    typer.echo("Refining story...")
    story = refine_story(story)
    filepath = save_json(story, f"final_groomed_{story.title}")
    
    typer.echo("Generating Text to Speech...")
    compile_audiobook(story, sanitize_filename(story.title))
    typer.echo(f"Success!\nStory: {story.title}\njson: {filepath}")

@story_app.command("write")
def write(suggestion: str):
    """Writes a Story with no text to voice"""
    typer.echo("Starting to work on a new story...")
    story = build_story(suggestion)
    filepath = save_json(story, story.title)
    typer.echo(f"JSON saved at {filepath}")

@story_app.command("read")
def read(file: str):
    """Load a Story from JSON and output story text"""
    story = load_json(file, Story)
    typer.echo(story.build_content())

@story_app.command("groom")
def groom(file: str):
    """Groom the Story from JSON and fix found issues"""
    story = load_json(file, Story)
    story = refine_story(story)
    filepath = save_json(story, f"groomed_{story.title}")
    typer.echo(f"Done. Saved to {filepath}")

@story_app.command("voice")
def voice(file: str):
    """Generate audio from an existing JSON file"""
    story = load_json(file, Story)
    compile_audiobook(story, sanitize_filename(story.title))
    typer.echo("Audio generation complete.")

if __name__ == "__main__":
    app()
