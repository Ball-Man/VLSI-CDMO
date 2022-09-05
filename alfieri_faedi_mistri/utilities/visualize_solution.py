"""Visualize an output instance.

Python >= 3.8.
"""
import sys
import re

import pyglet


CIRCUIT_LINE_RE = re.compile(r'[0-9]* [0-9]*')

WINDOW_WIDTH = 500


def show(width, height, n, circuits):
    """Show a window containing visual representation of an instance."""
    circuits_ratio = height / width
    window = pyglet.window.Window(
        WINDOW_WIDTH, int(circuits_ratio * WINDOW_WIDTH))
    # window.width = int(window.height * circuits_ratio)
    batch = pyglet.graphics.Batch()
    offset = 10

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    w_ratio = (window.width - 2 * offset) / width
    h_ratio = (window.height - 2 * offset) / height

    rects = []
    for circuit in circuits:
        c_x = circuit['x'] * w_ratio + offset
        c_y = circuit['y'] * h_ratio + offset
        c_w = circuit['w'] * w_ratio
        c_h = circuit['h'] * h_ratio
        rects.append(pyglet.shapes.BorderedRectangle(
            c_x, c_y, c_w, c_h, batch=batch, border=2,
            border_color=(255, 0, 0)))

    pyglet.clock.schedule(lambda dt: 0)
    pyglet.app.run()


def parse(data: str) -> list[dict]:
    """Parse a string containing output data and return it structured."""
    lines = data.splitlines()

    width, height = map(int, lines[0].split(' '))
    n = lines[1]

    # Filter away incorrect circuit lines
    circuit_lines = filter(CIRCUIT_LINE_RE.match, lines[2:])

    circuit_values = (map(int, line.split(' ')) for line in circuit_lines)
    circuits = [dict(zip(('w', 'h', 'x', 'y'), val)) for val in circuit_values]

    return width, height, n, circuits


def main(filename):
    with open(filename) as fin:
        w, h, n, circuits = parse(fin.read())

    print(f'width: {w}, height: {h}, circuits: {n}')
    show(w, h, n, circuits)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Specify an instance to visualize')
        sys.exit()
    main(sys.argv[1])
