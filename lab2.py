import sys
import math
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QGridLayout, QMessageBox,
    QFileDialog
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


def numpy_to_qpixmap(arr):
    arr = np.ascontiguousarray(arr.astype(np.uint8))
    h, w, _ = arr.shape
    qimg = QImage(arr.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


def load_image(path):
    qimg = QImage(path)
    if qimg.isNull():
        raise ValueError(f"Не удалось загрузить: {path}")
    qimg = qimg.convertToFormat(QImage.Format.Format_RGB888)
    w = qimg.width()
    h = qimg.height()
    ptr = qimg.bits()
    ptr.setsize(qimg.sizeInBytes())
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape(
        (h, qimg.bytesPerLine() // 3, 3)
    )
    return arr[:, :w, :].copy()


def draw_line(img, x1, y1, x2, y2, color):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    h, w = img.shape[:2]
    while True:
        if 0 <= x1 < w and 0 <= y1 < h:
            img[y1, x1] = color
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def to_pbm_text(img):
    h, w = img.shape[:2]
    gray = (0.2125 * img[:, :, 0] +
            0.7154 * img[:, :, 1] +
            0.0721 * img[:, :, 2])
    bits = (gray < 128).astype(int)
    lines = ["P1", f"{w} {h}"]
    for row in bits:
        lines.append(" ".join(str(b) for b in row))
    return "\n".join(lines) + "\n"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЛР №2 — Вариант 5")
        self.resize(1300, 750)

        self.image1 = None
        self.image2 = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        params = QGridLayout()
        params.setHorizontalSpacing(6)
        params.setVerticalSpacing(8)

        params.addWidget(QLabel("Width 1:"), 0, 0)
        self.edit_w1 = QLineEdit("300")
        self.edit_w1.setFixedWidth(60)
        params.addWidget(self.edit_w1, 0, 1)

        self.btn_create = QPushButton("Создать")
        params.addWidget(self.btn_create, 0, 2)

        self.btn_open = QPushButton("Открыть")
        params.addWidget(self.btn_open, 0, 3)

        params.addWidget(QLabel("Ширина фраг.:"), 0, 4)
        self.edit_frag_w = QLineEdit("120")
        self.edit_frag_w.setFixedWidth(50)
        params.addWidget(self.edit_frag_w, 0, 5)

        params.addWidget(QLabel("Высота фраг.:"), 0, 6)
        self.edit_frag_h = QLineEdit("40")
        self.edit_frag_h.setFixedWidth(50)
        params.addWidget(self.edit_frag_h, 0, 7)

        self.btn_move = QPushButton("Перенести")
        params.addWidget(self.btn_move, 0, 8)

        self.btn_axes = QPushButton("Координаты")
        params.addWidget(self.btn_axes, 0, 9)

        self.btn_exp = QPushButton("exp(x)")
        params.addWidget(self.btn_exp, 0, 10)

        self.btn_save = QPushButton("Сохранить")
        params.addWidget(self.btn_save, 0, 11)

        self.btn_save_pbm = QPushButton("Сохранить в PBM")
        params.addWidget(self.btn_save_pbm, 0, 12)

        params.addWidget(QLabel("Height 1:"), 1, 0)
        self.edit_h1 = QLineEdit("300")
        self.edit_h1.setFixedWidth(60)
        params.addWidget(self.edit_h1, 1, 1)

        root.addLayout(params)

        images_row = QHBoxLayout()

        self.lb2_image1 = QLabel("Новое изображение (image 1)")
        self.lb2_image1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb2_image1.setMinimumSize(300, 300)
        self.lb2_image1.setStyleSheet("QLabel { border: 1px solid #888; }")

        self.lb2_image2 = QLabel("Исходное изображение (image 2)")
        self.lb2_image2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb2_image2.setMinimumSize(300, 300)
        self.lb2_image2.setStyleSheet("QLabel { border: 1px solid #888; }")

        images_row.addWidget(self.lb2_image1, 1)
        images_row.addWidget(self.lb2_image2, 1)
        root.addLayout(images_row)

        self.btn_create.clicked.connect(self.on_create)
        self.btn_open.clicked.connect(self.on_open)
        self.btn_move.clicked.connect(self.on_move)
        self.btn_axes.clicked.connect(self.on_axes)
        self.btn_exp.clicked.connect(self.on_exp)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_save_pbm.clicked.connect(self.on_save_pbm)

    def refresh_image1(self):
        if self.image1 is None:
            return
        pix = numpy_to_qpixmap(self.image1)
        self.lb2_image1.setPixmap(
            pix.scaled(
                self.lb2_image1.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def refresh_image2(self):
        if self.image2 is None:
            return
        pix = numpy_to_qpixmap(self.image2)
        self.lb2_image2.setPixmap(
            pix.scaled(
                self.lb2_image2.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def on_create(self):
        try:
            w = int(self.edit_w1.text())
            h = int(self.edit_h1.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка",
                                "Ширина и высота должны быть целыми числами")
            return

        if w <= 0 or h <= 0:
            QMessageBox.warning(self, "Ошибка",
                                "Ширина и высота должны быть больше нуля")
            return

        self.image1 = np.full((h, w, 3), 255, dtype=np.uint8)
        self.refresh_image1()

    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть изображение", "",
            "Изображение (*.png *.jpg *.jpeg *.bmp *.ppm *.pgm *.tif *.tiff)"
        )
        if not path:
            return
        try:
            self.image2 = load_image(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        self.refresh_image2()

    def on_move(self):
        if self.image1 is None:
            QMessageBox.warning(self, "Внимание",
                                "Сначала создайте новое изображение")
            return
        if self.image2 is None:
            QMessageBox.warning(self, "Внимание",
                                "Сначала откройте исходное изображение")
            return

        try:
            frag_w = int(self.edit_frag_w.text())
            frag_h = int(self.edit_frag_h.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка",
                                "Размеры фрагмента должны быть целыми числами")
            return

        if frag_w <= 0 or frag_h <= 0:
            QMessageBox.warning(self, "Ошибка",
                                "Размеры фрагмента должны быть больше нуля")
            return

        h1, w1 = self.image1.shape[:2]
        h2, w2 = self.image2.shape[:2]

        xc_dst = w1 // 2
        yc_dst = h1 // 2
        xc_src = w2 // 2
        yc_src = h2 // 2

        half_w = frag_w // 2
        half_h = frag_h // 2

        THICK = 1

        for py in range(yc_src - half_h, yc_src + half_h + 1):
            for px in range(xc_src - half_w, xc_src + half_w + 1):
                if not (0 <= px < w2 and 0 <= py < h2):
                    continue

                dx_src = abs(px - xc_src)
                dy_src = abs(py - yc_src)

                on_border = ((half_w - THICK < dx_src <= half_w) or
                             (half_h - THICK < dy_src <= half_h))

                if on_border:
                    self.image2[py, px] = [255, 0, 0]
                else:
                    dx = px - xc_src
                    dy = py - yc_src
                    tx = xc_dst + dx
                    ty = yc_dst + dy
                    if 0 <= tx < w1 and 0 <= ty < h1:
                        self.image1[ty, tx] = self.image2[py, px]

        self.refresh_image1()
        self.refresh_image2()

    def on_axes(self):
        if self.image1 is None:
            QMessageBox.warning(self, "Внимание",
                                "Сначала создайте новое изображение")
            return

        h, w = self.image1.shape[:2]
        color = [0, 0, 0]

        oy_x = 10
        ox_y = h // 2

        draw_line(self.image1, oy_x, h - 10, oy_x, 10, color)
        draw_line(self.image1, oy_x, 10, oy_x - 5, 20, color)
        draw_line(self.image1, oy_x, 10, oy_x + 5, 20, color)

        draw_line(self.image1, oy_x - 2, ox_y, w - 10, ox_y, color)
        draw_line(self.image1, w - 10, ox_y, w - 20, ox_y - 5, color)
        draw_line(self.image1, w - 10, ox_y, w - 20, ox_y + 5, color)

        for x in range(oy_x + 10, w - 10, 10):
            draw_line(self.image1, x, ox_y, x, ox_y + 3, color)

        for y in range(ox_y - 10, 10, -10):
            draw_line(self.image1, oy_x, y, oy_x + 3, y, color)

        self.refresh_image1()

    def on_exp(self):
        if self.image1 is None:
            QMessageBox.warning(self, "Внимание",
                                "Сначала создайте новое изображение")
            return

        h, w = self.image1.shape[:2]
        ox_y = h // 2
        oy_x = 10
        color = [127, 127, 255]

        x_max_by_width = (w - 20) / 10.0

        y_max_pixels = ox_y - 20
        if y_max_pixels < 2:
            y_max_pixels = 2
        x_max_by_height = math.log(y_max_pixels)

        x_max = min(x_max_by_width, x_max_by_height)

        prev_px = None
        prev_py = None
        steps = int(x_max * 10) + 1
        for i in range(steps):
            x_val = i / 10.0
            y_val = math.exp(x_val)
            px = oy_x + i
            py = ox_y - int(round(y_val))
            if 0 <= px < w and 0 <= py < h:
                if prev_px is not None:
                    draw_line(self.image1, prev_px, prev_py, px, py, color)
                else:
                    self.image1[py, px] = color
                prev_px, prev_py = px, py

        self.refresh_image1()

    def on_save(self):
        if self.image1 is None:
            QMessageBox.warning(self, "Внимание", "Нечего сохранять")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результат", "result.png",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        if path:
            numpy_to_qpixmap(self.image1).save(path)

    def on_save_pbm(self):
        if self.image1 is None:
            QMessageBox.warning(self, "Внимание", "Нечего сохранять")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в PBM", "result.pbm",
            "PBM (*.pbm)"
        )
        if path:
            if not path.lower().endswith(".pbm"):
                path += ".pbm"
            with open(path, "w", encoding="ascii") as f:
                f.write(to_pbm_text(self.image1))


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()