#!/usr/bin/env python3
import json
import subprocess
import requests
import socket
import os
from datetime import datetime

# 读取主控地址
ENV_PATH = "/opt/vnstat_agent.env"
if not os.path.exists(ENV_PATH):
    print("❌ 缺少配置文件 /opt/vnstat_agent.env")
    exit(1)

exec(open(ENV_PATH).read())
if not REPORT_URL:
    print("❌ REPORT_URL 未设置")
    exit(1)

# 获取当前主机名
hostname = socket.gethostname()


def get_vnstat_json():
    try:
        result = subprocess.run(["vnstat", "--json"], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print("❌ 获取 vnstat 数据失败:", e)
        return None


def extract_latest_traffic(data):
    try:
        iface = data["interfaces"][0]
        name = iface["name"]
        traffic = iface["traffic"]

        def sum_latest(arr):
            if not arr:
                return 0, 0
            latest = arr[-1]
            return latest.get("rx", 0), latest.get("tx", 0)

        rx_day, tx_day = sum_latest(traffic.get("day", []))
        rx_week, tx_week = sum_latest(traffic.get("week", []))
        rx_month, tx_month = sum_latest(traffic.get("month", []))

        def to_gb(mb): return round(mb / 1024, 2)

        return {
            "interface": name,
            "daily": {"rx_gb": to_gb(rx_day), "tx_gb": to_gb(tx_day)},
            "weekly": {"rx_gb": to_gb(rx_week), "tx_gb": to_gb(tx_week)},
            "monthly": {"rx_gb": to_gb(rx_month), "tx_gb": to_gb(tx_month)}
        }
    except Exception as e:
        print("❌ 提取流量数据失败:", e)
        return None


def report_to_controller(payload):
    try:
        print(f"🛰️ 正在上报到 {REPORT_URL}")
        print("📦 上报内容：")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

        resp = requests.post(REPORT_URL, json=payload, timeout=10)
        print("✅ 上报结果：", resp.status_code, resp.text)
    except Exception as e:
        print("❌ 上报失败：", e)


def main():
    vnstat_data = get_vnstat_json()
    if not vnstat_data:
        return

    traffic_summary = extract_latest_traffic(vnstat_data)
    if not traffic_summary:
        return

    payload = {
        "hostname": hostname,
        "timestamp": datetime.utcnow().isoformat(),
        "vnstat": vnstat_data,
        "summary": traffic_summary
    }

    report_to_controller(payload)


if __name__ == "__main__":
    main()
