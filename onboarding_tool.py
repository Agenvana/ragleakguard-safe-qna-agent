from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
from typing import Literal, Optional

load_dotenv()


class OnboardingTool(BaseTool):
    """
    Customizes the Safe Q&A Agent before deployment: agent naming, model,
    detection locale and business context. Deliberately, there is NO bulk
    knowledge-file upload field here: every document enters the knowledge base
    through the agent's scan-before-ingest tool, never around it. No field
    here ever asks for, or stores, actual sensitive data values.
    """

    agent_name: str = Field(
        "Safe Q&A Agent",
        description="Name of the agent visible to your users.",
    )

    model: Literal["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"] = Field(
        "gpt-5.6-luna",
        description="OpenAI model the agent runs on (verified against the July 2026 catalog). "
        "The document scanner runs locally and costs no tokens; the economical "
        "gpt-5.6-luna is a strong default for Q&A.",
    )

    locale: Literal["default", "au"] = Field(
        "default",
        description="Detection locale pack for document scans. 'au' adds Australian "
        "identifiers (TFN, ABN, ACN, Medicare, AU phone formats) on top of the "
        "global/US defaults.",
        json_schema_extra={
            "ui:title": "Detection Locale",
        },
    )

    business_overview: Optional[str] = Field(
        None,
        description="Brief overview of your business and what this Q&A agent should "
        "help users with.",
        json_schema_extra={
            "ui:widget": "textarea",
            "ui:placeholder": "We answer product and policy questions for our online "
            "store's customers.",
        },
    )

    data_context: Optional[str] = Field(
        None,
        description="What kinds of documents will feed the knowledge base (categories "
        "only; never paste real records here).",
        json_schema_extra={
            "ui:widget": "textarea",
            "ui:placeholder": "Product FAQs, return policies, shipping guides.",
        },
    )

    assessment_contact: Optional[str] = Field(
        "https://tally.so/r/obaG5V",
        description="Where the agent softly points users who need a formal, human-led "
        "AI data-security assessment (email or URL). Deploying for your own clients? "
        "Replace this with your security team's contact, or clear it to disable the mention.",
        json_schema_extra={
            "ui:title": "Assessment Contact",
        },
    )

    def run(self):
        """
        Saves the configuration as a Python file with a config object.
        """
        import json

        tool_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(tool_dir, "onboarding_config.py")

        config = self.model_dump()

        json_str = json.dumps(config, indent=4, ensure_ascii=False)
        json_str = json_str.replace(": null", ": None").replace(": true", ": True").replace(": false", ": False")
        python_code = f"# Auto-generated onboarding configuration\n\nconfig = {json_str}\n"

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(python_code)
            return f"Configuration saved at: {config_path}"
        except Exception as e:
            return f"Error writing config file: {str(e)}"


if __name__ == "__main__":
    tool = OnboardingTool()
    print(tool.run())
