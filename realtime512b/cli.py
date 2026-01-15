"""CLI entry point for realtime512b"""

import click

from .init.run_init import run_init
from .start.run_start import run_start


@click.group()
@click.version_option(version="0.1.0")
def main():
    """realtime512b - Real-time processing of multi-electrode neural data."""
    pass


@main.command()
def init():
    """Initialize a new experiment directory."""
    run_init()


@main.command()
def start():
    """Start real-time processing of multi-electrode data."""
    run_start()


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", default=5000, help="Port to bind to (default: 5000)")
def serve(host, port):
    """Serve raw and computed data via HTTP API."""
    from .serve.run_serve import run_serve
    run_serve(host=host, port=port)


if __name__ == "__main__":
    main()
