import subprocess
import imageio_ffmpeg

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([
    ffmpeg, "-y", "-i", "results/motor_3d.mp4",
    "-vf", "fps=8,scale=560:-1:flags=lanczos,split[a][b];"
           "[a]palettegen=max_colors=64[p];[b][p]paletteuse",
    "results/motor_3d_small.gif",
], check=True)
print("Saved results/motor_3d_small.gif")