import sys
import os
from collections import defaultdict


def parse_fasta(fasta_path):
    """解析FASTA文件，返回序列字典"""
    sequences = {}
    current_id = None
    current_seq = []

    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith('>'):
                # 保存上一个序列
                if current_id is not None:
                    sequences[current_id] = ''.join(current_seq)

                # 开始新序列
                current_id = line[1:].split()[0]  # 只取第一个空格前的部分作为ID
                current_seq = []
            else:
                current_seq.append(line)

        # 保存最后一个序列
        if current_id is not None:
            sequences[current_id] = ''.join(current_seq)

    return sequences


def parse_gff(gff_path):
    """解析GFF文件，返回注释信息"""
    annotations = []

    with open(gff_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 9:
                continue

            seqid = parts[0]
            source = parts[1]
            feature_type = parts[2]
            start = int(parts[3])
            end = int(parts[4])
            score = parts[5] if parts[5] != '.' else None
            strand = parts[6]
            phase = parts[7] if parts[7] != '.' else None
            attr_str = parts[8]

            # 解析属性字段
            attributes = {}
            for attr in attr_str.split(';'):
                if '=' in attr:
                    key, value = attr.split('=', 1)
                    attributes[key] = value
                elif attr:  # 处理没有等号的情况
                    attributes[attr] = True

            annotations.append({
                'seqid': seqid,
                'source': source,
                'type': feature_type,
                'start': start,
                'end': end,
                'score': score,
                'strand': strand,
                'phase': phase,
                'attributes': attributes,
                'original_line': line  # 保存原始行以便输出
            })

    return annotations


def get_features_in_region(annotations, seqid, region_start, region_end):
    """
    获取指定区域内的所有特征注释

    Args:
        annotations: 所有注释列表
        seqid: 序列ID
        region_start: 区域起始位置
        region_end: 区域结束位置

    Returns:
        区域内所有特征的注释列表
    """
    region_annotations = []

    for ann in annotations:
        # 检查序列ID是否匹配
        if ann['seqid'] != seqid:
            continue

        # 检查特征是否与目标区域有重叠
        # 使用完全包含逻辑：特征完全在区域内
        if (ann['start'] >= region_start and ann['end'] <= region_end):
            region_annotations.append(ann)
        # 或者使用部分重叠逻辑（可选）
        # elif (ann['end'] >= region_start and ann['start'] <= region_end):
        #     region_annotations.append(ann)

    # 按起始位置排序
    region_annotations.sort(key=lambda x: x['start'])

    return region_annotations


def extract_region_sequence(sequences, seqid, region_start, region_end):
    """
    从序列中提取指定区域的序列

    Args:
        sequences: 序列字典
        seqid: 序列ID
        region_start: 区域起始位置（1-based）
        region_end: 区域结束位置

    Returns:
        提取的序列
    """
    if seqid not in sequences:
        raise ValueError(f"序列ID '{seqid}' 在FASTA文件中未找到")

    seq = sequences[seqid]

    # 检查坐标是否有效
    if region_start < 1 or region_end > len(seq):
        raise ValueError(f"坐标范围 {region_start}-{region_end} 超出序列长度 {len(seq)}")

    # 提取序列（注意：Python是0-based，GFF是1-based）
    extracted_seq = seq[region_start - 1:region_end]

    return extracted_seq


def save_extracted_region(fasta_path, gff_path, seqid, region_start, region_end,
                          sequences, region_annotations, output_dir):
    """保存提取的区域数据到文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 生成输出文件名
    base_filename = f"{seqid}_{region_start}_{region_end}"

    # 1. 保存序列
    seq_filename = f"{base_filename}.fasta"
    seq_path = os.path.join(output_dir, seq_filename)

    region_sequence = extract_region_sequence(sequences, seqid, region_start, region_end)

    with open(seq_path, 'w') as f:
        header = f">{seqid}:{region_start}-{region_end}"
        header += f" extracted_from:{os.path.basename(fasta_path)}"
        header += f" length:{len(region_sequence)}"
        f.write(f"{header}\n")

        # 每行80个字符
        for i in range(0, len(region_sequence), 80):
            f.write(f"{region_sequence[i:i + 80]}\n")

    # 2. 保存注释
    anno_filename = f"{base_filename}.gff"
    anno_path = os.path.join(output_dir, anno_filename)

    with open(anno_path, 'w') as f:
        # 写入GFF头信息
        f.write(f"##gff-version 3\n")
        f.write(f"##sequence-region {seqid} {region_start} {region_end}\n")
        f.write(f"##source: {os.path.basename(gff_path)}\n")
        f.write(f"##extracted-region: {seqid}:{region_start}-{region_end}\n")

        # 调整注释坐标（相对于提取区域的起始位置）
        for ann in region_annotations:
            # 计算新的相对坐标
            new_start = ann['start'] - region_start + 1
            new_end = ann['end'] - region_start + 1

            # 构建新的属性字符串
            attr_parts = []
            for key, value in ann['attributes'].items():
                if value is True:  # 处理布尔属性
                    attr_parts.append(key)
                else:
                    attr_parts.append(f"{key}={value}")

            # 添加原始坐标信息
            attr_parts.append(f"original_coords={ann['seqid']}:{ann['start']}-{ann['end']}")
            attr_str = ';'.join(attr_parts)

            # 写入调整后的GFF行
            score_str = ann['score'] if ann['score'] is not None else '.'
            phase_str = ann['phase'] if ann['phase'] is not None else '.'

            line = f"{seqid}\t{ann['source']}\t{ann['type']}\t"
            line += f"{new_start}\t{new_end}\t{score_str}\t"
            line += f"{ann['strand']}\t{phase_str}\t{attr_str}\n"
            f.write(line)

    # 3. 保存统计信息
    stat_filename = f"{base_filename}_statistics.txt"
    stat_path = os.path.join(output_dir, stat_filename)

    with open(stat_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write(f"提取区域统计信息\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"基因组文件: {fasta_path}\n")
        f.write(f"注释文件: {gff_path}\n")
        f.write(f"提取区域: {seqid}:{region_start}-{region_end}\n")
        f.write(f"区域长度: {region_end - region_start + 1} bp\n")
        f.write(f"提取时间: {os.path.getmtime(fasta_path)}\n\n")

        f.write(f"找到的特征数量: {len(region_annotations)}\n\n")

        # 按特征类型统计
        type_counts = defaultdict(int)
        for ann in region_annotations:
            type_counts[ann['type']] += 1

        f.write("特征类型统计:\n")
        for feature_type, count in sorted(type_counts.items()):
            f.write(f"  {feature_type}: {count}\n")

        f.write("\n详细信息:\n")
        f.write("-" * 60 + "\n")
        for i, ann in enumerate(region_annotations, 1):
            gene_id = ann['attributes'].get('ID', 'N/A')
            gene_name = ann['attributes'].get('Name', 'N/A')
            product = ann['attributes'].get('product', 'N/A')

            f.write(f"{i:3d}. {ann['type']:12s} | ")
            f.write(f"ID: {gene_id:15s} | ")
            f.write(f"坐标: {ann['start']:6d}-{ann['end']:6d} ({ann['strand']}) | ")
            f.write(f"长度: {ann['end'] - ann['start'] + 1:6d} bp | ")
            f.write(f"名称: {gene_name:20s}\n")

            if product != 'N/A' and product != gene_name:
                f.write(f"     Product: {product}\n")

    return seq_path, anno_path, stat_path


def main():
    """主函数 - 提取指定区域的所有注释和序列"""
    # 1. 设置输入文件路径
    fasta_path = "C:/基因组/Aquarius_paludum.fasta"  # 替换为你的FASTA文件路径
    gff_path = "C:/基因组/Aquarius_paludum.gff"  # 替换为你的GFF文件路径
    output_dir = "D:/黾蝽发育"  # 输出目录

    # 2. 设置要提取的基因组区域
    # 可以修改这里来提取不同区域
    regions_to_extract = [
        {
            'seqid': 'Chr04',  # 染色体/contig ID
            'start': 34822938,  # 起始位置
            'end': 35105506,  # 结束位置
            'strand': '+',  # 链方向
        },
        # 可以添加更多区域

    ]

    # 3. 检查输入文件
    if not os.path.exists(fasta_path):
        print(f"错误: FASTA文件不存在: {fasta_path}")
        return

    if not os.path.exists(gff_path):
        print(f"错误: GFF文件不存在: {gff_path}")
        return

    # 4. 解析文件
    print("=" * 60)
    print(f"正在解析FASTA文件: {fasta_path}")
    sequences = parse_fasta(fasta_path)
    print(f"找到 {len(sequences)} 条序列")

    print(f"\n正在解析GFF文件: {gff_path}")
    annotations = parse_gff(gff_path)
    print(f"找到 {len(annotations)} 条注释")
    print("=" * 60)

    # 5. 处理每个要提取的区域
    for i, region_info in enumerate(regions_to_extract, 1):
        seqid = region_info['seqid']
        region_start = region_info['start']
        region_end = region_info['end']
        description = region_info.get('description', '')

        print(f"\n{'=' * 60}")
        print(f"处理区域 {i}: {seqid}:{region_start}-{region_end}")
        if description:
            print(f"描述: {description}")
        print(f"{'=' * 60}")

        # 检查序列ID是否存在
        if seqid not in sequences:
            print(f"错误: 序列ID '{seqid}' 在FASTA文件中未找到")
            print(f"可用序列ID: {list(sequences.keys())[:5]}...")
            continue

        # 检查坐标是否有效
        seq_length = len(sequences[seqid])
        if region_start < 1 or region_end > seq_length:
            print(f"错误: 坐标范围 {region_start}-{region_end} 超出序列长度 {seq_length}")
            continue

        # 获取区域内的所有特征
        region_annotations = get_features_in_region(annotations, seqid, region_start, region_end)
        print(f"找到 {len(region_annotations)} 个特征")

        if not region_annotations:
            print("警告: 该区域内未找到任何特征")

        # 按特征类型统计
        from collections import Counter
        type_counter = Counter([ann['type'] for ann in region_annotations])
        for feature_type, count in type_counter.most_common():
            print(f"  {feature_type}: {count}")

        # 提取并保存
        try:
            seq_path, anno_path, stat_path = save_extracted_region(
                fasta_path, gff_path, seqid, region_start, region_end,
                sequences, region_annotations, output_dir
            )

            print(f"\n提取完成!")
            print(f"序列保存至: {seq_path}")
            print(f"注释保存至: {anno_path}")
            print(f"统计信息: {stat_path}")

        except Exception as e:
            print(f"错误: 提取失败 - {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()