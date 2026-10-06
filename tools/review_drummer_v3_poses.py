"""Render nine isolated states using exactly the production preview compositor."""
from pathlib import Path
import argparse
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from tools.render_drummer_v3_preview import TARGETS, LABELS, load_component_masks, compose_lighting, _content_crop


def render_review(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    source, masks = load_component_masks()
    states = [None, *TARGETS]
    sheet = Image.new('RGB', (1440, 1050), '#090d15')
    frames = []
    for i, target in enumerate(states):
        art = compose_lighting(source, masks, [] if target is None else [target]).crop(_content_crop(source))
        art.thumbnail((460, 300), Image.Resampling.LANCZOS)
        tile = Image.new('RGB', (480, 350), '#090d15')
        tile.paste(art, ((480-art.width)//2, 42))
        ImageDraw.Draw(tile).text((14, 12), 'IDLE' if target is None else LABELS[target], fill='white', font=ImageFont.load_default(size=20))
        sheet.paste(tile, ((i%3)*480, (i//3)*350))
        frames.append(tile.resize((960, 700), Image.Resampling.LANCZOS))
    sheet.save(output/'Drummer_Pose_Review.png')
    path = output/'Drummer_Pose_Review.mp4'
    with imageio.get_writer(path, fps=24, codec='libx264', quality=9, macro_block_size=None) as writer:
        for frame in frames:
            for _ in range(48):
                writer.append_data(np.asarray(frame))
    # Decode one frame per pose from the delivered file, so review includes encoding.
    decoded = Image.new('RGB', sheet.size, '#090d15')
    with imageio.get_reader(path) as reader:
        for i in range(9):
            im = Image.fromarray(reader.get_data(i*48+24)).resize((480,350))
            decoded.paste(im, ((i%3)*480,(i//3)*350))
    decoded.save(output/'Drummer_Pose_Decoded.png')
    return {'states':len(states),'seconds_per_state':2,'mp4':str(path)}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    print(render_review(parser.parse_args().output))
