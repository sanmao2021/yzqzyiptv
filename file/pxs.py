# 导入必要的Python模块
import json  # 用于处理JSON数据
import urllib.request  # 用于发送HTTP请求
from urllib.error import URLError, HTTPError  # 用于处理URL错误

# 定义基础URL（像素体育网站的域名）
BASE = "https://pixelsport.tv"
# 构建API端点URL - 获取直播事件
API_EVENTS = f"{BASE}/backend/liveTV/events"
# 构建API端点URL - 获取滑块内容（直播频道）
API_SLIDERS = f"{BASE}/backend/slider/getSliders"
# 输出文件名 - 生成的M3U播放列表文件
OUTPUT_FILE = "Pixelsports.m3u"

# 默认直播TV的LOGO图片URL
LIVE_TV_LOGO = "https://pixelsport.tv/static/media/PixelSportLogo.1182b5f687c239810f6d.png"
# 默认直播TV的TVG-ID（EPG标识符）
LIVE_TV_ID = "24.7.Dummy.us"

# VLC播放器需要的User-Agent头部
VLC_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# VLC播放器需要的Referer头部
VLC_REFERER = f"{BASE}/"
# VLC播放器需要的ICY元数据头部
VLC_ICY = "1"

# 联赛/体育类型信息映射表，包含：TVG-ID、LOGO URL、分组名称
LEAGUE_INFO = {
    "NFL": ("NFL.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Maxx.png", "NFL"),
    "MLB": ("MLB.Baseball.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Baseball3.png", "MLB"),
    "NHL": ("NHL.Hockey.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Hockey2.png", "NHL"),
    "NBA": ("NBA.Basketball.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Basketball-2.png", "NBA"),
    "NASCAR": ("Racing.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Motorsports2.png", "NASCAR"),
    "UFC": ("UFC.Fight.Pass.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/CombatSports2.png", "UFC"),
    "SOCCER": ("Soccer.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Soccer.png", "Soccer"),
    "BOXING": ("PPV.EVENTS.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Combat-Sports.png", "Boxing"),
}


def fetch_json(url):
    """从指定URL获取JSON数据（带请求头部）"""
    # 定义请求头部，模拟VLC播放器
    headers = {
        "User-Agent": VLC_USER_AGENT,
        "Referer": VLC_REFERER,
        "Accept": "*/*",
        "Connection": "close",
        "Icy-MetaData": VLC_ICY,
    }
    # 创建请求对象
    req = urllib.request.Request(url, headers=headers)
    # 发送请求并读取响应
    with urllib.request.urlopen(req, timeout=10) as resp:
        # 解析JSON响应数据
        return json.loads(resp.read().decode("utf-8"))


def collect_links(obj, prefix=""):
    """从对象中收集有效的流媒体链接"""
    links = []  # 存储链接的列表
    if not obj:  # 如果对象为空，返回空列表
        return links
    # 遍历可能的服务器URL字段（server1URL, server2URL, server3URL）
    for i in range(1, 4):
        # 构建字段名，如果提供了前缀则添加前缀
        key = f"{prefix}server{i}URL" if prefix else f"server{i}URL"
        # 从对象中获取URL值
        url = obj.get(key)
        # 如果URL存在且不是"null"（字符串），则添加到列表
        if url and url.lower() != "null":
            links.append(url)
    return links


def get_league_info(name):
    """根据联赛名称返回相关信息元组：(tvg-id, logo, group name)"""
    # 遍历联赛信息映射表
    for key, (tvid, logo, group) in LEAGUE_INFO.items():
        # 如果联赛名称中包含关键字（不区分大小写）
        if key.lower() in name.lower():
            return tvid, logo, group  # 返回匹配的信息
    # 如果没有匹配，返回默认信息
    return ("Pixelsports.Dummy.us", LIVE_TV_LOGO, "Pixelsports")


def build_m3u(events, sliders):
    """构建M3U播放列表文本"""
    lines = ["#EXTM3U"]  # M3U文件头部

    # 处理事件（直播赛事）
    for ev in events:
        # 获取比赛名称，如果没有则使用"Unknown Event"
        title = ev.get("match_name", "Unknown Event").strip()
        # 获取队伍LOGO，如果没有则使用默认LOGO
        logo = ev.get("competitors1_logo", LIVE_TV_LOGO)
        # 从嵌套结构中获取联赛/体育类型名称
        league = ev.get("channel", {}).get("TVCategory", {}).get("name", "Sports")
        # 获取联赛相关信息
        tvid, group_logo, group_display = get_league_info(league)
        # 从事件数据中收集流媒体链接
        links = collect_links(ev.get("channel", {}))
        if not links:  # 如果没有有效链接，跳过此事件
            continue

        # 为每个链接添加M3U条目
        for link in links:
            # 添加EXTINF行：包含元数据和标题
            lines.append(f'#EXTINF:-1 tvg-id="{tvid}" tvg-logo="{logo}" group-title="Pixelsports - {group_display}",{title}')
            # 添加VLC播放器选项
            lines.append(f"#EXTVLCOPT:http-user-agent={VLC_USER_AGENT}")
            lines.append(f"#EXTVLCOPT:http-referrer={VLC_REFERER}")
            lines.append(f"#EXTVLCOPT:http-icy-metadata={VLC_ICY}")
            lines.append(link)  # 添加流媒体链接

    # 处理滑块内容（直播频道）
    for ch in sliders:
        # 获取频道标题
        title = ch.get("title", "Live Channel").strip()
        # 获取直播TV数据
        live = ch.get("liveTV", {})
        # 使用默认LOGO
        logo = LIVE_TV_LOGO  
        # 从直播数据中收集链接（注意：这里使用了前缀"live"）
        links = collect_links(live, "live")
        if not links:  # 如果没有有效链接，跳过此频道
            continue

        # 为每个链接添加M3U条目
        for link in links:
            # 添加EXTINF行：使用固定的TVG-ID和分组
            lines.append(f'#EXTINF:-1 tvg-id="{LIVE_TV_ID}" tvg-logo="{logo}" group-title="Pixelsports - Live TV",{title}')
            # 添加VLC播放器选项
            lines.append(f"#EXTVLCOPT:http-user-agent={VLC_USER_AGENT}")
            lines.append(f"#EXTVLCOPT:http-referrer={VLC_REFERER}")
            lines.append(f"#EXTVLCOPT:http-icy-metadata={VLC_ICY}")
            lines.append(link)  # 添加流媒体链接

    # 将所有行连接为字符串，用换行符分隔
    return "\n".join(lines)


def main():
    """主函数：执行整个脚本逻辑"""
    try:
        print("[*] Fetching PixelSport data...")  # 开始获取数据
        # 获取事件数据
        events_data = fetch_json(API_EVENTS)
        # 从响应中提取events列表，如果响应是字典类型
        events = events_data.get("events", []) if isinstance(events_data, dict) else []
        # 获取滑块数据
        sliders_data = fetch_json(API_SLIDERS)
        # 从响应中提取data列表，如果响应是字典类型
        sliders = sliders_data.get("data", []) if isinstance(sliders_data, dict) else []

        # 构建M3U播放列表
        playlist = build_m3u(events, sliders)
        # 将播放列表写入文件
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(playlist)

        # 打印成功信息
        print(f"[+] Saved: {OUTPUT_FILE} ({len(events)} events + {len(sliders)} live channels)")
    except Exception as e:
        # 如果发生错误，打印错误信息
        print(f"[!] Error: {e}")


# 如果此脚本作为主程序运行，则执行main函数
if __name__ == "__main__":
    main()
