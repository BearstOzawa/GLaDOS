#!/usr/bin/env python3
"""GLaDOS 自动签到脚本"""

import os
import time
import random
import datetime
import requests
from dotenv import load_dotenv


# 配置常量
CHECKIN_URL = "https://glados.cloud/api/user/checkin"
STATUS_URL = "https://glados.cloud/api/user/status"
REQUEST_TIMEOUT = 15

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G9750) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
]


def get_beijing_time():
    """获取北京时间"""
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)


def log(message):
    """打印带时间戳的日志"""
    timestamp = get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
    print("[{}] {}".format(timestamp, message))


def translate_checkin_message(raw_message):
    """翻译签到结果消息"""
    translations = {
        "Please Try Tomorrow": "签到失败，请明天再试 🤖",
        "Checkin Repeats! Please Try Tomorrow": "重复签到，请明天再试 🔁",
    }
    
    if raw_message in translations:
        return translations[raw_message]
    
    if "Checkin! Got" in raw_message:
        try:
            points = raw_message.split("Got ")[1].split(" Points")[0]
            return "签到成功，获得 {} 积分 🎉".format(points)
        except IndexError:
            pass
    
    return "未知结果: {} ❓".format(raw_message)


def generate_headers(cookie):
    """生成请求头"""
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": cookie,
        "Origin": "https://glados.cloud",
        "Referer": "https://glados.cloud/console/checkin",
        "User-Agent": random.choice(USER_AGENTS),
    }


def format_days(days_str):
    """格式化剩余天数"""
    try:
        days = float(days_str)
        return str(int(days)) if days.is_integer() else "{:.2f}".format(days)
    except (ValueError, TypeError):
        return str(days_str)


def get_proxy_config():
    """获取代理配置"""
    http_proxy = os.getenv("HTTP_PROXY", "")
    https_proxy = os.getenv("HTTPS_PROXY", "")
    
    if http_proxy or https_proxy:
        return {"http": http_proxy, "https": https_proxy}
    return None


def check_account_status(email, cookie, proxy):
    """
    检查账户状态
    返回: (状态消息, 是否成功)
    """
    headers = generate_headers(cookie)
    
    try:
        response = requests.get(
            STATUS_URL, 
            headers=headers, 
            proxies=proxy, 
            timeout=REQUEST_TIMEOUT
        )
        log("  [DEBUG] 状态API响应码: {}".format(response.status_code))
        log("  [DEBUG] 响应内容: {}".format(response.text[:500] if response.text else '空'))
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            return "API 错误: {}".format(data.get("message", "未知错误")), False
        
        left_days = format_days(data["data"]["leftDays"])
        return "剩余 {} 天 🗓️".format(left_days), True
        
    except requests.Timeout:
        return "请求超时 ⏱️", False
    except requests.RequestException as e:
        return "网络错误: {}".format(e), False
    except (KeyError, ValueError) as e:
        return "解析错误: {}".format(e), False


def checkin(email, cookie, proxy):
    """
    执行签到
    返回: (签到消息, 是否成功)
    """
    headers = generate_headers(cookie)
    payload = {"token": "glados.cloud"}
    
    try:
        response = requests.post(
            CHECKIN_URL,
            headers=headers,
            json=payload,
            proxies=proxy,
            timeout=REQUEST_TIMEOUT
        )
        log("  [DEBUG] 签到API响应码: {}".format(response.status_code))
        log("  [DEBUG] 响应内容: {}".format(response.text[:500] if response.text else '空'))
        
        response.raise_for_status()
        data = response.json()
        
        raw_message = data.get("message", "")
        translated = translate_checkin_message(raw_message)
        success = "成功" in translated or "重复" in translated
        return translated, success
        
    except requests.Timeout:
        return "请求超时 ⏱️", False
    except requests.RequestException as e:
        return "网络错误: {}".format(e), False
    except ValueError:
        status = response.status_code if response else "N/A"
        content = response.text[:100] if response and response.text else "空响应"
        return "解析失败 (HTTP {}): {}".format(status, content), False


def load_accounts():
    """从环境变量加载账号列表"""
    accounts = []
    i = 1
    
    while True:
        email = os.getenv("GLADOS_EMAIL_{}".format(i))
        cookie = os.getenv("GLADOS_COOKIE_{}".format(i))
        
        if not email or not cookie:
            break
            
        accounts.append((email, cookie))
        i += 1
    
    return accounts


def process_account(email, cookie, proxy):
    """处理单个账号的签到和状态检查"""
    log("正在处理账号: {}".format(email))
    
    # 签到
    checkin_msg, checkin_ok = checkin(email, cookie, proxy)
    log("  签到: {}".format(checkin_msg))
    
    # 获取状态
    status_msg, status_ok = check_account_status(email, cookie, proxy)
    log("  状态: {}".format(status_msg))
    
    return {
        "email": email,
        "checkin": checkin_msg,
        "checkin_ok": checkin_ok,
        "status": status_msg,
        "status_ok": status_ok,
    }


def main():
    """主函数"""
    load_dotenv()
    
    log("=" * 50)
    log("GLaDOS 自动签到脚本启动")
    log("=" * 50)
    
    # 加载账号
    accounts = load_accounts()
    if not accounts:
        log("❌ 未找到账号信息，请检查环境变量配置")
        log("   需要设置 GLADOS_EMAIL_1, GLADOS_COOKIE_1 等")
        return
    
    log("📋 共加载 {} 个账号".format(len(accounts)))
    
    # 获取代理配置
    proxy = get_proxy_config()
    if proxy:
        log("🌐 使用代理: {}".format(proxy.get("http", "N/A")))
    
    # 处理每个账号
    results = []
    for idx, (email, cookie) in enumerate(accounts, 1):
        if idx > 1:
            delay = random.randint(3, 8)
            log("⏳ 等待 {} 秒...".format(delay))
            time.sleep(delay)
        
        result = process_account(email, cookie, proxy)
        results.append(result)
    
    # 汇总结果
    log("=" * 50)
    log("📊 签到结果汇总")
    log("-" * 50)
    
    success_count = sum(1 for r in results if r["checkin_ok"])
    for r in results:
        icon = "✅" if r["checkin_ok"] else "❌"
        log("{} {}: {} | {}".format(icon, r["email"], r["checkin"], r["status"]))
    
    log("-" * 50)
    log("完成: {}/{} 个账号签到成功".format(success_count, len(results)))
    log("=" * 50)


if __name__ == "__main__":
    main()
