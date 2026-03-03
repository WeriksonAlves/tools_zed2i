# examples/example_minimal.py
from tools_zed2i import ZED2i


def main() -> None:
    zed = ZED2i.from_yaml("configs/zed2i_pointcloud.yaml")

    zed.start()                 # inicia ROS2 em thread separada
    zed.start_pointcloud_stream()

    # Aqui poderia ser um loop do seu experimento/principal
    import time

    for _ in range(10):
        cloud = zed.get_last_pointcloud()
        print("Last cloud:", type(cloud))
        time.sleep(0.2)

    zed.stop()


if __name__ == "__main__":
    main()
