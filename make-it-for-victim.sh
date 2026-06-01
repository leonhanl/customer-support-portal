#!/usr/bin/env bash
# 切换成「受害者」形态：去掉攻击演示，只留干净的应用本体。
set -e

rm -rf demo_attacker README.md          # 删掉攻击演示目录和当前 README
rm -rf tests/test_attack_chain.py  # 删掉攻击链测试
mv README_AppOnly.md README.md    # 用纯应用版 README 替换


rm -rf make-it-for-*.sh    # 删除这个脚本自己