import shutil
import ollama
from pathlib import Path
import re
import prompt

features_dir = Path('../features_stari')
features_files = sorted(features_dir.glob('*.feature'))

if not features_files:
    raise RuntimeError("Feature directory is empty, no feature files found!")

context = ''

for file in features_files:
    context += f'\n\n===== {file.name} =====\n'
    context += file.read_text(encoding='utf-8')

model_name = 'gemma4:26b'

response = ollama.chat(
    model=model_name,
    messages=[
        {
            'role':'user',
            'content': prompt.prompt1(context)
        }
    ]
)

generated_text = response.message.content

output_dir = Path('app')

if output_dir.exists():
    shutil.rmtree(output_dir)

output_dir.mkdir()

raw_response_file = output_dir / 'llm_response.txt'
raw_response_file.write_text(generated_text, encoding='utf-8')

# pattern = re.compile(
#     r"FILE:\s*(.+?)\s*\n"
#     r"```[^\n]*\n"
#     r"(.*?)"
#     r"\n```",
#     re.DOTALL
# )

pattern = re.compile(
    r"FILE:\s*([^\r\n]+)\r?\n"
    r"```[^\r\n]*\r?\n"
    r"(.*?)"
    r"\r?\n```",
    re.DOTALL
)

matches = pattern.findall(generated_text)

if not matches:
    raise RuntimeError('No files were found in the LLM response.')


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