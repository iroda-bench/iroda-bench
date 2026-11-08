import json
from tempfile import mkdtemp

import pytest
from inspect_ai import eval
from inspect_ai.model import (
    ChatCompletionChoice,
    ChatMessageAssistant,
    ModelOutput,
    get_model,
)
from inspect_ai.tool import ToolCall

from iroda import SEED
from iroda_bench.runner import DATASET, make_task
from iroda_bench.scoring import load_tasks


@pytest.mark.parametrize(
    "mode", ["model", pytest.param("agent", marks=pytest.mark.docker)]
)
@pytest.mark.parametrize("case", load_tasks(DATASET), ids=lambda case: case.id)
def test_benchmark_roundtrip(tmp_path, monkeypatch, mode, case):
    monkeypatch.setattr(
        "iroda_bench.runner.mkdtemp", lambda **kwargs: mkdtemp(dir=tmp_path, **kwargs)
    )
    seed_bytes = SEED.read_bytes()
    called = []

    def respond(messages, tools, tool_choice, config):
        if messages[-1].role == "tool":
            assert expected_in_result in messages[-1].text
            called.append(tool_name)
            return ModelOutput.from_content("model", completion)
        name = next(tool.name for tool in tools if tool.name.endswith(tool_name))
        assert any(tool.name.endswith("feladat_letrehozas") for tool in tools) == (
            case.kind == "task_insert"
        )
        message = ChatMessageAssistant(
            content="",
            tool_calls=[ToolCall(id="call_1", function=name, arguments=args)],
        )
        return ModelOutput(
            model="model",
            choices=[ChatCompletionChoice(message=message, stop_reason="tool_calls")],
        )

    if case.kind == "answer":
        tool_name = "irodai_kornyezet"
        args = {}
        completion = json.dumps(case.expected)
        expected_in_result = case.expected["fordulonap"]
    else:
        tool_name = "feladat_letrehozas"
        args = case.expected.model_dump(exclude={"ajanlat_id"})
        args["ugy"] = {"tipus": "ajánlat", "azonosito": case.expected.ajanlat_id}
        completion = "Létrehoztam a feladatot."
        expected_in_result = "hatarido"

    model = get_model("mockllm/model", custom_outputs=respond, memoize=False)
    command = "python /app/example_agent.py" if mode == "agent" else None
    epochs = 2 if mode == "model" and case.kind == "task_insert" else 1
    log = eval(
        make_task(command),
        model=model,
        sample_id=case.id,
        epochs=epochs,
        max_samples=2,
        display="none",
        log_dir=str(tmp_path / "logs"),
        debug_errors=True,
    )[0]
    assert log.status == "success"
    assert called == [tool_name] * epochs
    assert [sample.scores["office_score"].value for sample in log.samples] == [
        "C"
    ] * epochs
    assert SEED.read_bytes() == seed_bytes
    assert not list(tmp_path.glob("iroda-*"))


def test_dataset_rejects_duplicate_ids(tmp_path):
    first = DATASET.read_text(encoding="utf-8").splitlines()[0]
    path = tmp_path / "tasks.jsonl"
    path.write_text(f"{first}\n{first}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unique IDs"):
        load_tasks(path)
