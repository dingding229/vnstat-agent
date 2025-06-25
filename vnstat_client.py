#!/usr/bin/env python3
import subprocess
import json
import requests
import schedule
import time
import os

# 配置
MASTER_URL = "http://<主控端IP或域名>:5000/receive_data"  # 主控端接收数据的URL
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """加载配置文件，如果不存在则创建"""
    if not os.path.exists(CONFIG_FILE):
        server_name = input("请输入自定义服务器名称: ")
        interface = input("请输入网络接口名称 (例如 eth0): ")
        config = {
            "server_name": server_name,
            "interface": interface
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    else:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    return config

# 加载配置
config = load_config()
SERVER_NAME = config["server_name"]
INTERFACE = config["interface"]

def get_vnstat_data():
    """获取 vnstat 的每日、每周、每月统计数据"""
    try:
        # 获取每日数据
        daily = subprocess.check_output(["vnstat", "-i", INTERFACE, "-d", "--json"]).decode()
        daily_data = json.loads(daily)

        # 获取每月数据
        monthly = subprocess.check_output(["vnstat", "-i", INTERFACE, "-m", "--json"]).decode()
        monthly_data = json.loads(monthly)

        # 每周数据需要从每日数据中累加最近7天
        daily_traffic = daily_data["interfaces"][0]["traffic"]["days"][:7]
        weekly_rx = sum(day["rx"] for day in daily_traffic) / 1024 / 1024  # MB
        weekly_tx = sum(day["tx"] for day in daily_traffic) / 1024 / 1024  # MB

        # 获取最新一天和最新一月的数据
        latest_day = daily_data["interfaces"][0]["traffic"]["days"][0]
        latest_month = monthly_data["interfaces"][0]["traffic"]["months"][0]

        return {
            "server_name": SERVER_NAME,
            "daily": {
                "date": f"{latest_day['date']['year']}-{latest_day['date']['month']}-{latest_day['date']['day']}",
                "rx_mb": latest_day["rx"] / 1024 / 1024,
                "tx_mb": latest_day["tx"] / 1024 / 1024
            },
            "weekly": {
                "rx_mb": weekly_rx,
                "tx_mb": weekly_tx
            },
            "monthly": {
                "date": f"{latest_month['date']['year']}-{latest_month['date']['month']}",
                "rx_mb": latest_month["rx"] / 1024 / 1024,
                "tx_mb": latest_month["tx"] / 1024 / 1024
            }
        }
    except Exception as e:
        print(f"Error collecting vnstat data: {e}")
        return None

def send_data_to_master(data):
    """将数据发送到主控端"""
    try:
        response = requests.post(MASTER_URL, json=data)
        if response.status_code == 200:
            print("Data sent successfully")
        else:
            print(f"Failed to send data: {response.status_code}")
    except Exception as e:
        print(f"Error sending data: {e}")

def job():
    """定时任务：收集并发送数据"""
    data = get_vnstat_data()
    if data:
        send_data_to_master(data)

# 定时任务：每小时发送数据
schedule.every().hour.at(":00").do(job)  # 每小时整点运行

if __name__ == "__main__":
    print("Starting vnstat client...")
    while True:
        schedule.run_pending()
        time.sleep(60)
