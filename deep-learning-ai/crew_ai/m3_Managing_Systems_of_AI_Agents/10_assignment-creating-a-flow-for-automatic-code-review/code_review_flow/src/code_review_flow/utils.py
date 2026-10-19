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
   "id": "9b83e6ef",
   "cell_type": "markdown",
   "source": "Add your utilities or helper functions to this file.",
   "metadata": {}
  },
  {
   "id": "b54d3cb7",
   "cell_type": "code",
   "metadata": {
    "lines_to_next_cell": 1,
    "trusted": true
   },
   "execution_count": null,
   "source": "import os\nfrom dotenv import load_dotenv, find_dotenv\nimport json\nfrom crewai import TaskOutput",
   "outputs": []
  },
  {
   "id": "cc0e1681",
   "cell_type": "code",
   "metadata": {
    "lines_to_next_cell": 1,
    "trusted": true
   },
   "execution_count": null,
   "source": "# these expect to find a .env file at the directory above the lesson.                                                                                                                     # the format for that file is (without the comment)                                                                                                                                       #API_KEYNAME=AStringThatIsTheLongAPIKeyFromSomeService\ndef load_env():\n    _ = load_dotenv(find_dotenv())",
   "outputs": []
  },
  {
   "id": "1483f8bd",
   "cell_type": "code",
   "metadata": {
    "lines_to_next_cell": 1,
    "trusted": true
   },
   "execution_count": null,
   "source": "def get_openai_api_key():\n    load_env()\n    openai_api_key = os.getenv(\"OPENAI_API_KEY\")\n    return openai_api_key",
   "outputs": []
  },
  {
   "id": "2cf8f0b8",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "def get_serper_api_key():\n    load_env()\n    serper_api_key = os.getenv(\"SERPER_API_KEY\")\n    return serper_api_key",
   "outputs": []
  }
 ]
}
