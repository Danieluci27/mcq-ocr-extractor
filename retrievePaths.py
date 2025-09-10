from pathlib import Path
import re
from typing import List

def retrieve_paths(
    directory: str | Path,
    max_id: int = 204251
) -> List[str]:
    '''
    This function returns the names of JPG files that
    includes screenshots of problems. 
    Look in `directory` for JPG/JPEG files named like:
      Screenshot_<date>_<ID>_<randomWord>.jpg
    Keep those with numeric ID <= max_id as any JPG file with ID > max_id are not problems 
    and return their file names.
    '''
    directory = Path(directory)
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    # Regex: Screenshot_<anything>_<ID>_<anything>.(jpg|jpeg)
    # ID captured in group 2
    pattern = re.compile(
        r'^Screenshot_.+?_(\d+?)_.+\.(jpg|jpeg)$',
        re.IGNORECASE
    )

    matches = []
    for p in directory.iterdir():
        if not p.is_file():
            continue
        m = pattern.match(p.name)
        if not m:
            continue
        try:
            file_id = int(m.group(1))
        except ValueError:
            continue  # ID wasn't a valid integer
        if file_id <= max_id:
            matches.append(str(directory / p.name))

    return matches




