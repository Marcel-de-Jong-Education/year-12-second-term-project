"""CLI tool for generating noise"""

# ----------------Dependencies---------------- #

import sys
import random as r
from enum import StrEnum

import inquirer
from time import time
from PIL import Image
from numpy import (
    array,
    zeros,
    zeros_like,
    stack,
    uint8
    )

# ----------------Definitions---------------- #

class Noise(StrEnum): # Not a typical python class, enums are special
    """Enumerates noise types to ensure type-safety."""
    WHITE = "WHITE"
    BLOBBY = "BLOBBY"
    PERLIN = "PERLIN"




def box_blur(value_matrix: list, repetitions: int = 1, total: int = 1) -> list: # total is just for UX and technically unnecessary. Total should always == repetitions except in recursions.
    """A recursive blurring function that averages a ring around each point."""
    blur = []
    for y in range(len(value_matrix)):
        line = []

        for x in range(len(value_matrix[y])):
            count = 1
            value = int(value_matrix[y][x])
            try:
                value += value_matrix[y-1][x] # up
                count += 1
            except:
                pass

            try:
                value += value_matrix[y][x-1] # left
                count += 1
            except:
                pass

            try:
                value += value_matrix[y+1][x] # down
                count += 1
            except:
                pass

            try:
                value += value_matrix[y][x+1] # right
                count += 1
            except:
                pass

            try:
                value += value_matrix[y-1][x-1] # up-left
                count += 1
            except:
                pass

            try:
                value += value_matrix[y+1][x-1] # down-left
                count += 1
            except:
                pass

            try:
                value += value_matrix[y+1][x+1] # down-right
                count += 1
            except:
                pass

            try:
                value += value_matrix[y-1][x+1] # up-right
                count += 1
            except:
                pass

            value /= count

            line.append(value)

        blur.append(line)

    if repetitions <= 1:
        return blur
    else:
        repetitions -= 1
        if not repetitions % 0x10: print(f'{total - repetitions}/{total}')
        return box_blur(blur, repetitions, total)



def gaussian_blur(value_matrix: list) -> list:
    """Applies a gaussian blur."""
    gh



def glowblur(value_matrix: list, brightness_multiplier: float = 1.0):
    """Iterates over every pixel and evaluates the brightness based on distance to sources."""
    brightness_multiplier = 1/brightness_multiplier
    # find sources
    sources = []
    for y in range(len(value_matrix)):

        for x in range(len(value_matrix[y])):

            if value_matrix[y][x] == 0xFF:
                sources.append([x,y])

    for y in range(len(value_matrix)):

        for x in range(len(value_matrix[y])):
            if value_matrix != 0xFF: # prevent value exceeding 255
                for source in sources:
                    dy = y - source[1]
                    dx = x - source[0]
                    distance = (dy**2 + dx**2)**0.5 + 1 # c = sqrt(a^2 + b^2), +1 to avoid div by 0

                    value_matrix[y][x] += int(255.0/((distance**2)*brightness_multiplier))
                    value_matrix[y][x] = min(value_matrix[y][x], 0xFF) # clamping

    return value_matrix




def generate_noise(width: int, height: int, noise_type: StrEnum = Noise.WHITE, density_percent: float = 2.0, spread_distance: int = 2,) -> list:
    """Generates a 2D matrix of noise of a given type."""
    matrix = []

    match noise_type:
        case Noise.WHITE:
            for y in range(height):
                line = []

                for x in range(width):
                    line.append(r.randint(0x00, 0xFF))

                matrix.append(line)

            return matrix


        case Noise.BLOBBY:

            origins = []

            for y in range(height):
                line = []

                for x in range(width):
                    if float(r.randint(1,100000))/1000 <= density_percent:
                        line.append(0xFF)
                        origins.append([x,y])
                    else:
                        line.append(0)

                matrix.append(line)

            # Spread noise
            # Note: slows down EXTREMELY fast. Needs optimisation

            for i in range(spread_distance):
                current_origins = list(origins) # Avoid TOCTOU
                origins = [] # prevent re-running on old points, massive optimisation
                for point in current_origins:
                    try:
                        matrix[point[1]-1][point[0]] = 0xFF # up
                        origins.append([point[0], point[1]-1])
                    except:
                        pass

                    try:
                        matrix[point[1]][point[0]-1] = 0xFF # left
                        origins.append([point[0]-1, point[1]])
                    except:
                        pass

                    try:
                        matrix[point[1]+1][point[0]] = 0xFF # down
                        origins.append([point[0], point[1]+1])
                    except:
                        pass

                    try:
                        matrix[point[1]][point[0]+1] = 0xFF # right
                        origins.append([point[0]+1, point[1]])
                    except:
                        pass

            # blur
            matrix = box_blur(value_matrix=matrix, repetitions=192, total=192) # ~1 second per 20 repetitions at 256x256

            return matrix

        case Noise.PERLIN:
            print('Perlin!')
            return matrix

        case _: # This should REALLY never run.
            print(f'Invalid type {noise_type}!')
            raise ValueError
            return matrix




def noise_to_text(value_matrix: list) -> str:
    """Converts a 2D matrix of integers into a text map with intensity-reflective colouring."""
    gradient_characters = ["██", "▓▓", "▒▒", "░░", "  "]
    output = "\n"

    for y in range(len(value_matrix)):

        for x in range(len(value_matrix[y])):
            if value_matrix[y][x] > 205:
                output += gradient_characters[0]
            elif value_matrix[y][x] > 155:
                output += gradient_characters[1]
            elif value_matrix[y][x] > 105:
                output += gradient_characters[2]
            elif value_matrix[y][x] > 55:
                output += gradient_characters[3]
            else:
                output += gradient_characters[4]

        output += '\n'

    return output


def noise_to_terrain(noise_matrix: list, sea_level: int = 196): # this made me hate myself so much why is documentation so painful to readddddd
    """Colours noise to look like terrain"""
    noise = array(noise_matrix, dtype=uint8)

    height, width = noise.shape
    terrain = zeros((height, width, 3), dtype=uint8)

    # masks
    water = noise < sea_level
    beach = (noise >= sea_level) & (noise < sea_level + 4)
    land = noise >= sea_level + 4

    # actual colouring
    terrain[water] = [0, 0, 128] # water
    terrain[beach] = [255, 192, 192] # beach
    terrain[land] = [32, 128, 32] # land

    return terrain



def interactive_selection() -> Noise:
    """Uses the inquirer module and user input to select an mode via the CLI"""
    question = [
        inquirer.List(
            "Noise Type",
            message="Select a noise type",
            choices=["White Noise", "Blobby Noise", "Perlin Noise"],
        )
    ]
    answer = inquirer.prompt(question)["Noise Type"]
    print(f"Selection: {answer}")
    match answer:
        case "White Noise":
            return Noise.WHITE

        case "Blobby Noise":
            return Noise.BLOBBY

        case "Perlin Noise":
            return Noise.PERLIN

        case _:
            raise ValueError("Script malfunction: Prompt returned an unexpected value.") # This line *should* never run




# ----------------Script---------------- #

def main() -> int:
    """Runs the script."""
    try:
        noise_selection = interactive_selection()
    except ValueError:
        return 1

    start = time()
    noise_map = generate_noise(
        width=256,
        height=256,
        noise_type=noise_selection,
        density_percent=0.8,
        spread_distance=3
        )
    end = time()
    print(f'Time to generate noise: {end-start}\n')


    if noise_selection == Noise.BLOBBY:
        terrain = noise_to_terrain(noise_matrix=noise_map, sea_level=32) # sea_level is from 0->255
        img = Image.fromarray(terrain, mode="RGB")
        img.show()
    else:
        print(noise_to_text(noise_map))
    return 0


if __name__ == "__main__":
    sys.exit(main())
