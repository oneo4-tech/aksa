#!/bin/sh
# PROTOTYPE demo: break the code on purpose, then see which tests notice.
cd "$(dirname "$0")"
cp discount.py /tmp/discount.bak
sed -i '' 's/(1 - percent \/ 100)/(1 + percent \/ 100)/' discount.py
echo "== AI tests vs broken code =="; uv run --with pytest pytest -q test_discount_ai.py 2>&1 | tail -1
echo "== Real tests vs broken code =="; uv run --with pytest pytest -q test_discount_real.py 2>&1 | tail -1
cp /tmp/discount.bak discount.py
