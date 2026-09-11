import ollama
from pathlib import Path
import re
import shutil

from nista import backend_prompts, frontend_prompts

features_dir = Path('../features_stari')
features_files = sorted(features_dir.glob('*.feature'))

if not features_files:
    raise RuntimeError("Feature directory is empty, no feature files found!")

context = ''

for file in features_files:
    context += f'\n\n===== {file.name} =====\n'
    context += file.read_text(encoding='utf-8')

model_name = 'gemma4:31b:cloud'


def make_backend():
    call(backend_prompts.generate_backend_models())
    call(backend_prompts.generate_backend_middlewares())
    call(backend_prompts.generate_backend_controllers())
    call(backend_prompts.generate_backend_routers())
    call(backend_prompts.generate_backend_base())

def make_frontend():
    call(frontend_prompts.generate_frontend_models())
    call(frontend_prompts.generate_frontend_services())
    call(frontend_prompts.generate_frontend_components())
    call(frontend_prompts.generate_frontend_guards())
    call(frontend_prompts.generate_angular_base())

def call(prompt : str) -> None:
    response = ollama.chat(
        model=model_name,
        messages=[
            {
                'role':'user',
                'content':prompt
            }
        ],
        options={
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 40,
            "seed": 42,
            "repeat_penalty": 1.1,
            "num_predict": 32000
        },
        stream=False
    )

    generated_text = response.message.content

    # print(f'\n\n{generated_text}\n\n')

    # raw_response_file = output_dir / 'llm_response.txt'
    # raw_response_file.write_text(generated_text, encoding='utf-8')

    pattern = re.compile(
        r"FILE:\s*([^\r\n]+)\r?\n\s*"
        r"```[^\r\n]*\r?\n"
        r"(.*?)"
        r"\r?\n```",
        re.DOTALL
    )

    matches = pattern.findall(generated_text)

    if not matches:
        raise RuntimeError('No files were found in the LLM response.')

    output_dir = Path('app')

    for relative_path, content in matches:
        relative_path = relative_path.strip()

        relative_path = relative_path.replace("\\", "/")
        path = Path(relative_path)

        if path.is_absolute():
            raise RuntimeError(f'Refusing to create absolute path: {relative_path}')

        if '..' in path.parts:
            raise RuntimeError(f'Refusing unsafe path: {relative_path}')

        destination = output_dir / path

        # print("DESTINATION:", destination)
        # print("LENGTH:", len(str(destination)))

        destination.parent.mkdir(parents=True, exist_ok=True)

        destination.write_text(
            content.rstrip() + '\n',
            encoding='utf-8'
        )


output_dir = Path('app')
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir()

make_backend()
# make_frontend()