import re
import pytest
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Dados do prompt v2."""
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    """Texto do system prompt."""
    return prompt_data.get("system_prompt", "")


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert isinstance(prompt_data["system_prompt"], str)
        assert prompt_data["system_prompt"].strip()

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"Você é um[a]? ", system_prompt), "Persona não definida com 'Você é um...'"
        assert re.search(r"Product Manager|Product Owner|Analista", system_prompt), \
            "Persona deve ter um papel profissional explícito"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        lowered = system_prompt.lower()
        assert "user story" in lowered
        assert "como um" in lowered and "eu quero" in lowered and "para que" in lowered
        assert "critérios de aceitação" in lowered
        assert "dado que" in lowered and "quando" in lowered and "então" in lowered

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"###\s*Exemplo\s+\d+", system_prompt)
        assert len(examples) >= 2, f"Esperado ao menos 2 exemplos, encontrados {len(examples)}"
        assert system_prompt.count("Relato de bug:") >= len(examples)
        assert system_prompt.count("User Story:") >= len(examples)

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field in ("system_prompt", "user_prompt", "description"):
            text = prompt_data.get(field, "") or ""
            assert "[TODO]" not in text, f"[TODO] encontrado em '{field}'"
            assert "TODO" not in text, f"TODO encontrado em '{field}'"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas {len(techniques)}"
        assert "Few-shot Learning" in techniques, "Few-shot Learning é obrigatório"

    def test_prompt_structure_is_valid(self, prompt_data):
        """Valida a estrutura completa com o validador de utils.py."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, errors

    def test_bug_report_only_in_user_prompt(self, prompt_data):
        """{bug_report} deve estar no user prompt e não duplicado no system prompt."""
        assert "{bug_report}" in prompt_data.get("user_prompt", "")
        assert "{bug_report}" not in prompt_data.get("system_prompt", "")

    def test_system_prompt_has_no_template_variables(self, system_prompt):
        """Chaves no system prompt seriam interpretadas como variáveis pelo ChatPromptTemplate."""
        assert not re.search(r"\{[^{}]*\}", system_prompt)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
