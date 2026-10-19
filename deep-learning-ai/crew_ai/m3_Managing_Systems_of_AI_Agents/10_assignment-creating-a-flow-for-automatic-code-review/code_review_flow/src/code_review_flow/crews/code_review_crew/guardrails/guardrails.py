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
   "id": "b995c11b",
   "cell_type": "code",
   "metadata": {
    "lines_to_next_cell": 1,
    "trusted": true
   },
   "execution_count": null,
   "source": "import re",
   "outputs": []
  },
  {
   "id": "604f5f56",
   "cell_type": "code",
   "metadata": {
    "trusted": true
   },
   "execution_count": null,
   "source": "def security_review_output_guardrail(output):\n    \n    # get the (JSON) output from the TaskOutput object\n    try: \n        json_output = output if type(output)==dict else output.json_dict\n    except Exception as e:\n        return (False, (\"Error retrieving the `json_dict` argument: \"\n                        f\"\\n{str(e)}\\n\"\n                        \"Make sure you set the output_json parameter in the Task.\"\n                        )\n                )\n\n    # define risk levels\n    valid_risk_levels = ['low', 'medium', 'high']\n\n    # validate that the highest risk level has a valid value\n    if json_output[\"highest_risk\"].lower() not in valid_risk_levels: \n        error_message = \"Invalid highest risk level.\"\n        return (False, error_message)\n    \n    # validate that each of the risk levels has a valid value\n    for vuln in json_output['security_vulnerabilities']:\n        # validate the risk level\n        if vuln['risk_level'].lower() not in valid_risk_levels:\n            error_message = f\"Invalid risk level: {vuln['risk_level']}\" \n            return (False, error_message)\n    \n    # validate that the highest risk level matches the highest risk level in the vulnerabilities\n    # get all risk_level values\n    risk_levels = [vuln['risk_level'].lower() for vuln in json_output['security_vulnerabilities']] \n    \n    # if \"high\" in risk levels, then highest risk level should be high\n    if \"high\" in risk_levels: \n        if json_output[\"highest_risk\"].lower() != \"high\":\n            error_message = \"Highest risk level does not match the highest risk level in the vulnerabilities.\"\n            return (False, error_message) \n    # if high is not present and medium is in risk levels, then highest risk level should be medium\n    elif \"medium\" in risk_levels: \n        if json_output[\"highest_risk\"].lower() != \"medium\":\n            error_message = \"Highest risk level does not match the highest risk level in the vulnerabilities.\"\n            return (False, error_message)\n    # if high and medium are not present, then lowest risk level should be low\n    elif \"low\" in risk_levels: \n        if json_output[\"highest_risk\"].lower() != \"low\":\n            error_message = \"Highest risk level does not match the highest risk level in the vulnerabilities.\"\n            return (False, error_message)\n    return (True, output.json_dict)",
   "outputs": []
  }
 ]
}
