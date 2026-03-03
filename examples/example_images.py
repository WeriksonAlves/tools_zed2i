# examples/example_images.py
from __future__ import annotations

import time

from tools_zed2i import ZED2i


def main() -> None:
    # Ajuste o caminho do YAML conforme sua estrutura
    zed = ZED2i.from_yaml("configs/zed2i_images.yaml")

    zed.start()
    zed.start_image_streams()

    for i in range(20):
        left = zed.get_last_left_image()
        print(f"[{i}] Left image:", "received" if left is not None else "None")

        # Se quiser testar gravação "fake":
        zed.save_placeholder_frame(i)

        time.sleep(0.2)

    zed.stop()


if __name__ == "__main__":
    main()
