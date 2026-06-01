#!/usr/bin/env bash
# 切换成「攻击者」形态：把 demo_attacker/ 的内容提升为整个仓库根目录。
# 注意：会清空当前目录（保留 .git），误删可重新 git clone。
set -e

cp -rf demo_attacker /tmp/demo_attacker     # 先备份到 /tmp
find . -maxdepth 1 ! -name . ! -name .git -exec rm -rf {} +   # 清空（留下 .git）
mv /tmp/demo_attacker ./            # 把 demo_attacker 复制回来
rm -rf /tmp/demo_attacker

rm -rf make-it-for-*.sh    # 删除这个脚本自己