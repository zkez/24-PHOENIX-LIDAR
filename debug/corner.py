import cv2


def onMouse(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        corners, image, original_image = param
        crop_image = original_image[max(0, y - 50):min(original_image.shape[0], y + 50),
                     max(0, x - 50):min(original_image.shape[1], x + 50)].copy()

        cv2.circle(crop_image, (50, 50), 2, (0, 255, 0), -1)

        cv2.imshow("Zoomed Image", crop_image)

    elif event == cv2.EVENT_LBUTTONDOWN:
        corners = param[0]
        corners.append((x, y))
        print("Clicked at:", (x, y))


def main():
    image = cv2.imread("../save_stuff/photos/17.jpg")
    original_image = image.copy()
    corners = []

    cv2.namedWindow("Calibration Image", cv2.WINDOW_NORMAL)
    cv2.imshow("Calibration Image", image)

    cv2.setMouseCallback("Calibration Image", onMouse, (corners, image, original_image))

    while len(corners) < 4:
        cv2.waitKey(10)

    print("Corner Coordinates:")
    for i, corner in enumerate(corners):
        x, y = corner
        x_decimal = round(x / image.shape[1], 4)
        y_decimal = round(y / image.shape[0], 4)
        print("Corner {}: ({}, {})".format(i + 1, x + x_decimal, y + y_decimal))

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
