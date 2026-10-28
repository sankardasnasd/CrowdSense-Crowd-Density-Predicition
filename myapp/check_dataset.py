
from pathlib import Path

DATASET = Path(
    r"C:\Users\GAYATHRI\Downloads\crowd desnity shangaai dataset"
    r"\ShanghaiTech_Crowd_Counting_Dataset"
    r"\part_B_final"
)

folders = [
    DATASET / "train_data" / "images",
    DATASET / "train_data" / "ground_truth",
    DATASET / "test_data" / "images",
    DATASET / "test_data" / "ground_truth",
]

for folder in folders:
    print("\nFolder:", folder)

    if not folder.exists():
        print("NOT FOUND")
        continue

    files = sorted(
        p for p in folder.iterdir()
        if p.is_file()
    )

    print("Files:", len(files))

    for file in files[:5]:
        print("  ", file.name)
