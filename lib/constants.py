import os

HERE = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
DATA_PATH = HERE + "/data"
LIB = HERE + "/lib"
IMG = HERE + "/images"
IMG_PLN = IMG + "/planimgs"
IMG_ELV = IMG + "/elevations"
IMG_FLRP = IMG + "/floorplans"
IMG_INT = IMG + "/interiors"

DEFUALT_GEOTAG = " "
