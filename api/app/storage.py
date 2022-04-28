from pathlib import Path
from typing import (
    IO,
    BinaryIO,
    Callable,
    Iterator,
    Literal,
    List,
    Sequence,
    Set,
    Dict,
    Any,
    Union
)
import fsspec
import json


class StorageManager():
    CHUNK_SIZE = 4096
    fs: fsspec.AbstractFileSystem
    root: Path

    def __init__(self,
                 protocol: Literal['local', 's3'],
                 root: str,
                 **storage_options) -> None:
        self.fs = fsspec.filesystem(protocol=protocol, **storage_options)
        self.root = Path(root)

    def read_pdf_file_reader(self, sha: str) -> Callable:
        path = self.root / sha / f"{sha}.pdf"
        if self.fs.exists(path):
            def fn(path: str = path):
                with self.fs.open(path, 'rb') as f:
                    while chunk := f.read(self.CHUNK_SIZE):
                        yield chunk
            return fn
        else:
            return None

    def get_all_pdf_shas(self) -> List[str]:
        all_pdfs = self.fs.glob(self.root / "*/*.pdf")
        return [p.split("/")[-2] for p in all_pdfs]

    def read_user_status(self, user: str):
        path = self.root / "status" / f"{user}.json"

        if self.fs.exists(path):
            with self.fs.open(path, 'r', encoding='utf-8') as st:
                return json.load(st)

    def write_user_status(self,
                          user: str,
                          sha: str,
                          data: Dict[str, Any],
                          create_if_missing: bool = False):

        path = self.root / "status" / f"{user}.json"
        status_json = self.read_user_status(user=user)

        # we create a user via creating their user status,
        # but only if create_if_missing is True
        status_json = status_json or ({} if create_if_missing else None)

        if status_json is not None:
            self.fs.mkdirs(path.parent, exist_ok=True)

            with self.fs.open(path, 'w', encoding='utf-8') as st:
                status_json[sha] = {**status_json.get(sha, {}), **data}
                json.dump(status_json, st)

    def read_pdf_metadata(self) -> Dict[str, str]:
        path = self.root / "pdf_metadata.json"
        if self.fs.exists(path):
            with self.fs.open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def write_pdf_metadata(self, data: Dict[str, str]):
        pdf_metadata = {**self.read_pdf_metadata(), **data}
        path = self.root / "pdf_metadata.json"
        with self.fs.open(path, 'w', encoding='utf-8') as f:
            return json.dump(pdf_metadata, f)

    def read_user_annotations(
        self,
        user: str,
        sha: str
    ) -> Dict[str, Sequence[Dict[str, Any]]]:

        path = self.root / sha / f"{user}_annotations.json"

        if self.fs.exists(path):
            with self.fs.open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"annotations": [], "relations": []}

        return data

    def add_pdf_dir(self, path: Union[str, Path]) -> Path:
        src = Path(path)
        dst = self.root / path.name
        self.fs.put(str(src), str(dst), recursive=True)
        return dst

    def write_user_annotations(self,
                               user: str,
                               sha: str,
                               annotations: Sequence[Dict[str, Any]],
                               relations: Sequence[Dict[str, Any]]):
        path = self.root / sha / f"{user}_annotations.json"
        user_status = self.read_user_status(user)
        if user_status:
            data = {"annotations": annotations, "relations": relations}
            with self.fs.open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            status_data = {k: len(v) for k, v in data.items()}
            self.write_user_status(user=user, sha=sha, data=status_data)


    def get_pdf_structure(self, sha: str):
        pdf_structure = self.root / sha / 'pdf_structure.json'

        if self.fs.exists(pdf_structure):
            with self.fs.open(pdf_structure, "r", encoding='utf-8') as f:
                response = json.load(f)
        else:
            response = None

        return response


class UsersManager():
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def get_users(self) -> Set[str]:
        if self.path.exists():
            with open(self.path, 'r', encoding='utf-8') as f:
                return set(ln.strip() for ln in f
                        if ln.strip() and not ln.strip().startswith('#'))
        else:
            raise FileNotFoundError('Cannot Locate Users File')

    def is_valid_user(self, email: str) -> bool:
        try:
            valid_users =  self.get_users()
            domain = '@' + email.rsplit('@', 1)[-1]
            return email in valid_users or domain in valid_users
        except FileNotFoundError:
            return False
