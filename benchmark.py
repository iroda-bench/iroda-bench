"""Inspect CLI entry points for the two IRODA benchmark modes."""

from inspect_ai import task

from iroda_bench.runner import make_task


@task
def model_benchmark():
    """Compare models using the same tool-calling loop."""
    return make_task()


@task
def agent_benchmark(command: str = "python /app/example_agent.py"):
    """Evaluate a complete agent command inside a Docker sandbox."""
    return make_task(command=command)
