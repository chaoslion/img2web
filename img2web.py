#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance


"""
does not work w/ python 3, since PIL has some bugs...
"""

"""
* Returns an image with reduced opacity. Taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/362879
* edited by chslion
* returns watermarked img file
* it contains no exif data
"""
def watermark(image, opacity):
    scale = 0.1    
    fontfile = "UbuntuMono-R.ttf"
    text = "alexander.jaehnel.info"

    width, height = image.size

    # skip small images
    if width < 100 or height < 100:
        return image



    # ===calc histogram of original
    # to black/white
    img_bw = image.convert("L")
    hist = img_bw.histogram()
    dark_portion = hist[:85]
    mid_portion = hist[85:170]
    light_portion = hist[170:]
        
    cnt_dark = 0
    cnt_mid = 0
    cnt_light = 0
    for pi in dark_portion:
        cnt_dark += pi
    for pi in mid_portion:
        cnt_mid += pi
    for pi in light_portion:
        cnt_light += pi

    if cnt_dark > cnt_light and cnt_dark > cnt_mid:
        color = (255, 255, 255)
        opacity /= 2
        print("image seems dark, lowering opacity")        
    elif cnt_light > cnt_dark and cnt_light > cnt_mid:
        color = (0, 0, 0)
        opacity *= 2
        print("image seems light, increasing opacity")        
    else:        
        color = (128, 128, 128)
        print("using default opacity")        

    if opacity > 1.0:
        opacity = 1.0
    elif opacity < 0.0:
        opacity = 0.0  

    font_size = int(scale*height)
    font = ImageFont.truetype(fontfile, font_size)

    if image.mode != "RGBA":
        image = image.convert("RGBA")


    # watermark layer takes biggest dimension
    # so rotation fills whole image
    textlayer = Image.new("RGBA", [width*2, height*2], (0,0,0,0))

    textdraw = ImageDraw.Draw(textlayer)

    wm_width, wm_height = textdraw.textsize(text, font=font)
    # textsize does not give correct height for ttf
    offset = font.getoffset(text)
    wm_width += offset[0]
    wm_height += offset[1]

    # lower right corner
    # textpos = [
    #     image.size[0] - textsize[0] - offset[0],
    #     image.size[1] - textsize[1] - offset[1]
    # ]
    # textdraw.text([0,0], text, font=font, fill=color)
    maxx = (int)(width*2/wm_width)
    maxy = (int)(height*2/wm_height)

    # render font in a checkered layout
    for y in range(maxy):
        y_odd = y % 2 == 0
        for x in range(maxx):
            # x is odd?
            x_odd = x % 2 == 0

            check = x_odd
            if not y_odd:
                check = not check

            if check:
                textdraw.text([x*wm_width, y*wm_height], text, font=font, fill=color)

    # rotate
    textlayer = textlayer.rotate(45, Image.BICUBIC)

    # crop to original size, from center    
    # import pdb; pdb.set_trace()
    cropx = textlayer.size[0] / 2 - width / 2
    cropy = textlayer.size[1] / 2 - height / 2
    textlayer = textlayer.crop([cropx, cropy, cropx + width, cropy + height])     

    if opacity > 0.0 and opacity < 1.0:
        if textlayer.mode != 'RGBA':
            textlayer = textlayer.convert('RGBA')
        else:
            textlayer = textlayer.copy()
        alpha = textlayer.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        textlayer.putalpha(alpha)

    # overlay onto original image    
    return Image.composite(textlayer, image, textlayer)



def process_image(oldpath, newpath, width, height, alpha):
    print("processing: {}".format(oldpath))

    im = Image.open(oldpath)
    # apply watermark
    wm = watermark(im, alpha)
    # scale image
    wm.thumbnail([width, height])
    # save image    
    wm.save(newpath)

def run():
    parser = argparse.ArgumentParser(
        description="Watermark Creator"
    )
    

    parser.add_argument("-a", "--alpha", type=float, dest="alpha", default=0.1)
    parser.add_argument("-sx", "--width", type=int, dest="width", default=1024)
    parser.add_argument("-sy", "--height", type=int, dest="height", default=768)
    parser.add_argument("path", type=str)
    cfg = parser.parse_args()

    print("hello")

    if os.path.isfile(cfg.path):
        fname, fext = os.path.splitext(cfg.path)

        if not (fext.lower() == ".png" or fext.lower() == ".jpg"):
            print("invalid image")
            return
        
        process_image(
                cfg.path, 
                "{}_web{}".format(fname, fext),                
                cfg.width, 
                cfg.height, 
                cfg.alpha
            )       

    elif os.path.isdir(cfg.path):

        for folder_item in os.listdir(cfg.path):

            if os.path.isdir(folder_item):
                continue

            fname, fext = os.path.splitext(folder_item)

            if not (fext.lower() == ".png" or fext.lower() == ".jpg"):
                continue

            # skip processed images
            if fname.lower().endswith("_web"):
                continue

            process_image(
                os.path.join(cfg.path, folder_item),
                os.path.join(cfg.path, "{}_web{}".format(fname, fext)),
                cfg.width, 
                cfg.height, 
                cfg.alpha
            )

    else:
        print("invalid path argument")

if __name__ == "__main__":
    run()
