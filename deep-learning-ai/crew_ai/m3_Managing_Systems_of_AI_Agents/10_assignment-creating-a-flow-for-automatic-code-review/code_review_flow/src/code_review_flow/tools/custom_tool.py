{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "jupytext": {
   "main_language": "python",
   "notebook_metadata_filter": "-all",
   "cell_metadata_filter": "-all",
   "text_representation": {
    "extension": ".py",
    "format_name": "light"
   }
  }
 },
 "cells": [
  {
   "id": "ebfc431b",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "from typing import Type",
   "outputs": []
  },
  {
   "id": "2135ad10",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "from crewai.tools import BaseTool\nfrom pydantic import BaseModel, Field",
   "outputs": []
  },
  {
   "id": "e6b34a74",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "class MyCustomToolInput(BaseModel):\n    \"\"\"Input schema for MyCustomTool.\"\"\"\n\n    argument: str = Field(..., description=\"Description of the argument.\")",
   "outputs": []
  },
  {
   "id": "da10ad4d",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "class MyCustomTool(BaseTool):\n    name: str = \"Name of my tool\"\n    description: str = (\n        \"Clear description for what this tool is useful for, your agent will need this information to use it.\"\n    )\n    args_schema: Type[BaseModel] = MyCustomToolInput\n\n    def _run(self, argument: str) -> str:\n        # Implementation goes here\n        return \"this is an example of a tool output, ignore it and move along.\"",
   "outputs": []
  }
 ]
}
