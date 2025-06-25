#!/bin/bash

set -e

echo "🌐 正在安装 vnstat-agent ..."

# 安装依赖
apt update && apt install -y curl python3 python3-pip vnstat jq

# 启动 vnstat（如果未启动）
systemctl enable --now vnstat

# 安装 Python 模块
pip3 install requests

# 设置目录
INSTALL_DIR="/opt"
SCRIPT_URL="https://raw.githubusercontent.com/YOUR_GITHUB_USER/vnstat-agent/main/vnstat_agent.py"

# 下载主脚本
curl -o ${INSTALL_DIR}/vnstat_agent.py -sSL "$SCRIPT_URL"
chmod +x ${INSTALL_DIR}/vnstat_agent.py

# 获取主控端地址和自定义名称
read -p "请输入主控端地址（例如：http://123.123.123.123:5000/report）: " report_url
read -p "请输入该服务器的自定义名称（例如：日本节点1 或 hk-cn2）: " custom_name

# 写入配置
echo "REPORT_URL=\"$report_url\"" > ${INSTALL_DIR}/vnstat_agent.env
echo "CUSTOM_NAME=\"$custom_name\"" >> ${INSTALL_DIR}/vnstat_agent.env

# 设置定时任务（每小时执行）
(crontab -l 2>/dev/null; echo "0 * * * * /usr/bin/python3 /opt/vnstat_agent.py") | crontab -

echo "✅ 安装完成！已设置每小时自动上报"
