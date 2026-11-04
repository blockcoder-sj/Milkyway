"""Update a ZIP installation from the public classroom branch, preserving data."""
from __future__ import annotations

from contextlib import ExitStack
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import urllib.request
from urllib.parse import urlsplit
import zipfile

REPOSITORY = "blockcoder-sj/Milkyway"
BRANCH = "codex/week10-python"
SOURCE_DIRS = {"cloud_app", "deploy", "docs", "tests"}
MAX_ZIP_BYTES = 32 * 1024 * 1024
MAX_SOURCE_BYTES = 96 * 1024 * 1024
MAX_FILES = 10000


def installation_root(candidate):
    root = Path(candidate).resolve()
    if not (root / "run_milkyway.py").is_file():
        matches = [p for p in root.glob("Milkyway*") if p.is_dir()
                   and not p.is_symlink() and (p / "run_milkyway.py").is_file()]
        if len(matches) != 1:
            raise RuntimeError("run_milkyway.py가 있는 실습 폴더에서 업데이트 명령을 실행해 주세요")
        root = matches[0].resolve()
    if (root / ".git").exists():
        raise RuntimeError("Git 체크아웃에는 ZIP 업데이트를 적용하지 않습니다. Git으로 업데이트해 주세요")
    return root


def download(url, maximum_bytes):
    request = urllib.request.Request(url, headers={"User-Agent": "Milkyway-Updater/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname not in {"api.github.com", "codeload.github.com"}:
            raise RuntimeError("GitHub 공식 다운로드 주소를 확인하지 못했습니다")
        payload = response.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise RuntimeError("업데이트 파일이 허용 용량을 초과했습니다")
    return payload


def source_member(path):
    if any(part.startswith(".") or part.casefold() in {"runtime", "backups", "logs", "__pycache__"}
           for part in path.parts):
        return False
    if len(path.parts) > 1:
        return path.parts[0] in SOURCE_DIRS
    name = path.name
    return (not name.startswith(".") and
            (name.endswith(".py") or name == "README.md" or
             (name.startswith("requirements") and path.suffix in {".txt", ".lock", ".in"})))


def archive_sources(payload):
    files, seen, roots, total = {}, set(), set(), 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        if len(members) > MAX_FILES:
            raise RuntimeError("업데이트 파일 수가 허용 범위를 초과했습니다")
        for member in members:
            name = member.filename
            path = PurePosixPath(name)
            if ("\\" in name or "\x00" in name or ":" in name or path.is_absolute()
                    or ".." in path.parts or not path.parts):
                raise RuntimeError("업데이트 ZIP에 안전하지 않은 경로가 있습니다")
            roots.add(path.parts[0])
            if len(roots) != 1:
                raise RuntimeError("업데이트 ZIP의 최상위 폴더가 올바르지 않습니다")
            if member.is_dir():
                continue
            mode = stat.S_IFMT(member.external_attr >> 16)
            if mode not in {0, stat.S_IFREG}:
                raise RuntimeError("업데이트 ZIP에 일반 파일이 아닌 항목이 있습니다")
            if len(path.parts) < 2:
                raise RuntimeError("업데이트 ZIP의 폴더 구조가 올바르지 않습니다")
            relative = PurePosixPath(*path.parts[1:])
            if not source_member(relative):
                continue
            # Case folding also prevents ambiguous overwrite targets on Windows.
            key = str(relative).casefold()
            if key in seen:
                raise RuntimeError("업데이트 ZIP에 중복 파일이 있습니다")
            seen.add(key)
            total += member.file_size
            if member.file_size > MAX_ZIP_BYTES or total > MAX_SOURCE_BYTES:
                raise RuntimeError("압축 해제 용량이 허용 범위를 초과했습니다")
            with archive.open(member) as handle:
                content = handle.read(member.file_size + 1)
            if len(content) != member.file_size:
                raise RuntimeError("업데이트 파일을 끝까지 읽지 못했습니다")
            files[str(relative)] = content
    required = {"run_milkyway.py", "update_milkyway.py", "requirements-native.txt",
                "requirements-native.lock", "cloud_app/native_platform.py"}
    if not required.issubset(files):
        raise RuntimeError("실습 실행에 필요한 파일이 없는 업데이트입니다")
    return files


def check_target(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
        raise RuntimeError("업데이트 대상 경로가 올바르지 않습니다")
    target = root / relative
    current = target
    while current != root:
        if current.is_symlink():
            raise RuntimeError("코드 폴더의 심볼릭 링크에는 업데이트할 수 없습니다")
        current = current.parent
    if target.exists() and not target.is_file():
        raise RuntimeError("업데이트 파일 위치에 폴더가 있습니다")
    return target


def apply_sources(root, files, revision):
    # Private data, .env, .venv, runtime, backups and logs are never selected.
    files = dict(files)
    files[".milkyway-version.json"] = json.dumps(
        {"repository": REPOSITORY, "branch": BRANCH, "commit": revision}, indent=2
    ).encode()
    for relative in files:
        check_target(root, relative)
    staging = Path(tempfile.mkdtemp(prefix=".milkyway-update-", dir=root))
    changed, keep_staging = [], False
    try:
        for relative, content in files.items():
            prepared = staging / "new" / relative
            prepared.parent.mkdir(parents=True, exist_ok=True)
            prepared.write_bytes(content)
        for relative in files:
            target = check_target(root, relative)
            saved = staging / "old" / relative
            existed = target.exists()
            if existed:
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(target, saved)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / "new" / relative, target)
            changed.append((target, saved, existed))
    except BaseException:
        for target, saved, existed in reversed(changed):
            try:
                if existed:
                    os.replace(saved, target)
                else:
                    target.unlink(missing_ok=True)
            except OSError:
                keep_staging = True
        if keep_staging:
            raise RuntimeError("업데이트 복원이 끝나지 않았습니다. 보존된 폴더: " + staging.name) from None
        raise
    finally:
        if not keep_staging:
            shutil.rmtree(staging)


def main(root=None):
    root = installation_root(root or Path.cwd())
    sys.path.insert(0, str(root))
    from cloud_app.native_platform import flock, LOCK_EX, LOCK_NB, protect_directory
    if (root / "runtime").is_symlink():
        raise RuntimeError("개인 데이터 폴더의 심볼릭 링크에는 업데이트할 수 없습니다")
    protect_directory(root / "runtime")
    with ExitStack() as stack:
        for path in (root / ".setup.lock", root / "runtime/launcher.lock"):
            if path.is_symlink():
                raise RuntimeError("잠금 파일의 심볼릭 링크를 사용할 수 없습니다")
            lock = stack.enter_context(path.open("a+"))
            try:
                flock(lock, LOCK_EX | LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("밀키웨이나 설치 창이 실행 중입니다. Ctrl+C로 종료한 뒤 같은 업데이트 명령을 실행해 주세요") from None
        print("[1/2] GitHub 실습 브랜치의 최신 버전을 받습니다", flush=True)
        metadata = json.loads(download(
            f"https://api.github.com/repos/{REPOSITORY}/git/ref/heads/{BRANCH}", 1024 * 1024))
        obj = metadata.get("object") if isinstance(metadata, dict) else None
        revision = obj.get("sha", "") if isinstance(obj, dict) else ""
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise RuntimeError("GitHub 버전을 확인하지 못했습니다")
        payload = download(f"https://codeload.github.com/{REPOSITORY}/zip/{revision}", MAX_ZIP_BYTES)
        files = archive_sources(payload)
        print("[2/2] 코드를 업데이트합니다. 계좌·전략·연결 설정은 유지합니다", flush=True)
        apply_sources(root, files, revision)
    command = "py -3.14" if os.name == "nt" else "python3.14"
    print(f"업데이트 완료: {revision[:7]}\n다시 실행: {command} run_milkyway.py", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
        print("업데이트를 완료하지 못했습니다: " + str(error), file=sys.stderr)
        raise SystemExit(1)
