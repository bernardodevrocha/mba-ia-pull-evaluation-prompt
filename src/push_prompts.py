import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "bug_to_user_story_v2.yml")


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """Publica o prompt (público) no Hub com descrição, tags e técnicas. Retorna True se deu certo."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])

    techniques = prompt_data.get("techniques_applied", [])
    tags = list(dict.fromkeys(
        prompt_data.get("tags", [])
        + [prompt_data.get("version", "")]
        + [t.lower().replace(" ", "-") for t in techniques]
    ))
    tags = [t for t in tags if t]

    description = prompt_data.get("description", "")
    if techniques:
        description = f"{description} | Técnicas: {', '.join(techniques)}"

    try:
        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=description,
            readme=prompt_data.get("readme"),
            tags=tags,
        )
    except Exception as e:
        if "nothing to commit" in str(e).lower() or "409" in str(e):
            print("   ℹ️  Nenhuma alteração desde o último push (prompt já está atualizado)")
            return True
        print(f"❌ Erro ao fazer push de '{prompt_name}': {e}")
        return False

    print(f"   ✓ Push realizado: {prompt_name}")
    print(f"   ✓ Tags: {', '.join(tags)}")
    print(f"   ✓ URL: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """Valida o prompt e devolve (ok, lista_de_erros)."""
    is_valid, errors = validate_prompt_structure(prompt_data)

    user_prompt = (prompt_data.get("user_prompt") or "").strip()
    if not user_prompt:
        errors.append("user_prompt está vazio")
    elif "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")

    if "{bug_report}" in prompt_data.get("system_prompt", ""):
        errors.append("{bug_report} deve aparecer apenas no user_prompt, não no system_prompt")

    return (len(errors) == 0, errors)


def main():
    """Checa o .env, carrega o YAML, valida e faz o push."""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(PROMPT_PATH)
    if not data or PROMPT_KEY not in data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {PROMPT_PATH}")
        return 1

    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print("   ✓ Prompt validado")

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/{PROMPT_KEY}"
    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
