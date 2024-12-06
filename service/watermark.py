import concurrent.futures

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, ImageSequenceClip

from config import utils


def make_text_picture(h, w, text, font_size=45, angle=45, color=(169, 169, 169, int(255 * 0.2))):
    """
    制作水印图片

    h: 原图高度
    w: 原图宽度
    font_path：字体文件路径
    font_size：字体大小
    angle：字体旋转角度
    color：字体颜色
    """
    text_pic = Image.new('RGBA', (4 * h, 4 * w), (0, 0, 0, 0))

    mixins_medium_font_path = utils.get_project_path() + "/MiSans-Medium.ttf"
    fnt = ImageFont.truetype(mixins_medium_font_path, font_size, encoding="utf-8")

    text_d = ImageDraw.Draw(text_pic)

    # a, b 分别控制水印的列间距和行间距，默认为字体的1倍列距，4倍行距
    a, b = 1, 4
    for x in range(10, text_pic.size[0] - 10, a * font_size * len(text)):
        for y in range(10, text_pic.size[1] - 10, b * font_size):
            text_d.multiline_text((x, y), text, fill=color, font=fnt)

    # 旋转水印
    text_pic = text_pic.rotate(angle)
    # 截取水印部分图片
    text_pic = text_pic.crop((h, w, 2 * h, 2 * w))

    return text_pic


def add_watermark_to_pic(input_picture_path, output_picture_path, text="Watermark"):
    """
    为图片添加水印
    input_video_path: 输入图片路径
    output_video_path: 输出图片路径
    text: 水印文案
    """
    # 加载图片
    origin_picture = Image.open(input_picture_path).convert('RGBA')
    h, w = origin_picture.size

    # 创建水印图片
    text_pic = make_text_picture(h, w, text)

    # 融合图片
    composite_picture = Image.alpha_composite(origin_picture, text_pic)

    # 保存新图片文件
    composite_picture.save(output_picture_path)


def add_watermark_to_frame_with_index(args):
    frame_index, frame, text_pic = args
    # 在这里进行水印添加操作
    result_frame = add_watermark_to_frame(frame, text_pic)
    return frame_index, result_frame


def add_watermark_to_video(input_video_path, output_video_path, text="Watermark"):
    """
    为视频添加水印
    input_video_path: 输入视频路径
    output_video_path: 输出视频路径
    text: 水印文案
    """
    # 加载视频
    clip = VideoFileClip(input_video_path)
    h, w = clip.size

    # 创建水印图片
    text_pic = make_text_picture(h, w, text)

    # 处理每一帧
    # frames = [add_watermark_to_frame(frame, text_pic) for frame in clip.iter_frames()]

    # 并发处理
    with concurrent.futures.ThreadPoolExecutor() as executor:
        frame_args = [(i, frame, text_pic) for i, frame in enumerate(clip.iter_frames())]
        processed_frames = list(executor.map(add_watermark_to_frame_with_index, frame_args))
    # 对处理后的帧按照索引进行排序
    processed_frames.sort(key=lambda x: x[0])
    frames = [frame for _, frame in processed_frames]

    # 根据添加水印后的帧创建新的视频剪辑，但先不设置音频
    new_clip = ImageSequenceClip(frames, fps=clip.fps)

    # 将原始视频的音频设置给新剪辑
    new_clip = new_clip.set_audio(clip.audio)

    # 保存新视频文件
    new_clip.write_videofile(output_video_path, codec='libx264')


def add_watermark_to_frame(frame, text_pic):
    """
    将水印添加到视频帧上
    frame: 当前视频帧
    text_pic: 水印图片
    """
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
    image = Image.alpha_composite(image, text_pic)
    return pil_2_cv2(image)


def pil_2_cv2(pil_img):
    """
    PIL图片格式转CV图片格式
    """
    r, g, b, a = pil_img.split()
    img_cv_rgb = np.array(Image.merge("RGB", (r, g, b)))
    b_cv, g_cv, r_cv = cv2.split(img_cv_rgb)
    img_cv2 = cv2.merge([r_cv, g_cv, b_cv])
    return img_cv2


def main():
    input_picture_path = "../file/input/input_image.jpg"
    output_picture_path = "../file/output/output_image.png"
    add_watermark_to_pic(input_picture_path, output_picture_path)
    input_video_path = "../file/input/input_video.mp4"
    output_video_path = "../file/output/output_video.mp4"
    add_watermark_to_video(input_video_path, output_video_path)


if __name__ == '__main__':
    main()
