#!/bin/zsh
set -eu
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
cd -- "${0:A:h}"
if ! command -v python3 >/dev/null; then
  print "Python 3를 먼저 설치해 주세요. 설치 안내는 docs/PERSONAL_RECOVERY.md에 있습니다."
  read -r "?Enter를 누르면 닫습니다."
  exit 1
fi
if ! python3 deploy/local_control.py start; then
  read -r "?위 안내를 확인한 뒤 Enter를 누르면 닫습니다."
  exit 1
fi
