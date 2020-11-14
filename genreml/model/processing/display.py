# Name: display.py
# Description: defines common display functionality for matplot graphics

import matplotlib.pyplot as plt
import numpy as np

from genreml.model.processing.config import DisplayConfig


class VisualDataMixin(object):
    """ Defines common functionality for visualization of features """

    @staticmethod
    def normalize(visual_data: np.array) -> np.array:
        return 255 * ((visual_data - visual_data.min()) /
                      (visual_data.max() - visual_data.min()))

    @staticmethod
    def convert_pixels_to_8_bits(visual_data: np.array) -> np.array:
        return visual_data.astype(np.uint8)

    @staticmethod
    def flip_and_invert(visual_data: np.array) -> np.array:
        flipped_img = np.flip(visual_data, axis=0)
        return 255 - flipped_img

    @staticmethod
    def create_display_figure(frameon: bool = False, display_axes: bool = False,
                              x_axis_name: str = None, y_axis_name: str = None,
                              figure_width: float = DisplayConfig.FIGSIZE_WIDTH,
                              figure_height: float = DisplayConfig.FIGSIZE_HEIGHT) -> tuple:
        print("Creating display figure with {0},{1}".format(figure_width, figure_height))
        fig = plt.figure(frameon=frameon, figsize=(figure_width, figure_height))
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        if not display_axes:
            ax.set_axis_off()
        else:
            ax.set(xlabel=x_axis_name, ylabel=y_axis_name)
        fig.add_axes(ax)
        return fig, ax

    @staticmethod
    def display_data(
            visual_data: np.array, frameon: bool = False, cmap: str = DisplayConfig.CMAP,
            display_axes: bool = False, x_axis_name: str = None, y_axis_name: str = None,
            figure_width: float = DisplayConfig.FIGSIZE_WIDTH, figure_height: float = DisplayConfig.FIGSIZE_HEIGHT
    ) -> plt.figure:
        """ Displays the given data in a matplotlib figure and returns the figure object """
        fig, ax = VisualDataMixin.create_display_figure(
            frameon, display_axes, x_axis_name, y_axis_name, figure_width=figure_width, figure_height=figure_height)
        ax.imshow(visual_data, aspect='auto', cmap=cmap)
        return fig

    @staticmethod
    def close_img(fig: plt.figure) -> None:
        """ Closes a matplotlib figure """
        plt.close(fig)
