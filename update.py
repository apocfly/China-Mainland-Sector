import os
import re
import shutil
from pathlib import Path


def detect_encoding(file_path):
    """
    检测文件编码
    """
    encodings = ['gbk', 'gb2312', 'gb18030', 'utf-8', 'latin-1']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue

    # 如果所有编码都失败，返回默认编码
    return 'gbk'


def remove_special_pattern(content):
    """
    移除特定的多行注释模式
    """
    # 匹配包含大量全角空格、分号和＃号的模式
    pattern = r'[\s;]*[　;]*[　\s;]*＃[＃\s;]*[　\s;]*'
    cleaned_content = re.sub(pattern, '', content)
    return cleaned_content


def replace_keywords(content):
    """
    替换特定的关键词
    """
    original_content = content

    # 先替换长的字符串，避免重叠替换问题
    content = content.replace('China Sector Package Studio', 'Flyleague-Collection')
    content = content.replace('China Sector Package', 'China-Mainland-Sector')

    # 记录替换详情
    changes = []
    if original_content != content:
        if 'China Sector Package Studio' in original_content:
            changes.append("替换 'China Sector Package Studio' 为 'Flyleague-Collection'")
        if 'China Sector Package' in original_content:
            changes.append("替换 'China Sector Package' 为 'China-Mainland-Sector'")

    return content, changes


def extract_info_section(content, file_path):
    """
    从内容中提取[INFO]到[AIRPORT]之间的部分（不包括[AIRPORT]）
    """
    # 使用正则表达式匹配[INFO]到[AIRPORT]之间的内容
    pattern = r'\[INFO\]\s*(.*?)\s*\[AIRPORT\]'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        info_content = match.group(1).strip()
        print(f"  从 {file_path} 提取的 [INFO] 内容:")
        print(f"  --- 开始 ---")
        print(info_content)
        print(f"  --- 结束 ---")
        return info_content
    else:
        print(f"  警告: 在 {file_path} 中未找到 [INFO] 到 [AIRPORT] 的标记")
        return None


def find_sct_files(base_path):
    """
    在base_path及其子目录中查找所有的.sct文件
    """
    sct_files = {}

    for sct_file in Path(base_path).rglob('*.sct'):
        # 跳过Sectors目录中的文件
        if 'Sectors' in str(sct_file):
            continue

        # 获取文件名（不含扩展名）
        file_stem = sct_file.stem
        sct_files[file_stem] = sct_file
        print(f"找到源文件: {sct_file} -> {file_stem}")

    return sct_files


def update_sct_with_info(source_sct_files, target_sectors_dir, target_dirs):
    """
    使用源sct文件中的[INFO]到[AIRPORT]内容更新目标sct文件
    """
    updated_count = 0

    for dir_name in target_dirs:
        target_sct_path = target_sectors_dir / dir_name / f"{dir_name}.sct"

        # 检查目标sct文件是否存在
        if not target_sct_path.exists():
            print(f"警告: 目标文件 {target_sct_path} 不存在")
            continue

        # 查找对应的源sct文件
        source_key = dir_name
        if dir_name == 'FSS':
            source_key = 'PRC'  # FSS 对应的源文件是 PRC.sct

        if source_key in source_sct_files:
            source_sct_path = source_sct_files[source_key]

            try:
                print(f"\n处理 {dir_name}.sct:")
                print(f"  源文件: {source_sct_path}")
                print(f"  目标文件: {target_sct_path}")

                # 读取源sct文件内容
                source_encoding = detect_encoding(source_sct_path)
                with open(source_sct_path, 'r', encoding=source_encoding) as f:
                    source_content = f.read()

                # 提取[INFO]到[AIRPORT]之间的内容
                info_content = extract_info_section(source_content, source_sct_path)

                if info_content:
                    # 读取目标sct文件内容
                    target_encoding = detect_encoding(target_sct_path)
                    with open(target_sct_path, 'r', encoding=target_encoding) as f:
                        target_content = f.read()

                    # 替换目标文件中的[INFO]到[AIRPORT]内容
                    pattern = r'(\[INFO\]\s*).*?(\s*\[AIRPORT\])'
                    replacement = r'\1' + info_content + r'\2'

                    if re.search(pattern, target_content, re.DOTALL):
                        updated_content = re.sub(pattern, replacement, target_content, flags=re.DOTALL)

                        # 写回目标文件
                        with open(target_sct_path, 'w', encoding=target_encoding) as f:
                            f.write(updated_content)

                        updated_count += 1
                        print(f"  成功更新 {target_sct_path} 的 [INFO] 部分")
                    else:
                        print(f"  警告: 目标文件 {target_sct_path} 中未找到 [INFO] 到 [AIRPORT] 的标记")
                else:
                    print(f"  警告: 源文件 {source_sct_path} 中未找到 [INFO] 到 [AIRPORT] 的内容")

            except Exception as e:
                print(f"  处理文件 {target_sct_path} 时出错: {e}")
        else:
            print(f"警告: 未找到 {dir_name} 对应的源 sct 文件 (查找键: {source_key})")

    return updated_count


def process_files():
    """
    主处理函数
    """
    # 定义Sectors目录路径
    sectors_dir = Path('Sectors')

    # 定义目标目录列表和特殊映射
    target_dirs = ['FSS', 'ZBPE', 'ZGZU', 'ZHWH', 'ZJSA', 'ZLHW', 'ZPKM', 'ZSHA', 'ZWUQ', 'ZYSH']

    # 特殊文件映射：PRC -> FSS
    special_mappings = {
        'PRC': 'FSS'
    }

    # 确保所有目标目录存在
    for dir_name in target_dirs:
        target_dir = sectors_dir / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)

    # 统计信息
    total_files = 0
    processed_files = 0
    moved_files = 0
    renamed_files = 0

    # 遍历Sectors目录下的所有.sct和.ese文件
    for file_path in sectors_dir.glob('*.*'):
        if file_path.suffix.lower() in ['.sct', '.ese']:
            total_files += 1
            print(f"\n--- 处理文件: {file_path.name} ---")

            try:
                # 检测文件编码
                encoding = detect_encoding(file_path)
                print(f"  检测到编码: {encoding}")

                # 读取文件内容
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()

                original_length = len(content)

                # 处理内容
                content = remove_special_pattern(content)
                content, keyword_changes = replace_keywords(content)

                # 记录变化
                removed_pattern = original_length - len(content)
                if removed_pattern > 0:
                    print(f"  移除了 {removed_pattern} 个特殊模式字符")

                if keyword_changes:
                    for change in keyword_changes:
                        print(f"  {change}")
                else:
                    print("  未找到需要替换的关键词")

                # 写回文件（使用相同编码）
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)

                processed_files += 1

                # 处理文件重命名和移动
                file_stem = file_path.stem  # 获取文件名（不含扩展名）

                # 检查是否需要特殊重命名
                new_file_stem = file_stem
                if file_stem in special_mappings:
                    new_file_stem = special_mappings[file_stem]
                    new_file_path = file_path.with_name(f"{new_file_stem}{file_path.suffix}")
                    file_path.rename(new_file_path)
                    file_path = new_file_path
                    renamed_files += 1
                    print(f"  重命名文件: {file_stem}{file_path.suffix} -> {new_file_stem}{file_path.suffix}")

                # 移动文件到对应的目录
                if new_file_stem in target_dirs:
                    target_path = sectors_dir / new_file_stem / file_path.name
                    shutil.move(str(file_path), str(target_path))
                    moved_files += 1
                    print(f"  移动文件到: {target_path}")
                else:
                    print(f"  警告: 文件 {file_path.name} 没有对应的目标目录")

            except Exception as e:
                print(f"  处理文件 {file_path} 时出错: {e}")

    # 更新sct文件的[INFO]部分
    print(f"\n--- 开始更新.sct文件的[INFO]部分 ---")

    # 查找所有源sct文件（在update.py同级目录及其子目录中，但不包括Sectors目录）
    base_path = Path('.')  # update.py所在目录
    source_sct_files = find_sct_files(base_path)
    print(f"找到 {len(source_sct_files)} 个源.sct文件")

    # 更新目标sct文件
    updated_count = update_sct_with_info(source_sct_files, sectors_dir, target_dirs)

    # 打印统计信息
    print(f"\n=== 处理完成 ===")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {processed_files}")
    print(f"重命名文件: {renamed_files}")
    print(f"移动文件: {moved_files}")
    print(f"更新.sct文件的[INFO]部分: {updated_count}")


def main():
    """
    程序主入口
    """
    print("开始处理Sectors目录下的文件...")

    # 检查Sectors目录是否存在
    if not Path('Sectors').exists():
        print("错误: Sectors目录不存在!")
        return

    process_files()


if __name__ == "__main__":
    main()