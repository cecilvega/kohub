import pandas as pd
import openpyxl
import re
from datetime import datetime
from pathlib import Path


# Function to get weeks and comments where value is 1
def get_weeks_and_comments(row):
    weeks = []
    comments = []
    row_idx = int(row.name.strip("N°"))
    col_idx = 1
    for col, value in row.items():
        if value == 1:
            weeks.append(col)
            cell = sheet[row_idx + 1][col_idx]
            comments.append(cell.comment.text if cell.comment else "")
        col_idx += 1
    return pd.Series({"weeks": weeks, "comments": comments})


def get_end_week(row):
    weeks = []
    pool_repair_types = []
    row_idx = int(row.name.strip("N°"))
    for col_idx in range(0, row.__len__()):
        if col_idx > 2:
            prev_cell = sheet[row_idx + 1][col_idx - 1]
            cell = sheet[row_idx + 1][col_idx]
            if (
                (prev_cell.fill.fgColor.rgb != cell.fill.fgColor.rgb)
                & (prev_cell.value is None)
                & (prev_cell.fill.fgColor.rgb in ["FFEDBFBB", "FFC5E0B4", "FFE88880"])
                # & (prev_cell.fill.fgColor.rgb in ["FFC5E0B4", "FFE88880"])
            ):
                weeks.append(list(row.keys())[col_idx - 2])
                if prev_cell.fill.fgColor.rgb in ["FFEDBFBB", '"FFE88880"']:
                    pool_repair_types.append("I")
                else:
                    pool_repair_types.append("P")

    return pd.Series({"weeks": weeks, "pool_repair_type": pool_repair_types})


def idx_to_pool_number(df):
    df = (
        df.reset_index()
        .rename(columns={"index": "pool_number"})
        .assign(pool_number=lambda x: x["pool_number"].str.strip("N°"))
    )
    return df


files = [p for p in Path("pool-files").rglob("*cms.xlsx")]


frames = []
for file in files:

    # Function to extract information from comments
    def extract_info(comment):
        equipo_match = re.search(r"Equipo:\s*(\d+)", comment)
        ns_match = re.search(r"NS:\s*(#\w*-?\w*)", comment)

        equipo = equipo_match.group(1) if equipo_match else None
        ns = ns_match.group(1) if ns_match else None

        return equipo, ns

    # Read the Excel file
    excel_file = file.__str__()  # Replace with your actual file name
    wb = openpyxl.load_workbook(excel_file, data_only=True)
    sheet = wb.active

    # Create a DataFrame from the Excel data
    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        data.append(row)

    df = pd.DataFrame(data, columns=[cell.value for cell in sheet[1]])
    df.set_index(df.columns[0], inplace=True)

    # Process the dataframe
    start_repair_df = (
        df.apply(get_weeks_and_comments, axis=1)
        .explode(["weeks", "comments"])
        .rename(columns={"weeks": "repair_start_week"})
        .pipe(idx_to_pool_number)
    )

    # Extract information from comments
    start_repair_df[["equipo", "ns"]] = start_repair_df["comments"].apply(lambda x: pd.Series(extract_info(x)))
    start_repair_df = start_repair_df.drop(columns=["comments"]).assign(
        repair_start_date=start_repair_df["repair_start_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w"))
    )
    end_repair_df = (
        df.apply(get_end_week, axis=1)
        .explode(["weeks", "pool_repair_type"])
        .rename(columns={"weeks": "repair_end_week"})
        .pipe(idx_to_pool_number)
    )
    end_repair_df = end_repair_df.assign(
        repair_end_date=end_repair_df["repair_end_week"].map(lambda x: datetime.strptime(x + "-1", "%Y-W%W-%w"))
    )

    df = pd.merge_asof(
        start_repair_df.sort_values("repair_start_date"),
        end_repair_df.sort_values("repair_end_date"),
        by="pool_number",
        left_on="repair_start_date",
        right_on="repair_end_date",
        direction="forward",
    ).assign(component=file.stem.split("-")[-1])
    frames.append(df)
df = pd.concat(frames)

# @st.cache_data(persist="disk")
# def select_lr_partitions(date_filters=None, machine_filters=None):
#     files = list_lr_files()
#     df = pl.from_pandas(pd.DataFrame(files))
#     if machine_filters is not None:
#         df = df.filter(pl.col("machine_id").is_in(machine_filters))
#     if date_filters is not None:
#         df = (
#             df.join(date_filters, how="inner", on="machine_id")
#             .filter(pl.col("partition_date").is_between(lower_bound="from_datetime", upper_bound="to_datetime"))
#             .drop(["from_datetime", "to_datetime"])
#         )
#     files = df.to_dicts()
#     return files
