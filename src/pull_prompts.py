import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def extract_messages(prompt) -> dict:
    """Separa o texto do system prompt e do user prompt."""
    system_parts, user_parts = [], []

    for message in prompt.messages:
        template = getattr(getattr(message, "prompt", None), "template", None)
        if template is None:
            continue

        class_name = type(message).__name__
        if "System" in class_name:
            system_parts.append(template)
        elif "Human" in class_name:
            user_parts.append(template)

    return {
        "system_prompt": "\n\n".join(system_parts),
        "user_prompt": "\n\n".join(user_parts),
    }


def pull_prompts_from_langsmith():
    """Baixa o prompt do Hub e devolve os dados no formato do YAML (ou None se falhar)."""
    client = Client()

    print(f"Puxando prompt: {SOURCE_PROMPT}")
    try:
        prompt = client.pull_prompt(SOURCE_PROMPT, dangerously_pull_public_prompt=True)
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        return None

    messages = extract_messages(prompt)
    if not messages["system_prompt"] and not messages["user_prompt"]:
        print("❌ O prompt retornado não contém mensagens de texto")
        return None

    print(f"   ✓ Prompt carregado ({len(prompt.messages)} mensagens)")
    print(f"   ✓ Variáveis de entrada: {', '.join(prompt.input_variables)}")

    return {
        PROMPT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": messages["system_prompt"],
            "user_prompt": messages["user_prompt"],
            "version": "v1",
            "source": SOURCE_PROMPT,
            "input_variables": list(prompt.input_variables),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }


def main():
    """Checa o .env, faz o pull e salva o arquivo."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    data = pull_prompts_from_langsmith()
    if data is None:
        return 1

    if not save_yaml(data, str(OUTPUT_PATH)):
        return 1

    print(f"   ✓ Prompt salvo em: {OUTPUT_PATH.relative_to(OUTPUT_PATH.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
