
import os
import glob
import argparse

import numpy as np
import scipy.io as sio
from PIL import Image
from scipy.ndimage import gaussian_filter

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms


# =========================================================
# 1. DATASET PATH
# =========================================================

DATASET_ROOT = (
    r"C:\Users\GAYATHRI\Downloads\crowd desnity shangaai dataset"
    r"\ShanghaiTech_Crowd_Counting_Dataset"
)

DEVICE = torch.device("cpu")


# =========================================================
# 2. CSRNet MODEL
# =========================================================

class CSRNet(nn.Module):

    def __init__(self, pretrained=True):
        super().__init__()

        # VGG16 frontend
        try:
            if pretrained:
                vgg = models.vgg16(
                    weights=models.VGG16_Weights.DEFAULT
                )
            else:
                vgg = models.vgg16(weights=None)

        except Exception as error:
            print("Could not load pretrained VGG16:", error)
            print("Using VGG16 with random initialization.")
            vgg = models.vgg16(weights=None)

        # Three max-pooling layers: output resolution is 1/8
        self.frontend = nn.Sequential(
            *list(vgg.features.children())[:23]
        )

        # Dilated convolution backend
        self.backend = nn.Sequential(
            nn.Conv2d(512, 512, 3, padding=2, dilation=2),
            nn.ReLU(inplace=True),

            nn.Conv2d(512, 512, 3, padding=2, dilation=2),
            nn.ReLU(inplace=True),

            nn.Conv2d(512, 256, 3, padding=2, dilation=2),
            nn.ReLU(inplace=True),

            nn.Conv2d(256, 128, 3, padding=2, dilation=2),
            nn.ReLU(inplace=True),

            nn.Conv2d(128, 64, 3, padding=2, dilation=2),
            nn.ReLU(inplace=True),
        )

        self.output_layer = nn.Conv2d(64, 1, kernel_size=1)

    def forward(self, x):
        x = self.frontend(x)
        x = self.backend(x)
        x = self.output_layer(x)
        return x


# =========================================================
# 3. SHANGHAITECH DATASET
# =========================================================

class ShanghaiDataset(Dataset):

    def __init__(
        self,
        root,
        part="B",
        split="train",
        image_size=256
    ):
        self.image_size = image_size

        part_folder = os.path.join(
            root, f"part_{part}_final"
        )

        if not os.path.isdir(part_folder):
            part_folder = os.path.join(
                root, f"part_{part}"
            )

        split_folder = (
            "train_data" if split == "train"
            else "test_data"
        )

        self.image_dir = os.path.join(
            part_folder, split_folder, "images"
        )

        self.gt_dir = os.path.join(
            part_folder, split_folder, "ground_truth"
        )

        if not os.path.isdir(self.gt_dir):
            self.gt_dir = os.path.join(
                part_folder, split_folder, "ground-truth"
            )

        if not os.path.isdir(self.image_dir):
            raise FileNotFoundError(
                f"Image folder not found:\n{self.image_dir}\n"
                "Check your ShanghaiTech dataset folder structure."
            )

        if not os.path.isdir(self.gt_dir):
            raise FileNotFoundError(
                f"Ground-truth folder not found:\n{self.gt_dir}"
            )

        image_files = (
            glob.glob(os.path.join(self.image_dir, "*.jpg"))
            + glob.glob(os.path.join(self.image_dir, "*.jpeg"))
            + glob.glob(os.path.join(self.image_dir, "*.png"))
        )

        image_files = sorted(image_files)

        self.samples = []

        for image_path in image_files:

            filename = os.path.splitext(
                os.path.basename(image_path)
            )[0]

            possible_gt_paths = [
                os.path.join(
                    self.gt_dir, "GT_" + filename + ".mat"
                ),
                os.path.join(
                    self.gt_dir, filename + ".mat"
                ),
            ]

            gt_path = next(
                (
                    path for path in possible_gt_paths
                    if os.path.isfile(path)
                ),
                None
            )

            if gt_path:
                self.samples.append((image_path, gt_path))

        if not self.samples:
            raise RuntimeError(
                f"No matching image and GT pairs found.\n"
                f"Images: {self.image_dir}\n"
                f"Ground truth: {self.gt_dir}"
            )

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        print(f"{part}-{split} images found: {len(self.samples)}")

    def extract_points(self, mat_path):

        mat = sio.loadmat(mat_path)

        # Standard ShanghaiTech MATLAB annotation format
        if "image_info" in mat:

            info = mat["image_info"]

            try:
                points = info[0, 0]["location"][0, 0]
                points = np.asarray(
                    points, dtype=np.float32
                )

                return points.reshape(-1, 2)

            except (IndexError, KeyError, TypeError, ValueError):
                pass

        # Alternative annotation formats
        for key in ("annPoints", "points", "location"):

            if key in mat:

                points = np.asarray(
                    mat[key], dtype=np.float32
                )

                if (
                    points.ndim == 2
                    and points.shape[1] == 2
                ):
                    return points

        raise ValueError(
            f"Cannot read annotation points from: {mat_path}"
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):

        image_path, gt_path = self.samples[index]

        image = Image.open(image_path).convert("RGB")

        original_width, original_height = image.size

        points = self.extract_points(gt_path)

        # Resize image
        image = image.resize(
            (self.image_size, self.image_size),
            Image.Resampling.BILINEAR
        )

        # Scale annotation coordinates to resized image
        points = points.copy()

        if len(points) > 0:
            points[:, 0] *= self.image_size / original_width
            points[:, 1] *= self.image_size / original_height

        image_tensor = self.transform(image)

        # Create density map at 1/8 image resolution
        density = np.zeros(
            (self.image_size // 8, self.image_size // 8),
            dtype=np.float32
        )

        for x, y in points:

            gx = int(round(x / 8))
            gy = int(round(y / 8))

            if (
                0 <= gx < density.shape[1]
                and 0 <= gy < density.shape[0]
            ):
                density[gy, gx] += 1.0

        # Smooth point annotations into a density map
        density = gaussian_filter(density, sigma=1)

        # Preserve the annotated person count
        density_sum = density.sum()

        if density_sum > 0:
            density *= len(points) / density_sum

        density_tensor = torch.from_numpy(
            density.astype(np.float32)
        ).unsqueeze(0)

        actual_count = torch.tensor(
            float(len(points)),
            dtype=torch.float32
        )

        return image_tensor, density_tensor, actual_count


# =========================================================
# 4. MODEL EVALUATION
# =========================================================

def evaluate_model(model, loader):

    model.eval()

    absolute_errors = []
    squared_errors = []

    with torch.no_grad():

        for images, _, actual_counts in loader:

            images = images.to(DEVICE)

            predicted_density = model(images)

            predicted_count = max(
                0.0,
                predicted_density.sum().item()
            )

            actual_count = actual_counts.item()

            error = predicted_count - actual_count

            absolute_errors.append(abs(error))
            squared_errors.append(error ** 2)

    mae = float(np.mean(absolute_errors))
    rmse = float(np.sqrt(np.mean(squared_errors)))

    return mae, rmse


# =========================================================
# 5. TRAINING FUNCTION
# =========================================================

def train_model(args, part):

    print("\n" + "=" * 60)
    print(f"Training CSRNet - ShanghaiTech Part {part}")
    print(f"Dataset: {DATASET_ROOT}")
    print(f"Device: {DEVICE}")
    print("=" * 60)

    train_dataset = ShanghaiDataset(
        root=DATASET_ROOT,
        part=part,
        split="train",
        image_size=args.image_size
    )

    test_dataset = ShanghaiDataset(
        root=DATASET_ROOT,
        part=part,
        split="test",
        image_size=args.image_size
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=1,
        shuffle=True,
        num_workers=0
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=1,
        shuffle=False,
        num_workers=0
    )

    model = CSRNet(
        pretrained=not args.no_pretrained
    ).to(DEVICE)

    criterion = nn.MSELoss()

    optimizer = optim.SGD(
        model.parameters(),
        lr=args.lr,
        momentum=0.9,
        weight_decay=5e-4
    )

    os.makedirs(args.output_dir, exist_ok=True)

    best_mae = float("inf")

    for epoch in range(args.epochs):

        model.train()

        total_loss = 0.0

        print(
            f"\nEpoch {epoch + 1}/{args.epochs}"
        )

        for step, batch in enumerate(train_loader):

            images, density_maps, _ = batch

            images = images.to(DEVICE)
            density_maps = density_maps.to(DEVICE)

            optimizer.zero_grad()

            predicted_density = model(images)

            loss = criterion(
                predicted_density,
                density_maps
            )

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            if (step + 1) % 10 == 0:
                print(
                    f"Step {step + 1}/{len(train_loader)} "
                    f"| Loss: {loss.item():.6f}"
                )

        average_loss = (
            total_loss / max(len(train_loader), 1)
        )

        mae, rmse = evaluate_model(
            model, test_loader
        )

        print("\nEpoch Results")
        print(f"Training Loss : {average_loss:.6f}")
        print(f"Test MAE      : {mae:.2f}")
        print(f"Test RMSE     : {rmse:.2f}")

        checkpoint = {
            "model_state_dict": model.state_dict(),
            "part": part,
            "epoch": epoch + 1,
            "mae": mae,
            "rmse": rmse,
            "image_size": args.image_size,
        }

        last_path = os.path.join(
            args.output_dir,
            f"csrnet_part_{part}_last.pth"
        )

        torch.save(checkpoint, last_path)

        if mae < best_mae:

            best_mae = mae

            best_path = os.path.join(
                args.output_dir,
                f"csrnet_part_{part}_best.pth"
            )

            torch.save(checkpoint, best_path)

            print(f"Best model saved: {best_path}")

    print("\n" + "=" * 60)
    print(f"Part {part} training completed")
    print(f"Best Test MAE: {best_mae:.2f}")
    print("=" * 60)




if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Train CSRNet on ShanghaiTech Dataset"
    )

    parser.add_argument(
        "--part",
        choices=["A", "B", "both"],
        default="B"
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=50
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=1e-6
    )

    parser.add_argument(
        "--image-size",
        type=int,
        default=256
    )

    parser.add_argument(
        "--output-dir",
        default="checkpoints"
    )

    parser.add_argument(
        "--no-pretrained",
        action="store_true"
    )

    args = parser.parse_args()

    if not os.path.isdir(DATASET_ROOT):
        raise FileNotFoundError(
            f"Dataset path does not exist:\n{DATASET_ROOT}"
        )

    if args.part in ("A", "both"):
        train_model(args, "A")

    if args.part in ("B", "both"):
        train_model(args, "B")
