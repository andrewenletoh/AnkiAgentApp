"""
Configuration for the Anki Agent.
 
Every person who runs this app supplies their own values from AWS and Bedrock via
environment variables (or a local .env file, which is gitignored). If the
required values are missing, the app will not start.
 
AWS credentials themselves (access key/secret, SSO profile, or an assumed
role) are never read here. They're resolved by boto3's standard credential
chain on whatever machine runs the app. This module only controls *which*
region and model that machine's own credentials get used against.
"""
 
import os
 
from dotenv import load_dotenv
 
load_dotenv()  # no-op if there's no .env file present
 
 
class MissingBedrockConfigError(RuntimeError):
    """Raised when required Bedrock configuration is not present in the environment."""
 
 
REQUIRED_ENV_VARS = ("AWS_REGION", "BEDROCK_MODEL_ID")
 
 
def get_bedrock_config() -> dict[str, str]:
    """Read required Bedrock settings from the environment.
 
    Returns:
        dict with "region_name" and "model_id".
 
    Raises:
        MissingBedrockConfigError: if AWS_REGION or BEDROCK_MODEL_ID is not set.
    """
    missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise MissingBedrockConfigError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ".\n\nCopy .env.example to .env and fill in your own AWS region "
            "and Bedrock model ID, or export these as environment variables. "
            "See the README's 'AWS / Bedrock Setup' section for details."
        )
 
    return {
        "region_name": os.environ["AWS_REGION"],
        "model_id": os.environ["BEDROCK_MODEL_ID"],
    }
 
