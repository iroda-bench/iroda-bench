"""Run the same cases through a fixed loop or an isolated external agent."""

import hashlib
import shlex
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp

from inspect_ai import Task
from inspect_ai.agent import AgentState, BridgedToolsSpec, sandbox_agent_bridge
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem, ModelOutput
from inspect_ai.scorer import CORRECT, INCORRECT, Score, accuracy, scorer
from inspect_ai.solver import solver
from inspect_ai.tool import mcp_server_stdio
from inspect_ai.util import sandbox

from iroda import SEED
from iroda_bench.scoring import AnswerTask, InsertTask, load_tasks, score

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "iroda_bench" / "tasks.jsonl"
SYSTEM_PROMPT = "Az IRODA eszközeivel oldd meg a feladatot. Magyarul válaszolj."


@solver
def copy_database():
    async def setup(state, generate):
        directory = Path(mkdtemp(prefix="iroda-"))
        state.store.set("database", str(directory / "run.db"))
        shutil.copyfile(SEED, directory / "run.db")
        return state

    return setup


async def cleanup_database(state):
    database = state.store.get("database")
    if database is not None:
        shutil.rmtree(Path(database).parent)


@solver
def run_agent(cases: dict[str, AnswerTask | InsertTask], command: str | None):
    argv = shlex.split(command) if command is not None else None
    if argv == []:
        raise ValueError("Agent command must contain an executable.")

    async def solve(state, generate):
        args = [str(ROOT / "mcp_server.py"), "--adatbazis", state.store.get("database")]
        if isinstance(cases[state.sample_id], InsertTask):
            args.append("--irhato")

        async with mcp_server_stdio(
            name="iroda", command=sys.executable, args=args
        ) as office:
            tools = await office.tools()
            if argv is None:
                state.messages.insert(0, ChatMessageSystem(content=SYSTEM_PROMPT))
                state.tools = tools
                return await generate(
                    state, tool_calls="loop", parallel_tool_calls=False
                )

            agent_state = AgentState(messages=list(state.messages))
            async with sandbox_agent_bridge(
                agent_state,
                bridged_tools=[
                    BridgedToolsSpec(name="iroda", tools=tools, require_proposal=False)
                ],
            ) as bridge:
                result = await sandbox().exec(
                    argv,
                    input=cases[state.sample_id].prompt,
                    env={
                        "IRODA_MCP_CONFIG": bridge.mcp_server_configs[
                            0
                        ].model_dump_json(exclude_none=True),
                        "OPENAI_BASE_URL": f"http://127.0.0.1:{bridge.port}/v1",
                        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{bridge.port}",
                        "GOOGLE_GEMINI_BASE_URL": f"http://127.0.0.1:{bridge.port}/v1beta",
                        "IRODA_MODEL": "inspect",
                    },
                    timeout=110,
                    timeout_retry=False,
                )
                if not result.success:
                    raise RuntimeError(
                        f"Agent command failed ({result.returncode}): {result.stderr[-2000:]}"
                    )
                state.messages = list(bridge.state.messages)
                state.output = ModelOutput.from_content(
                    str(state.model), result.stdout.strip()
                )
                state.messages.append(state.output.message)
                return state

    return solve


@scorer(metrics=[accuracy()])
def office_score(cases: dict[str, AnswerTask | InsertTask]):
    async def evaluate(state, target):
        passed, detail = score(
            cases[state.sample_id],
            state.output.completion,
            SEED,
            Path(state.store.get("database")),
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=detail)

    return evaluate


def make_task(command: str | None = None) -> Task:
    cases = {case.id: case for case in load_tasks(DATASET)}
    return Task(
        dataset=[
            Sample(id=case.id, input=case.prompt, metadata={"kind": case.kind})
            for case in cases.values()
        ],
        setup=copy_database(),
        solver=run_agent(cases, command),
        scorer=office_score(cases),
        cleanup=cleanup_database,
        sandbox=("docker", str(ROOT / "environment" / "compose.yaml"))
        if command is not None
        else None,
        metadata={
            "seed_sha256": hashlib.sha256(SEED.read_bytes()).hexdigest(),
            "tasks_sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(),
        },
        time_limit=120,
        turn_limit=20,
        version="0.1.0",
    )
