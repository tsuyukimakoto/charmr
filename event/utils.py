from PIL import Image  


def calc_thumb_size(width, height, resize_to) :
    if width > height:
            scale = float(resize_to)/height
    else:
        scale = float(resize_to)/width
    return int(width * scale), int(height * scale)

def crop_rect(width, height) :
    if width > height :
        w = int( (width - height) / 2)
        h = 0
        max = height
    else :
        w = 0
        h = int( (height - width) / 2)
        max = width
    return (0 + w, 0 + h, max + w, max + h)

def resize_image(image, x, y, to):
    tmp_im = image.resize(calc_thumb_size(x, y, to), Image.ANTIALIAS)
    return tmp_im.crop(crop_rect(tmp_im.size[0], tmp_im.size[1]))
