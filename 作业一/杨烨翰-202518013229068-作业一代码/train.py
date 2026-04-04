import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import numpy as np
from tqdm import tqdm

torch.manual_seed(42)
np.random.seed(42)

class Config:
    train_dir = 'dataset/train'
    test_dir = 'dataset/test'
    batch_size = 32
    num_epochs = 15
    learning_rate = 0.001
    img_size = 224 
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    class_names = ['cat', 'dog']
    num_classes = 2

cfg = Config()
print(f"使用设备: {cfg.device}")

class CatDogDataset(Dataset):
    def __init__(self, data_dir, transform=None, is_test=False):
        self.data_dir = data_dir
        self.transform = transform
        self.is_test = is_test


        self.image_paths = []
        self.labels = []

        for filename in os.listdir(data_dir):
            if filename.endswith('.jpg'):
                self.image_paths.append(os.path.join(data_dir, filename))
                # 从文件名解析标签: cat.0.jpg -> 0, dog.0.jpg -> 1
                label_str = filename.split('.')[0]
                label = 0 if label_str == 'cat' else 1
                self.labels.append(label)

        sorted_pairs = sorted(zip(self.image_paths, self.labels), key=lambda x: x[0])
        self.image_paths, self.labels = zip(*sorted_pairs)
        self.image_paths = list(self.image_paths)
        self.labels = list(self.labels)

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        image = Image.open(img_path).convert('RGB')
        label = self.labels[idx]

        if self.transform:
            image = self.transform(image)

        return image, label

train_transform = transforms.Compose([
    transforms.Resize((cfg.img_size, cfg.img_size)),
    transforms.RandomHorizontalFlip(p=0.5),      # 随机水平翻转
    transforms.RandomRotation(15),                 # 随机旋转
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),  # 颜色抖动
    transforms.ToTensor(),                          # 转换为Tensor
    transforms.Normalize(                          # ImageNet标准化
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

test_transform = transforms.Compose([
    transforms.Resize((cfg.img_size, cfg.img_size)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

class CatDogClassifier(nn.Module):

    def __init__(self, num_classes=2, pretrained=True):
        super(CatDogClassifier, self).__init__()

        # 这里的直接用的预训练的ResNet18
        self.backbone = models.resnet18(pretrained=pretrained)

        # +一个2分类的MLP-head
        in_features = self.backbone.fc.in_features  # 512
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),  
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)


def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

    
        outputs = model(images)
        loss = criterion(outputs, labels)

      
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc


def evaluate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    class_correct = [0, 0]
    class_total = [0, 0]

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            for i in range(len(labels)):
                label = labels[i].item()
                class_correct[label] += (predicted[i] == label).item()
                class_total[label] += 1

    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100. * correct / total

    # 计算每个类别的准确率
    cat_acc = 100. * class_correct[0] / class_total[0] if class_total[0] > 0 else 0
    dog_acc = 100. * class_correct[1] / class_total[1] if class_total[1] > 0 else 0

    return epoch_loss, epoch_acc, cat_acc, dog_acc

def main():

    train_dataset = CatDogDataset(cfg.train_dir, transform=train_transform)
    test_dataset = CatDogDataset(cfg.test_dir, transform=test_transform)

    train_loader = DataLoader(train_dataset, batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=cfg.batch_size, shuffle=False, num_workers=0)

    model = CatDogClassifier(num_classes=cfg.num_classes, pretrained=True)
    model = model.to(cfg.device)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(model.parameters(), lr=cfg.learning_rate)

    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

    print(f"{'Epoch':^8}{'Train Loss':^15}{'Train Acc':^15}{'Test Loss':^15}{'Test Acc':^15}{'Cat Acc':^15}{'Dog Acc':^15}")

    best_acc = 0.0

    for epoch in range(cfg.num_epochs):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, cfg.device)
        test_loss, test_acc, cat_acc, dog_acc = evaluate(model, test_loader, criterion, cfg.device)

        scheduler.step()

        print(f"{epoch+1:^8}{train_loss:^15.4f}{train_acc:^15.2f}{test_loss:^15.4f}{test_acc:^15.2f}{cat_acc:^15.2f}{dog_acc:^15.2f}")

        # 保存最佳模型
        if test_acc > best_acc:
            best_acc = test_acc
            torch.save(model.state_dict(), 'best_model.pth')

    print("-" * 80)
    print(f"最佳测试准确率: {best_acc:.2f}%")
    print("\n训练完成！模型已保存至 best_model.pth")

    print("\n" + "=" * 50)
    print("最终测试集评估结果:")
    print("=" * 50)
    _, final_acc, final_cat_acc, final_dog_acc = evaluate(model, test_loader, criterion, cfg.device)
    print(f"整体准确率: {final_acc:.2f}%")
    print(f"猫的准确率 (Cat Acc): {final_cat_acc:.2f}%")
    print(f"狗的准确率 (Dog Acc): {final_dog_acc:.2f}%")

    return model, final_cat_acc, final_dog_acc

if __name__ == '__main__':
    main()
