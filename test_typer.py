import typer
app = typer.Typer()
@app.command()
def test(count: int = typer.Option(6)):
    print(count)
app()
