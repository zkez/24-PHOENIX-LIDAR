from PIL import Image


def resize_image(input_path, output_path, max_size):
    # 打开图片文件
    with Image.open(input_path) as img:
        # 获取原始图片的宽高
        width, height = img.size

        # 计算等比例缩放后的尺寸
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        # 缩小图片
        resized_img = img.resize((new_width, new_height), Image.ANTIALIAS)

        # 转换为RGB模式
        resized_img = resized_img.convert("RGB")

        # 保存缩小后的图片
        resized_img.save(output_path)


input_image_path = "./save_stuff/map.jpg"
output_image_path = "./save_stuff/output_map.jpg"
max_size = 960

resize_image(input_image_path, output_image_path, max_size)
