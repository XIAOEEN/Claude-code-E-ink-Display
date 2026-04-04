import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import numpy as np

class CatDogDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        self.image_paths = []
        self.labels = []

        for filename in sorted(os.listdir(data_dir)):
            if filename.endswith('.jpg'):
                self.image_paths.append(os.path.join(data_dir, filename))
                label_str = filename.split('.')[0]
                label = 0 if label_str == 'cat' else 1
                self.labels.append(label)

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert('RGB')
        label = self.labels[idx]
        if self.transform:
            image = self.transform(image)
        return image, label, self.image_paths[idx]

class CatDogClassifier(nn.Module):
    def __init__(self, num_classes=2, pretrained=True):
        super(CatDogClassifier, self).__init__()
        self.backbone = models.resnet18(pretrained=pretrained)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")

    # 数据预处理
    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # 加载数据集
    test_dataset = CatDogDataset('dataset/test', transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # 加载模型
    model = CatDogClassifier(num_classes=2, pretrained=False)
    if os.path.exists('best_model.pth'):
        model.load_state_dict(torch.load('best_model.pth', map_location=device))
        print("已加载训练好的模型: best_model.pth")
    else:
        print("警告: 未找到训练好的模型，使用随机初始化的模型")
        print("请先运行 python train.py 进行训练")

    model = model.to(device)
    model.eval()

    # 推理
    correct = 0
    total = 0
    class_correct = [0, 0]
    class_total = [0, 0]

    print("\n开始推理...")
    with torch.no_grad():
        for images, labels, paths in test_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            _, predicted = outputs.max(1)

            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            for i in range(len(labels)):
                label = labels[i].item()
                class_correct[label] += (predicted[i] == label).item()
                class_total[label] += 1

    # 输出结果
    print("\n" + "=" * 50)
    print("测试集分类结果")
    print("=" * 50)

    overall_acc = 100. * correct / total
    cat_acc = 100. * class_correct[0] / class_total[0]
    dog_acc = 100. * class_correct[1] / class_total[1]

    print(f"整体准确率: {overall_acc:.2f}%")
    print(f"猫 (Cat) 准确率: {cat_acc:.2f}% ({class_correct[0]}/{class_total[0]})")
    print(f"狗 (Dog) 准确率: {dog_acc:.2f}% ({class_correct[1]}/{class_total[1]})")
    print("=" * 50)

    return cat_acc, dog_acc

if __name__ == '__main__':
    main()
