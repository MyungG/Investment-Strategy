# -*- coding: utf-8 -*-
"""
market_scanner.py

\uc2dc\uac00\uc1a1 \uc0c1\uc704 100\uc885\ubaa9\uc758 \uc804\uc77c \uc678\uad6d\uc778/\uae30\uad00 \uc21c\ub9e4\uc218\ub97c \uacc4\uc0b0\ud574 \uce90\uc2dc \uc800\uc7a5.
\uc7a5\uc678 \uc2dc\uac04\uc5d0\ub3c4 \ub3d9\uc791 (\uc804\uc77c \ub370\uc774\ud130 \uae30\uc900).

\uc2e4\ud589:
    python market_scanner.py

\uc18c\uc694 \uc2dc\uac04: \uc57d 15\ucd08 (100\uc885\ubaa9 * 0.15\ucd08)
"""
import sys
from datetime import datetime
from kis_api import build_investor_ranking

sys.stdout.reconfigure(encoding="utf-8")


def main():
    print("=" * 55)
    print("  Market Scanner  (\uc678\uad6d\uc778/\uae30\uad00 \uc21c\ub9e4\uc218 \ub79c\ud0b9)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    print("\n\uc2dc\uac00\uc1a1 \uc0c1\uc704 100\uc885\ubaa9 \uc2a4\uce94 \uc911...\n")

    build_investor_ranking(n=100, top=20)

    print("\n\uc644\ub8cc! \uc6f9 \ub300\uc2dc\ubcf4\ub4dc\ub97c \uc0c8\ub85c\uace0\uce68\ud558\uba74 \ub370\uc774\ud130\uac00 \ud45c\uc2dc\ub429\ub2c8\ub2e4.")


if __name__ == "__main__":
    main()
