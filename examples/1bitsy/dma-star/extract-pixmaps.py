#!/usr/bin/env python3

from itertools import groupby
import sys

import PIL.Image

white_pixel = 255

img = PIL.Image.open('pixmaps/text-snips.png')
gray = img.convert('L')
pix = gray.load()
w, h = gray.size

def row_is_blank(row):
    return all(pix[i, row] == white_pixel for i in range(w))

def col_is_blank(col):
    return all(pix[col, i] == white_pixel for i in range(h))

left = 0
while left < w and col_is_blank(left):
    left += 1

right = w
while right > left and col_is_blank(right - 1):
    right -= 1

regions = []

active = False
for row in range(h):
    if row_is_blank(row):
        if active:
            active = False
            active_height = row - start
            regions.append((start, row))
    else:
        if not active:
            active = True
            start = row

assert len(regions) == 7
region_width = right - left
region_height = regions[0][1] - regions[0][0]
region_size = region_height * region_width
assert all(reg[1] - reg[0] == region_height for reg in regions)

reg_img = [gray.crop((left, reg[0], right, reg[1],)) for reg in regions]

def get_data(img):
    return [list(255 - b for (i, b) in row)
            for (g, row) in groupby(enumerate(img.getdata()),
                                    lambda x: x[0] // region_width)]

reg_data = [get_data(img) for img in reg_img]

region_map = {
    0: 'pb2aa',
    1: 'pb2fade',
    2: 'pb2fill',
    3: 0,
    4: 1,
    5: 'pb4more',
    6: 'pb4less',
}

for k in region_map:
    v = region_map[k]
    if isinstance(v, int):
        assert reg_img[k] == reg_img[v]
        assert reg_img[k] != reg_img[v+1]
        # print('img[{}] == img[{}]'.format(k, v))

template = '''
#ifndef PIXMAPS_included
#define PIXMAPS_included

/* This file was automatically generated by {program}.  Do not edit. */

#include <stdint.h>

#define TEXT_PIXMAP_WIDTH {width}
#define TEXT_PIXMAP_HEIGHT {height}

typedef uint8_t text_pixmap[{height}][{width}];

{definitions}
#endif /* !PIXMAPS_included */
'''.lstrip()

pixmap_template = r'''
// static const uint8_t {name}[{height}][{width}] = {{
static const text_pixmap {name} = {{
{bytes}
}};
'''.lstrip()

def by_n(n, seq):
    return ((x for (i, x) in g)
            for (k, g) in groupby(enumerate(seq), lambda x: x[0] // n))

def format_map(index, name):
    pixels = reg_data[index]
    s = ',\n'.join('    {{ {} }}'
                   .format(',\n      '.join(', '.join('{:3d}'.format(b)
                                                     for b in line)
                                           for line in by_n(12, row)))
                   for row in pixels)
    return pixmap_template.format(name=name,
                                  height=region_height,
                                  width=region_width,
                                  bytes=s)

defs = '\n\n'.join(
    format_map(index, name)
    for (index, name) in region_map.items()
    if isinstance(name, str))

print(template.format(program=sys.argv[0],
                      width=region_width,
                      height=region_height,
                      definitions=defs))

