import string
import random


CHARS = string.ascii_lowercase + string.digits


def generate_random_string(length):
    return ''.join(random.choices(CHARS, k=length))
