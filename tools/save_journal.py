from datetime import datetime
from pathlib import Path



def save_journal(user_text: str, root_dir: str):
    journal_path = Path(root_dir) / "memory" / "data" / "journal.txt"
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    entry = f"[{datetime.now().isoformat(timespec='seconds')}] {user_text}\n"
    with open(journal_path, "a", encoding="utf-8") as file_obj:
        file_obj.write(entry)
    return {
        "tool": "save_journal",
        "status": "success",
        "saved_text": user_text,
    }
