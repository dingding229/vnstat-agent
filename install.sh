#!/bin/bash
set -euo pipefail

# 配置参数
MASTER_URL由用户输入
INSTALL_DIR="/root/vnstat_client"

echo "开始安装 vnstat 和依赖..."

# 更新系统并安装 vnstat 和 Python
apt-get update
apt-get install -y vnstat python3 python3-pip

# 安装 Python 依赖
pip3 install requests schedule

# 提示用户输入
read -p "请输入主控端地址（例如 http://example.com:5000/receive_data）: " MASTER_URL"
read -p "请输入自定义服务器名称: " SERVER_NAME
read -p "请输入网络接口（例如 eth0）: " INTERFACE_NAME

# 创建安装目录
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 下载被控端脚本
curl -O https://raw.githubusercontent.com/dingding229/vnstat-agent/refs/heads/main/vnstat_client.py

# 创建配置文件
cat << EOF > config.json
{
    "server_name": "$SERVER_NAME",
    "interface": "$INTERFACE_NAME"
}
EOF

# 替换脚本中的 MASTER_URL
sed -i "s|MASTER_URL = \".*\"|MASTER_URL = \"$MASTER_URL\"|" vnstat_client.py

# 设置 vnstat 服务
vnstatd -d
systemctl enable vnstat
systemctl start vnstat

# 创建 systemd 服务
cat << EOF > /etc/systemd/system/vnstat-client.service
[Unit]
Description=vnStat Client Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/vnstat_client.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
systemctl enable vnstat-client
systemctl start vnstat-client

echo "安装完成！vnstat 客户端已启动。"
