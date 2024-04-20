import cv2


def find_chessboard_corners(image_path):
    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    chessboard_size = (8, 6)

    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

    if ret:
        cv2.drawChessboardCorners(image, chessboard_size, corners, ret)

        top_left = tuple(corners[0][0])
        top_right = tuple(corners[chessboard_size[0] - 1][0])
        bottom_right = tuple(corners[-1][0])
        bottom_left = tuple(corners[-chessboard_size[0]][0])

        return top_left, top_right, bottom_right, bottom_left

    else:
        print("Chessboard corners not found!")
        return None


def main():
    image_path = "../save_stuff/photos/0.jpg"
    top_left, top_right, bottom_right, bottom_left = find_chessboard_corners(image_path)

    if top_left is not None:
        print("Top Left Corner:", top_left)
        print("Top Right Corner:", top_right)
        print("Bottom Right Corner:", bottom_right)
        print("Bottom Left Corner:", bottom_left)
    else:
        print("Failed to find chessboard corners.")


if __name__ == "__main__":
    main()
