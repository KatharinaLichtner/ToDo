#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

# the camera of the wiimote gives its points and the midpoint to be equalized
# after that the related points on the display are returned

# source: jupyter notebook Projective Transformation

import numpy as np


class Transform():

    # following source is to sort a list
    # source: https://stackoverflow.com/questions/37111798/how-to-sort-a-list-of-x-y-coordinates, last visited: 29.06.2018
    def transform(self, P, leds, W, H):

        A = leds[0]
        B = leds[1]
        C = leds[2]
        D = leds[3]

        points = [A, B, C, D]
        points = sorted(points, key=lambda k: k[0])

        if points[0][1] < points[1][1]:
            A = points[0]
            B = points[1]
        else:
            A = points[1]
            B = points[0]

        if points[2][1] < points[3][1]:
            D = points[2]
            C = points[3]
        else:
            D = points[3]
            C = points[2]

        self.source_points_123 = np. matrix([[A[0], B[0], C[0]], [A[1], B[1], C[1]], [1, 1, 1]])
        self.source_point_4 = [[D[0]], [D[1]], [1]]

        scale_to_source = np.linalg.solve(self.source_points_123, self.source_point_4)
        l, m, t = [float(x) for x in scale_to_source]

        unit_to_source = np.matrix([[l * A[0], m * B[0], t * C[0]], [l * A[1], m * B[1], t * C[1]], [l, m, t]])

        DESTINATION_SCREEN_WIDTH = W
        DESTINATION_SCREEN_HEIGHT = H

        A2 = 0, DESTINATION_SCREEN_HEIGHT
        B2 = 0, 0
        C2 = DESTINATION_SCREEN_WIDTH, 0
        D2 = DESTINATION_SCREEN_WIDTH, DESTINATION_SCREEN_HEIGHT

        dest_points_123 = np.matrix([[A2[0], B2[0], C2[0]], [A2[1], B2[1], C2[1]], [1, 1, 1]])

        dest_point_4 = np.matrix([[D2[0]], [D2[1]], [1]])

        scale_to_dest = np.linalg.solve(dest_points_123, dest_point_4)
        l, m, t = [float(x) for x in scale_to_dest]

        unit_to_dest = np.matrix([[l * A2[0], m * B2[0], t * C2[0]], [l * A2[1], m * B2[1], t * C2[1]], [l, m, t]])

        source_to_unit = np.linalg.inv(unit_to_source)
        source_to_dest = unit_to_dest @ source_to_unit

        x, y, z = [float(w) for w in (source_to_dest @ np.matrix([[512], [384], [1]]))]

        x = x / z
        y = y / z
        return x, y
