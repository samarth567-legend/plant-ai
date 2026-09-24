import os

# इथे तुझ्या dataset च्या MAIN FOLDER चा path टाक
DATASET_PATH = r"C:\Users\gc\Downloads\Plants_2"

image_extensions = (".jpg", ".jpeg", ".png", ".webp")

print("\n" + "=" * 70)
print("DATASET STRUCTURE")
print("=" * 70)

total_images = 0

for root, dirs, files in os.walk(DATASET_PATH):

    image_files = [
        f for f in files
        if f.lower().endswith(image_extensions)
    ]

    if image_files:
        relative_path = os.path.relpath(root, DATASET_PATH)

        print(f"\nFolder: {relative_path}")
        print(f"Images: {len(image_files)}")

        # पहिल्या 5 image names
        print("Sample images:")
        for img in image_files[:5]:
            print("   ", img)

        total_images += len(image_files)

print("\n" + "=" * 70)
print(f"TOTAL IMAGES: {total_images}")
print("=" * 70)
