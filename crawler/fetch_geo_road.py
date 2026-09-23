"""
S1-Fetch: OSM 路网数据采集
输出: data/raw/geo_road/
"""
import time

import requests

from config import get_output_dir, PROXIES

REGIONS = {"china": "https://download.geofabrik.de/asia/china-latest.osm.pbf"}


def fetch(output_dir):
    for region, url in REGIONS.items():
        filename = url.split("/")[-1]
        out = output_dir / filename
        # 已完整下载则跳过；存在 .part 文件则断点续传
        part = out.with_suffix(out.suffix + ".part")
        for retry in range(5):
            headers = None
            resume_from = part.stat().st_size if part.exists() else 0
            dl_headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}
            try:
                mode = "ab" if resume_from else "wb"
                with requests.get(url, stream=True, timeout=60,
                                  proxies=PROXIES, headers=dl_headers) as resp:
                    if resume_from and resp.status_code != 206:
                        # 服务器不支持续传，从头下载
                        resume_from = 0
                        mode = "wb"
                    total = int(resp.headers.get("content-length", 0)) + resume_from
                    downloaded = resume_from
                    print(f"[S1] 从 {downloaded/1024/1024:.0f} MB 处继续..." if resume_from
                          else f"[S1] 下载 {filename}...")
                    with open(part, mode) as f:
                        for chunk in resp.iter_content(chunk_size=8 * 1024 * 1024):
                            f.write(chunk); downloaded += len(chunk)
                            if total > 0:
                                print(f"\r  {downloaded/1024/1024:.0f}/{total/1024/1024:.0f} MB ({downloaded/total*100:.1f}%)", end="", flush=True)
                print()
                part.rename(out)
                print(f"[S1] 完成: {out.stat().st_size // 1024 // 1024} MB")
                break
            except Exception as e:
                print(f"\n[S1] 中断于 {part.stat().st_size/1024/1024:.0f} MB: {type(e).__name__} (第 {retry+1}/5 次重试)")
                time.sleep(5)
        else:
            raise RuntimeError(f"[S1] {filename} 下载多次失败，.part 文件已保留，可重跑续传")


if __name__ == "__main__":
    OUTPUT_DIR = get_output_dir("s1_geo_road")
    fetch(OUTPUT_DIR)
