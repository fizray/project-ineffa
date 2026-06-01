import cv2


def main() -> None:
    cv2.setLogLevel(0)
    found = []
    for index in range(5):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                found.append(index)
        cap.release()

    cameras = ", ".join(map(str, found)) if found else "none"
    print(f"Detected cameras: {cameras}")


if __name__ == "__main__":
    main()
