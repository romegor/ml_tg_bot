import torch
import torchvision.transforms as transforms
from PIL import Image
import torch.nn as nn
import torchvision.models as models
from torchvision.utils import save_image
from io import BytesIO

class VGG(nn.Module):
    def __init__(self):
        super(VGG, self).__init__()
        self.req_features = ['0', '5', '10', '19', '28']
        self.model = models.vgg19(pretrained=True).features[:29]
    def forward(self, x):
        features = []
        for layer_num, layer in enumerate(self.model):
            x = layer(x)
            if (str(layer_num) in self.req_features):
                features.append(x)
        return features

class vgg16model:
    def __init__(self, img_size=384, img_size_cpu=224):
        """Constructor"""
        self.model = models.vgg19(pretrained=True).features
        self.device = torch.device("cuda" if (torch.cuda.is_available()) else 'cpu')
        # self.device = torch.device('cpu')
        self.alpha = 8
        self.beta = 70
        self.size = img_size
        if self.device.type == 'cpu':
            self.size = img_size_cpu



    def image_loader(self, path):
        image = Image.open(path)
        loader = transforms.Compose([transforms.Resize((self.size, self.size)), transforms.ToTensor()])
        image = loader(image).unsqueeze(0)
        return image.to(self.device, torch.float)

    def calc_content_loss(self, gen_feat, orig_feat):
        content_l = torch.mean((gen_feat - orig_feat) ** 2)
        return content_l

    def calc_style_loss(self, gen, style):
        batch_size, channel, height, width = gen.shape
        G = torch.mm(gen.view(channel, height * width), gen.view(channel, height * width).t())
        A = torch.mm(style.view(channel, height * width), style.view(channel, height * width).t())
        style_l = torch.mean((G - A) ** 2)
        return style_l

    def calculate_loss(self, gen_features, orig_feautes, style_featues):
        style_loss = content_loss = 0
        for gen, cont, style in zip(gen_features, orig_feautes, style_featues):
            content_loss += self.calc_content_loss(gen, cont)
            style_loss += self.calc_style_loss(gen, style)
        total_loss = self.alpha * content_loss + self.beta * style_loss
        return total_loss


    def image_transformation(self, original_path, style_path, epoch=300, lr=0.01):
        # self.device = torch.device("cuda" if (torch.cuda.is_available()) else 'cpu')
        original_image = self.image_loader(original_path)
        # style_image = self.styles[style_name]
        style_image = self.image_loader(style_path)
        style_image = style_image.expand(-1, 3, -1, -1)
        generated_image = original_image.clone().requires_grad_(True)
        self.model = VGG().to(self.device).eval()
        optimizer = torch.optim.Adam([generated_image], lr=lr, betas=(0.5, 0.999))
        for e in range(epoch):
            gen_features = self.model(generated_image)
            orig_feautes = self.model(original_image)
            style_featues = self.model(style_image)
            optimizer.zero_grad()
            total_loss = self.calculate_loss(gen_features, orig_feautes, style_featues)
            total_loss.backward()
            optimizer.step()

        with torch.no_grad():
            buffer = BytesIO()
            buffer.name = 'generated.jpg'
            save_image(generated_image, buffer)
        torch.cuda.empty_cache()
        return buffer

