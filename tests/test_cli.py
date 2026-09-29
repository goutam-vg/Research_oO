import sys
from types import SimpleNamespace as NS

from research_agent import cli


def test_read_topics_from_args_and_file(tmp_path):
    topics_file = tmp_path / "topics.txt"
    topics_file.write_text("# my list\n\nBlack holes\n  Roman Empire  \n", encoding="utf-8")
    args = cli.build_parser().parse_args(["Quantum", "computing", "--file", str(topics_file)])
    assert cli.read_topics(args) == ["Quantum computing", "Black holes", "Roman Empire"]


def test_parser_defaults():
    args = cli.build_parser().parse_args(["x"])
    assert (args.length, args.lang, args.format, args.output_dir) == ("medium", "English", "txt", "outputs")


def test_main_saves_a_file(monkeypatch, tmp_path):
    import research_agent.agent as agent

    def fake_stream(topic, model, length, lang):
        yield {"type": "status", "text": "Searching Wikipedia"}
        yield {"type": "token", "text": "Hi [1]"}
        yield {"type": "done", "summary": "Hi [1]", "sources": [{"title": "T", "url": "https://t.example"}]}

    monkeypatch.setattr(agent, "research_stream", fake_stream)
    monkeypatch.setattr(cli, "check_ollama", lambda model: None)

    code = cli.main(["Cats", "--format", "md", "-o", str(tmp_path)])
    assert code == 0
    saved = list(tmp_path.glob("*.md"))
    assert len(saved) == 1
    assert "[T](https://t.example)" in saved[0].read_text(encoding="utf-8")


def test_main_stops_when_ollama_is_down(monkeypatch):
    monkeypatch.setattr(cli, "check_ollama", lambda model: "Cannot reach Ollama")
    assert cli.main(["Cats"]) == 1
