import torch
from utils import *
from PIL import Image
from io import BytesIO

class sr_model:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.device = torch.device('cpu')
        self.srgan_checkpoint = "./checkpoint_srgan.pth.tar"
        self.srgan_generator = torch.load(self.srgan_checkpoint, map_location=self.device)['generator'].to(device)
        self.srgan_generator.eval()

    def get_sr_image(self, img):
        lr_img = Image.open(img, mode="r")
        lr_img = lr_img.convert('RGB')

        sr_img_srgan = self.srgan_generator(convert_image(lr_img, source='pil', target='imagenet-norm').
                                            unsqueeze(0).to(self.device))
        sr_img_srgan = sr_img_srgan.squeeze(0).cpu().detach()
        torch.cuda.empty_cache()
        sr_img_srgan = convert_image(sr_img_srgan, source='[-1, 1]', target='pil')
        buffer = BytesIO()
        buffer.name = 'generated.jpg'
        sr_img_srgan.save(buffer)
        return buffer