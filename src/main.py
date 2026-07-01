"""エントリポイント（03_ディレクトリ構成.md: src/main.py）。"""
import sys
from pathlib import Path

# プロジェクトルートをsys.pathへ追加する（Docker実行時はWORKDIRがルートである前提）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app.cli.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
