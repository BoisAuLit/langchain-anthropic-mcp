import arxiv
import json
import os
from typing import Any, List

from console import ConsoleView

PAPER_DIR = "papers"


def search_papers(topic: str, max_results: int = 5) -> List[str]:
    client = arxiv.Client()

    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = client.results(search)

    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            papers_info = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids = []
    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)
        papers_info[paper_id] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(papers_info, f, indent=2, ensure_ascii=False)

    ConsoleView.success(f"search_papers saved results to: {file_path}")
    ConsoleView.info("returned paper_ids", paper_ids, icon="📄")
    return paper_ids


def extract_info(paper_id: str) -> str:
    if not os.path.exists(PAPER_DIR):
        return f"Paper directory '{PAPER_DIR}' does not exist yet."

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if not os.path.isdir(item_path):
            continue

        file_path = os.path.join(item_path, "papers_info.json")
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                papers_info = json.load(f)
            if paper_id in papers_info:
                return json.dumps(papers_info[paper_id], indent=2, ensure_ascii=False)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            ConsoleView.warn(f"Error reading {file_path}: {str(e)}")

    return f"There's no saved information related to paper {paper_id}."


def execute_tool(tool_name: str, tool_args: dict[str, Any]) -> str:
    ConsoleView.tool_call(tool_name, tool_args)

    if tool_name not in mapping_tool_function:
        return f"Unknown tool: {tool_name}"

    try:
        result = mapping_tool_function[tool_name](**tool_args)
    except Exception as e:
        return f"Tool execution error: {type(e).__name__}: {str(e)}"

    if result is None:
        result = "The operation completed but didn't return any results."
    elif isinstance(result, list):
        result = ", ".join(result)
    elif isinstance(result, dict):
        result = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        result = str(result)

    ConsoleView.tool_result(result)
    return result


mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info,
}

tools = [
    {
        "name": "search_papers",
        "description": (
            "Search for papers on arXiv based on a topic and store their information. "
            "Returns a list of paper IDs. If the user asks to search papers, call this first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to search for"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to retrieve",
                    "default": 5,
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "extract_info",
        "description": (
            "Search for information about a specific paper using a paper ID. "
            "Only call this after you have received actual paper IDs from search_papers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "paper_id": {"type": "string", "description": "The ID of the paper to look for"}
            },
            "required": ["paper_id"],
        },
    },
]
