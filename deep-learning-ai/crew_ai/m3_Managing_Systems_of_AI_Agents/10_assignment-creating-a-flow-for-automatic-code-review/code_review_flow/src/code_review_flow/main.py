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
   "id": "a6fa788f",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "from pydantic import BaseModel\nfrom crewai import LLM\nfrom crewai.flow import Flow, listen, start, router, or_, persist\n# from typing import Literal, Optional\nfrom code_review_flow.crews.code_review_crew.crew import CodeReviewCrew\nimport dill\nimport json",
   "outputs": []
  },
  {
   "id": "39e64506",
   "cell_type": "code",
   "metadata": {
    "lines_to_next_cell": 1,
    "trusted": true
   },
   "execution_count": null,
   "source": "import os\nos.environ[\"CREWAI_TESTING\"] = \"true\"",
   "outputs": []
  },
  {
   "id": "4dbde296",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "# define the flow state\nclass ReviewState(BaseModel):\n    # already dive the path to the PR diff file\n    pr_file_path: str = \"../files/code_changes.txt\"\n    ### START CODE HERE ###\n    pr_content: None = None # initialize with an empty string\n    errors: None = None # initialize with an empty list\n    review_result: None = {} # set the correct type\n    crew_needed: None = False # set the correct type\n    tokens_used: dict = None # initialize with an empty dict\n    final_answer: None = None # initialize with an empty string\n    ### END CODE HERE ###",
   "outputs": []
  },
  {
   "id": "a081db94",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "@persist()\n# Define the flow\nclass PRCodeReviewFlow(Flow[ReviewState]):\n    \"\"\"\n    CrewAI Flow for automated code review of pull requests.\n    \"\"\"\n    ### START CODE HERE ###\n    @None()\n    ### END CODE HERE ###\n    def read_pr_file(self):\n        \"\"\"Read the PR file and determine if crew review is needed\"\"\"\n        print(\"🔍 Starting PR Code Review...\")\n        \n        # Get the file path from the state\n        pr_file_path = self.state.pr_file_path\n\n        if not pr_file_path:\n            # append some error message to the errors state variable\n            self.state.errors.append(\"Missing 'file_path' in state\") \n            # save the error message in the final answer state variable\n            self.state.final_answer = f\"There was no file_path set. Please set the 'file_path' in the state and try again.\" \n            print(f\"❌ {self.state.final_answer}\")\n            return\n\n        # try reading the file\n        try:\n            with open(pr_file_path, \"r\") as f:\n                file_contents = f.read()\n            \n            ### START CODE HERE ###\n            # save the file content in the state variable\n            self.state.pr_content = None\n            ### END CODE HERE ###\n               \n        # if there are any issues, raise an error\n        except Exception as e:\n            error_message = f\"There was an error reading the file at {pr_file_path}: \\n{str(e)}\"\n            print(f\"❌ {error_message}\")\n            ### START CODE HERE ###\n            # append some error message to the errors state variable\n            self.state.None.append(\"Error while reading the PR file\")\n            # save the error message in the final answer state variable\n            self.state.None = None\n            ### END CODE HERE ###\n\n    ### START CODE HERE ###\n    @None(\"read_pr_file\")\n    ### END CODE HERE ###\n    def analyze_changes(self, context):\n        \"\"\"Route to appropriate review type based on complexity\"\"\"\n\n        ### START CODE HERE ###\n        # if there are any errors in the state variable, return 'ERROR'\n        if len(self.state.errors) > 0:\n            return None\n        ### END CODE HERE ###\n\n        else:\n            # define the prompt to analyze the changes\n            prompt = (\n                \"Analyze this pull request diff file and respond with exactly one word: SIMPLE or COMPLEX.\\n\"\n                \"SIMPLE: small changes that don't compromise code quality or security. For example typos, minor refactoring, formatting, small doc changes\"\n                \"COMPLEX: bigger changes that need closer inspection. For example new features, bug fixes, logic changes, security-relevant changes, or anything requiring deep review or best practices research.\\n\"\n                f\"\\nPR Diff:\\n{self.state.pr_content}\\n\"\n                )\n\n            # define the llm for the decision \n            llm = LLM(model=\"gpt-4o-mini\",) \n            # call the llm and save the result\n            decision = llm.call(messages=prompt) \n            \n            # the word COMPLEX is in the decision, \n            # set the crew_needed to True in the state and return \"COMPLEX\"\n            if \"COMPLEX\" in decision.upper():\n                ### START CODE HERE ###\n                self.None.None = None\n                return None\n                ### END CODE HERE ###\n            # if not COMPLEX (i.e. SIMPLE)\n            # set the crew_needed to False in the state and return \"SIMPLE\"\n            else:\n                ### START CODE HERE ###\n                self.None.None = None\n                return None\n                ### END CODE HERE ###\n\n    # if the PR is simple, do a simple review\n    ### START CODE HERE ###\n    @None(None)\n    ### END CODE HERE ###\n    def simple_review(self):\n        \"\"\"Simple review for minor changes\"\"\"\n        print(\"⚡ Performing simple review...\")\n        \n        ### START CODE HERE ###\n        # Complete the last part of the prompt\n        prompt = (\n            \"Analyze this pull request diff file and evaluate the changes.\\n\"\n            \"Do not make assumptions or considerations about the code outside of the diff provided, but if warranted you can make suggestions.\\n\"\n            None)\n        ### END CODE HERE ###\n\n        # define the llm for the decision \n        llm = LLM(model=\"gpt-4o-mini\",)\n        # call the llm and save the result\n        result = llm.call(messages=prompt)\n\n        ### START CODE HERE ###\n        # Save the result of the LLM call in the review_result state variable\n        self.None.None = None\n        ### END CODE HERE ###\n\n    # if the PR is complex, deploy crew review\n    ### START CODE HERE ###\n    @None(None)\n    ### END CODE HERE ###\n    def full_crew_review(self):\n        \"\"\"Full crew review for complex changes\"\"\"\n        print(\"🚀 Starting full crew review...\")\n        \n        # get the PR content from the state variable\n        pr_content = self.state.pr_content\n\n        # create the crew\n        code_review_crew = CodeReviewCrew().crew()\n\n        try: \n            ### START CODE HERE ###\n            # kickoff the crew. Pass the PR content in the inputs\n            result = code_review_crew.None(None={'file_content': None})\n\n            # save the results in the state variable. You can use the `json_dict` attribute of the result\n            self.state.review_result = None\n\n            # save the tokens used by the crew. You can use the `token_usage` attribute of the result\n            self.state.tokens_used = None\n            ### END CODE HERE ###\n        except Exception as e:\n            error_message = f\"There was an error during the crew review: \\n{str(e)}\"\n            print(f\"❌ {error_message}\")\n            ### START CODE HERE ###\n            # append some error message to the errors state variable\n            self.None.None.append(\"Error during crew review\")\n            # save the error message in the final answer state variable\n            self.None.None = None\n            ### END CODE HERE ###\n\n    # make the final decision based on the review results\n    ### START CODE HERE ###\n    @None(None(None, None))\n    ### END CODE HERE ###\n    def make_final_decision(self):\n        \"\"\"Make the final decision based on the review results\"\"\"\n        print(\"🧐 Making final decision based on review results...\")\n        \n        # get the review result from the state variable\n        review_result = self.state.review_result\n\n        # use an LLM call to make the final decision and generate the final message\n        prompt = (\n            \"Based on the following analysis of the pull request diff file, \"\n            \"make a final decision on whether to approve the PR for merging.\\n\" \\\n            \"Any review with a confidence score above 85 can be approves, but improvements can be suggested.\\n\"\n            \"Return a full report with:\\n\"\n            \"- Final Review Decision: APPROVE (the PR is good to be approved), REQUEST CHANGES (the PR needs some modifications, but they are concrete changes) \" \n            \" or ESCALATE (the PR requires human attention, there are major issues that need fixing)\\n\"\n            \"- Confidence Score: int. A confidence score between 0-100 that indicates the confidence for merging the PR\\n\"\n            \"- Findings: str. A summary of the key findings\\n\"\n            \"- If the decision is to REQUEST CHANGES, provide a list of the changes requested to grant approval\\n\"\n            \"- If the decision is to ESCALATE, provide a list of reasons why the PR needs to be escalated to a human reviewer, along with possible solutions\\n\"\n            f\"\\nAnalysis:\\n{review_result}\\n\"\n        )\n        llm = LLM(model=\"gpt-4o-mini\",)\n        \n        ### START CODE HERE ###\n        # make the LLM call\n        final_decision = llm.None(messages=None)\n        # save the final answer in the state variable\n        self.None.None = None\n        ### END CODE HERE ###\n\n\n    # return the final answer\n    @listen(or_(\"ERROR\", \"make_final_decision\"))\n    def return_final_answer(self):\n        \"\"\"Return the final answer to the user\"\"\"\n\n        print(\"📝 Final Answer:\")\n        print(f\"{self.state.final_answer}\")\n        print(\"\\n✨ Automatic code review completed!\")\n        return self.state.final_answer",
   "outputs": []
  },
  {
   "id": "d6a3e086",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "def kickoff():\n    ### START CODE HERE ###\n    # instantiate the flow with tracing enabled\n    pr_code_review_flow = None(tracing=None)\n    # kickoff the flow. \n    # Here you have a custom id set so that that you can use the persistence features\n    result = pr_code_review_flow.None(inputs={\"id\": \"my_code_review_flow\"})\n    ### END CODE HERE ###\n\n    # save the result of the flow - for grading purposes\n    with open('../result.dill', 'wb') as f:\n        dill.dump(result, f)\n    # Save the flow state as JSON - for grading purposes\n    with open('../flow_state.json', 'w') as f:\n        json.dump(pr_code_review_flow.state.model_dump(), f, indent=2)",
   "outputs": []
  },
  {
   "id": "c2c82de9",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "def plot():\n    pr_code_review_flow = PRCodeReviewFlow()\n    pr_code_review_flow.plot()",
   "outputs": []
  },
  {
   "id": "0d6f0cce",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "if __name__ == \"__main__\":\n    kickoff()",
   "outputs": []
  }
 ]
}
