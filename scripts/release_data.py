"""
数据打包并上传到 GitHub Release

功能:
  1. 按数据类型分包（raw/cleaned/integrated）
  2. 超过 2GB 自动拆分
  3. 每个包作为独立 Release 上传

用法:
  python scripts/release_data.py --repo my-org/my-repo
  python scripts/release_data.py --repo my-org/my-repo --dry-run
  python scripts/release_data.py --repo my-org/my-repo --tag v0.1

GitHub 限制: 单个 Release 附件最大 2 GB
"""
import argparse
import math
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RELEASE_DIR = PROJECT_ROOT / "release"

# GitHub 单文件限制
MAX_RELEASE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


def get_dir_size(d):
    """计算目录总大小"""
    if not d.exists():
        return 0
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())


def get_dir_file_count(d):
    """计算目录文件数"""
    if not d.exists():
        return 0
    return sum(1 for f in d.rglob("*") if f.is_file())


def split_and_compress(data_subdir, chunk_prefix, max_size=MAX_RELEASE_SIZE):
    """将目录打包，超过 max_size 自动拆分"""
    src_dir = DATA_DIR / data_subdir
    if not src_dir.exists() or get_dir_size(src_dir) == 0:
        print(f"  {data_subdir}: 目录为空或不存在，跳过")
        return []

    total_size = get_dir_size(src_dir)
    total_files = get_dir_file_count(src_dir)
    print(f"  {data_subdir}: {total_files} 文件, {total_size / 1024 / 1024:.1f} MB")

    # 收集所有文件并按大小排序（大文件优先）
    all_files = sorted(
        [(f, f.stat().st_size) for f in src_dir.rglob("*") if f.is_file()],
        key=lambda x: -x[1]
    )

    chunks = []
    current_chunk = []
    current_size = 0

    for f, size in all_files:
        if current_size + size > max_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
        current_chunk.append((f, size))
        current_size += size

    if current_chunk:
        chunks.append(current_chunk)

    # 压缩每个 chunk
    zip_paths = []
    for i, chunk in enumerate(chunks):
        chunk_size = sum(s for _, s in chunk)
        suffix = f"_part{i + 1}" if len(chunks) > 1 else ""
        zip_name = f"{chunk_prefix}{suffix}.zip"
        zip_path = RELEASE_DIR / zip_name

        print(f"  压缩 {zip_name} ({chunk_size / 1024 / 1024:.1f} MB, {len(chunk)} 文件)...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f, _ in chunk:
                arcname = f"data/{data_subdir}/{f.relative_to(DATA_DIR / data_subdir)}"
                zf.write(f, arcname)

        actual_size = zip_path.stat().st_size
        print(f"    → {zip_path.name} ({actual_size / 1024 / 1024:.1f} MB)")
        zip_paths.append(zip_path)

    return zip_paths


def check_gh_cli():
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_repo(repo_name):
    """检查 GitHub 仓库是否存在"""
    result = subprocess.run(["gh", "repo", "view", repo_name, "--json", "name"],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"仓库已存在: {repo_name}")
        return True
    print(f"错误: 仓库不存在: {repo_name}")
    print(f"  请先在 GitHub 上创建仓库: https://github.com/new")
    return False


def create_release(repo_name, tag, title, notes, zip_paths):
    """创建 Release 并上传多个附件"""
    args = ["gh", "release", "create", tag, "--repo", repo_name,
            "--title", title, "--notes", notes]
    for zp in zip_paths:
        args.append(str(zp))

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Release 创建成功: {tag}")
        for zp in zip_paths:
            print(f"    附件: {zp.name} ({zp.stat().st_size / 1024 / 1024:.1f} MB)")
        return True
    else:
        print(f"  Release 创建失败: {result.stderr[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="数据打包并上传到 GitHub Release")
    parser.add_argument("--repo", required=True, help="GitHub 仓库名 (如 my-org/my-repo)")
    parser.add_argument("--tag", default=None, help="版本号 (默认: v{日期})")
    parser.add_argument("--dry-run", action="store_true", help="仅打包不上传")
    args = parser.parse_args()

    tag = args.tag or f"v{datetime.now().strftime('%Y%m%d')}"
    repo_name = args.repo

    print("=" * 60)
    print(f"数据打包 Release: {tag}")
    print("=" * 60)

    # 1. 打包三个目录
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    all_zips = []

    configs = [
        ("raw", "data_raw"),
        ("cleaned", "data_cleaned"),
        ("integrated", "data_integrated"),
    ]

    for subdir, prefix in configs:
        zips = split_and_compress(subdir, prefix)
        all_zips.extend(zips)

    if not all_zips:
        print("\n没有可打包的数据")
        return

    total_size = sum(z.stat().st_size for z in all_zips)
    print(f"\n共 {len(all_zips)} 个包, 总计 {total_size / 1024 / 1024:.1f} MB")

    if args.dry_run:
        print("\n[dry-run] 仅打包，不上传到 GitHub")
        for z in all_zips:
            print(f"  {z.name}: {z.stat().st_size / 1024 / 1024:.1f} MB")
        return

    # 2. 检查 GitHub CLI
    if not check_gh_cli():
        print("\n错误: 请先安装 GitHub CLI 并登录:")
        print("  安装: https://cli.github.com/")
        print("  登录: gh auth login")
        return

    # 3. 检查仓库是否存在
    if not check_repo(repo_name):
        return

    # 4. 创建 Release（每个 zip 一个 Release）
    for zp in all_zips:
        release_tag = f"{tag}-{zp.stem}"
        title = f"数据发布: {zp.stem}"
        size_mb = zp.stat().st_size / 1024 / 1024
        notes = f"## {zp.stem}\n\n大小: {size_mb:.1f} MB\n\n发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        create_release(repo_name, release_tag, title, notes, [zp])

    print("\n全部完成！")


if __name__ == "__main__":
    main()
