import pandas as pd

def excel_to_txt(excel_path, txt_path):
    # 读取 Excel
    df = pd.read_excel(excel_path)

    columns = df.columns.tolist()
    feature_cols = columns[2:]  # 第三列及之后

    with open(txt_path, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            # 第一行：物种名
            species_name = str(row[columns[0]])
            f.write(species_name + "\n")

            descriptions = []

            for col in feature_cols:
                value = row[col]

                # 空白 → [未确认]
                if pd.isna(value):
                    descriptions.append(f"{col}[未确认]")
                    continue

                value = str(value).strip()

                # "-" → 跳过
                if value == "-":
                    continue

                descriptions.append(f"{col}{value}")

            # 第二行：描述
            f.write("；".join(descriptions) + "\n\n")  # 空行分隔物种

    print(f"已完成描述，文件存储于{txt_path}")


if __name__ == "__main__":

    input_file = "D:/中国动物志编写/形态描述/海黾亚科.xlsx"
    output_file = f"{input_file.split('.')[0]}.txt"
    # 示例调用
    excel_to_txt(input_file, output_file)


