"""Command line interface: research-agent "your topic" """

import argparse
import sys
import threading
import time
from pathlib import Path

from research_agent import __version__
from research_agent.config import FORMAT_CHOICES, LENGTH_CHOICES, get_model_name
from research_agent.health import check_ollama
from research_agent.storage import format_references, format_summary, save_summary


class Spinner:
    """Tiny ASCII spinner on stderr, shown while the agent searches."""

    FRAMES = "|/-\\"

    def __init__(self):
        self.label = ""
        self._running = False
        self._thread = None

    def _spin(self):
        i = 0
        while self._running:
            sys.stderr.write(f"\r{self.FRAMES[i % 4]} {self.label}...   ")
            sys.stderr.flush()
            i += 1
            time.sleep(0.1)

    def start(self, label: str):
        self.label = label
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()

    def stop(self):
        if self._running:
            self._running = False
            self._thread.join()
            sys.stderr.write("\r" + " " * 60 + "\r")
            sys.stderr.flush()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research-agent",
        description="Summarize any topic with references, using a local Ollama model.",
        epilog=(
            'examples:\n  research-agent "Quantum computing"\n'
            '  research-agent "Black holes" --length long --format md\n'
            '  research-agent --file topics.txt --lang Spanish'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("topic", nargs="*", help="topic to research")
    parser.add_argument("-f", "--file", help="text file with one topic per line (# for comments)")
    parser.add_argument("-m", "--model", help="Ollama model (default: OLLAMA_MODEL or qwen3:8b)")
    parser.add_argument("-l", "--length", choices=LENGTH_CHOICES, default="medium")
    parser.add_argument("--lang", default="English", help="language of the summary")
    parser.add_argument("--format", choices=FORMAT_CHOICES, default="txt", help="output file format")
    parser.add_argument("-o", "--output-dir", default="outputs", help="where to save files")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def read_topics(args) -> list[str]:
    topics = []
    inline = " ".join(args.topic).strip()
    if inline:
        topics.append(inline)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                topics.append(line)
    return topics


def _warm_up_in_background(model: str) -> None:
    def work():
        from research_agent.agent import warm_up

        warm_up(model)

    threading.Thread(target=work, daemon=True).start()


def run_topic(topic: str, model: str, args) -> bool:
    from research_agent.agent import research_stream  # imported late: keeps --help fast

    print(f"Researching '{topic}' with {model} ({args.length})\n")
    spinner = Spinner()
    spinner.start("Starting")
    summary, sources, typed = "", [], False
    try:
        for event in research_stream(topic, model, args.length, args.lang):
            kind = event["type"]
            if kind == "status":
                spinner.label = event["text"]
            elif kind == "token":
                spinner.stop()  # answer is streaming: show it as it is typed
                print(event["text"], end="", flush=True)
                typed = True
            elif kind == "done":
                summary, sources = event["summary"], event["sources"]
    except Exception as error:
        spinner.stop()
        print(f"\nError: {error}", file=sys.stderr)
        return False
    finally:
        spinner.stop()

    if not typed:
        print(summary)
    print(f"\n\n{format_references(sources)}")
    text = format_summary(topic, summary, model, sources, args.format)
    path = save_summary(topic, text, args.output_dir, args.format)
    print(f"\nSaved to: {path}\n")
    return True


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = build_parser().parse_args(argv)
    model = get_model_name(args.model)

    try:
        topics = read_topics(args)
    except OSError as error:
        print(f"Cannot read topics file: {error}", file=sys.stderr)
        return 2

    problem = check_ollama(model)
    if problem:
        print(f"Error: {problem}", file=sys.stderr)
        return 1

    if not topics:
        _warm_up_in_background(model)  # load the model while the user types
        try:
            topic = input("What topic should I research? ").strip()
        except EOFError:
            topic = ""
        if not topic:
            print("No topic given. Try: research-agent --help", file=sys.stderr)
            return 2
        topics = [topic]

    results = [run_topic(topic, model, args) for topic in topics]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
