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
   "id": "ffbf9e1e",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "import os\nfrom crewai import Agent, Crew, Process, Task\nfrom crewai.project import CrewBase, agent, crew, task\nfrom crewai_tools import (\n\tSerperDevTool,\n    ScrapeWebsiteTool,\n)\nfrom pydantic import BaseModel\nfrom code_review_flow.utils import get_serper_api_key, get_openai_api_key\n# import the guardrails\nfrom code_review_flow.crews.code_review_crew.guardrails.guardrails import security_review_output_guardrail",
   "outputs": []
  },
  {
   "id": "4cee7609",
   "cell_type": "code",
   "metadata": {
    "lines_to_next_cell": 1,
    "trusted": true
   },
   "execution_count": null,
   "source": "os.environ[\"OPENAI_API_KEY\"] = get_openai_api_key()\nos.environ[\"SERPER_API_KEY\"] = get_serper_api_key()",
   "outputs": []
  },
  {
   "id": "ab223426",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "@CrewBase\nclass CodeReviewCrew:\n    \"\"\"CodeReview crew\"\"\"\n    @agent\n    def senior_developer(self) -> Agent:       \n        return Agent(\n            config=self.agents_config[\"senior_developer\"],\n            llm=\"gpt-4o-mini\",\n        )\n\n    ### START CODE HERE ###\n    @None\n    ### END CODE HERE ###\n    def security_engineer(self) -> Agent:\n        os.environ[\"SERPER_API_KEY\"] = get_serper_api_key()\n        return Agent(\n            config=self.agents_config[\"security_engineer\"],\n            tools=[\n                # add the SerperDevTool to the agent's tools\n                SerperDevTool(search_url=\"https://owasp.org\",\n                              base_url=os.getenv(\"DLAI_SERPER_BASE_URL\")),\n                ScrapeWebsiteTool() \n                ],\n            llm=\"gpt-4o-mini\"\n        )\n    \n    ### START CODE HERE ###\n    @None\n    ### END CODE HERE ###\n    def tech_lead(self) -> Agent:\n        return Agent(\n            config=self.agents_config[\"tech_lead\"],\n            llm=\"gpt-4o-mini\",\n        )\n        \n    @task\n    def analyze_code_quality(self) -> Task:\n        # Define the pydantic model for the code quality analysis output\n        class CodeQualityJSON(BaseModel):\n            critical_issues: list[str]\n            minor_issues: list[str]\n            reasoning: str\n        return Task(\n            config=self.tasks_config[\"analyze_code_quality\"],\n            output_json=CodeQualityJSON,\n            \n            ### START CODE HERE ###\n            # allow for asynchronous execution\n            async_execution=None,\n            ### END CODE HERE ###\n        )\n    \n    ### START CODE HERE ###\n    @None\n    ### END CODE HERE ###\n    def review_security(self) -> Task:\n        # Define the pydantic model for the security vulnerabilities\n        class SecurityVulnerability(BaseModel):\n            description: str \n            risk_level: str \n            evidence: str\n\n        # Define the pydantic model for the security review output\n        class ReviewSecurityJSON(BaseModel):\n            security_vulnerabilities: list[SecurityVulnerability] \n            blocking: bool\n            highest_risk: str\n            security_recommendations: list[str]\n\n        return Task(\n            config=self.tasks_config[\"review_security\"],\n            output_json=ReviewSecurityJSON,\n\n            ### START CODE HERE ###\n            # allow for asynchronous execution\n            async_execution=None,\n            ### END CODE HERE ###\n\n            # add the security review output guardrail (already imported above)\n            guardrails=[security_review_output_guardrail]\n        )\n    \n    ### START CODE HERE ###\n    @None\n    ### END CODE HERE ###\n    def summarize_findings(self) -> Task:\n        \n        # Define the pydantic model for the fixes output\n        class Fix(BaseModel):\n            description: str \n            solutions: str \n            explanation: str\n\n        ### START CODE HERE ###\n        # Define the pydantic model for the summarized findings output\n        class SummarizedFindingsJSON(BaseModel):\n            confidence: None\n            findings: None\n            fix: None[Fix]\n            recommendations: list[None]\n        ### END CODE HERE ###\n        \n        return Task(\n            config=self.tasks_config[\"summarize_findings\"],\n            # Set the Markdown parameter to get the final report in Markdown format\n            output_json=SummarizedFindingsJSON,\n        )\n    \n\n    ### START CODE HERE ###\n    @None\n    ### END CODE HERE ###\n    def crew(self) -> Crew:\n        \"\"\"Creates the CodeReviewCrew crew\"\"\"\n        return Crew(\n            agents=self.agents,  # Automatically created by the @agent decorator\n            tasks=self.tasks,  # Automatically created by the @task decorator\n            # set the process to sequential\n            process=Process.sequential,\n            verbose=True,\n            memory=True,\n        )",
   "outputs": []
  }
 ]
}
