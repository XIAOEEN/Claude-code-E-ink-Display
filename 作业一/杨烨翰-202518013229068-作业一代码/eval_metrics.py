import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

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
        return image, label

class CatDogClassifier(nn.Module):
    def __init__(self, num_classes=2, pretrained=True):
        super(CatDogClassifier, self).__init__()
        self.backbone = models.resnet18(weights=None)
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
        print("错误: 未找到 best_model.pth")
        return

    model = model.to(device)
    model.eval()

    # 收集所有预测结果
    all_labels = []
    all_preds = []

    print("\n开始评估...")
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            _, predicted = outputs.max(1)

            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(predicted.cpu().numpy())

    all_labels = np.array(all_labels)
    all_preds = np.array(all_preds)

    # 计算混淆矩阵
    cm = confusion_matrix(all_labels, all_preds)

    # 按类别计算指标
    # Cat (class 0)
    tp_0 = cm[0, 0]
    fp_0 = cm[1, 0]
    fn_0 = cm[0, 1]
    tn_0 = cm[1, 1]

    precision_0 = tp_0 / (tp_0 + fp_0) if (tp_0 + fp_0) > 0 else 0
    recall_0 = tp_0 / (tp_0 + fn_0) if (tp_0 + fn_0) > 0 else 0
    f1_0 = 2 * precision_0 * recall_0 / (precision_0 + recall_0) if (precision_0 + recall_0) > 0 else 0

    # Dog (class 1)
    tp_1 = cm[1, 1]
    fp_1 = cm[0, 1]
    fn_1 = cm[1, 0]
    tn_1 = cm[0, 0]

    precision_1 = tp_1 / (tp_1 + fp_1) if (tp_1 + fp_1) > 0 else 0
    recall_1 = tp_1 / (tp_1 + fn_1) if (tp_1 + fn_1) > 0 else 0
    f1_1 = 2 * precision_1 * recall_1 / (precision_1 + recall_1) if (precision_1 + recall_1) > 0 else 0

    precision_macro = (precision_0 + precision_1) / 2
    recall_macro = (recall_0 + recall_1) / 2
    f1_macro = (f1_0 + f1_1) / 2

    accuracy = (tp_0 + tp_1) / (tp_0 + tp_1 + fp_0 + fp_1 + fn_0 + fn_1)

    print("\n【按类别统计】")
    print(f"{'指标':<20} {'Cat (0)':>12} {'Dog (1)':>12} {'Macro Avg':>12}")
    print("-" * 58)
    print(f"{'Accuracy':<20} {'-':>12} {'-':>12} {accuracy*100:>11.2f}%")
    print(f"{'Precision':<20} {precision_0*100:>11.2f}% {precision_1*100:>11.2f}% {precision_macro*100:>11.2f}%")
    print(f"{'Recall':<20} {recall_0*100:>11.2f}% {recall_1*100:>11.2f}% {recall_macro*100:>11.2f}%")
    print(f"{'F1 Score':<20} {f1_0*100:>11.2f}% {f1_1*100:>11.2f}% {f1_macro*100:>11.2f}%")

    print("```")
    print("| 指标 | Cat (0) | Dog (1) | Macro Avg |")
    print("|:-----|--------:|--------:|----------:|")
    print(f"| Accuracy | - | - | {accuracy*100:.2f}% |")
    print(f"| Precision | {precision_0*100:.2f}% | {precision_1*100:.2f}% | {precision_macro*100:.2f}% |")
    print(f"| Recall | {recall_0*100:.2f}% | {recall_1*100:.2f}% | {recall_macro*100:.2f}% |")
    print(f"| F1 Score | {f1_0*100:.2f}% | {f1_1*100:.2f}% | {f1_macro*100:.2f}% |")
    print("```")

if __name__ == '__main__':
    main()
