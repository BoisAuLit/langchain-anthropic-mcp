{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "jupytext": {
   "main_language": "bash",
   "notebook_metadata_filter": "-all",
   "cell_metadata_filter": "-all",
   "text_representation": {
    "extension": ".md",
    "format_name": "markdown"
   }
  }
 },
 "cells": [
  {
   "id": "6bc72bba",
   "cell_type": "markdown",
   "source": "# {{crew_name}} Crew\n\nWelcome to the {{crew_name}} Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.\n\n## Installation\n\nEnsure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.\n\nFirst, if you haven't already, install uv:",
   "metadata": {}
  },
  {
   "id": "c7e07d33",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "pip install uv",
   "outputs": []
  },
  {
   "id": "3ebaf0c9",
   "cell_type": "markdown",
   "source": "Next, navigate to your project directory and install the dependencies:\n\n(Optional) Lock the dependencies and install them by using the CLI command:",
   "metadata": {
    "lines_to_next_cell": 0
   }
  },
  {
   "id": "58e0da35",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "crewai install",
   "outputs": []
  },
  {
   "id": "a604db7e",
   "cell_type": "markdown",
   "source": "### Customizing\n\n**Add your `OPENAI_API_KEY` into the `.env` file**\n\n- Modify `src/code_review_flow/config/agents.yaml` to define your agents\n- Modify `src/code_review_flow/config/tasks.yaml` to define your tasks\n- Modify `src/code_review_flow/crew.py` to add your own logic, tools and specific args\n- Modify `src/code_review_flow/main.py` to add custom inputs for your agents and tasks\n\n## Running the Project\n\nTo kickstart your flow and begin execution, run this from the root folder of your project:",
   "metadata": {}
  },
  {
   "id": "6a944438",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "crewai run",
   "outputs": []
  },
  {
   "id": "5dea87bb",
   "cell_type": "markdown",
   "source": "This command initializes the code_review_flow Flow as defined in your configuration.\n\nThis example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.\n\n## Understanding Your Crew\n\nThe code_review_flow Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.\n\n## Support\n\nFor support, questions, or feedback regarding the {{crew_name}} Crew or crewAI.\n\n- Visit our [documentation](https://docs.crewai.com)\n- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)\n- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)\n- [Chat with our docs](https://chatg.pt/DWjSBZn)\n\nLet's create wonders together with the power and simplicity of crewAI.",
   "metadata": {}
  }
 ]
}
