import os
import emoji


def strip_emojis(text):
    return emoji.replace_emoji(text, replace="")


changed_files = 0
for root, _, files in os.walk("."):
    if any(ignore in root for ignore in [".venv", ".git", "__pycache__", "env"]):
        continue
    for file in files:
        if file.endswith(".html") or file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            clean_content = strip_emojis(content)
            if content != clean_content:
                with open(path, "w", encoding="utf-8") as f:
                    # remove trailing whitespaces left by emojis
                    clean_content = clean_content.replace("  ", " ")
                    f.write(clean_content)
                print(f"Cleaned {path}")
                changed_files += 1

print(f"Finished stripping emojis from {changed_files} files.")
