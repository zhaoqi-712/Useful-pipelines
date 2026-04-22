import pandas as pd
import os


def excel_to_txt(excel_path, txt_path, start_col=3):
    """
    将 Excel 转换为 txt 描述，支持复杂标点和性别段落处理
    excel_path: 输入 Excel 路径
    txt_path: 输出 txt 路径
    start_col: 从第几列开始处理（默认第3列，即索引2）
    """
    df = pd.read_excel(excel_path)
    columns = df.columns.tolist()

    gender_prefix = ("两性", "雄性", "雌性")
    punctuations = ("，", ",", "：", ":", ";", "；")

    with open(txt_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            # 第一行：物种名
            species_name = str(row[columns[0]])
            f.write(species_name + "\n")

            output = ""  # 最终输出字符串

            for i in range(start_col-1, len(columns)):
                col = columns[i] #标题重复时去掉后缀
                #print(col)
                col_str = str(col).strip().split('.')[0]

                # 忽略空标题
                if not col_str:
                    continue

                value = row[col]

                # 处理空内容
                if pd.isna(value) or str(value).strip() == "":
                    content = "[待确认]"
                else:
                    content = str(value).strip()

                # 跳过 "-"
                if content == "-":
                    continue

                # 是否最后一列
                is_last_col = (i == len(columns) - 1)

                # 下一列是否为性别段
                next_is_gender = False
                if i + 1 < len(columns):
                    next_col = str(columns[i+1]).strip()
                    if next_col.startswith(gender_prefix):
                        next_is_gender = True

                # 当前列是否为性别或标点开头
                current_is_special = col_str.startswith(punctuations) or col_str.startswith(gender_prefix)

                # 构造文本
                text = f"{col_str}{content}"


                # 第 n 列，直接输出
                if i == start_col-1:
                    output += text
                else:
                    # 特殊开头，直接输出标题+内容
                    if current_is_special:
                        output += text
                    # 下一列是性别段，当前列加句号
                    elif next_is_gender:
                        output += "；" + text + "。"
                    # 其他情况，前面加分号
                    else:
                        output += "；" + text

                # 最后一列，必须加句号
                if is_last_col:
                    output += "。"

            f.write(output + "\n\n")

    print(f"已完成描述，文件存储于 {txt_path}")



if __name__ == "__main__":
    base_path = "D:/中国动物志编写/形态描述"

    species_list = ["涧黾属","始黾属", "东方黾蝽属", "淡纹黾蝽属", "大涧黾", "毛足涧黾属"
        , "巨涧黾属", "黾蝽亚属", "宏黾蝽亚属"]
    for species in species_list:
        input_file = f"{base_path}/{species}.xlsx"
        output_file = f"{base_path}/{species}.txt"
        excel_to_txt(input_file, output_file)

