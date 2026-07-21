import hashlib


def sha256_file(filename):

    sha = hashlib.sha256()

    with open(filename, "rb") as f:

        while True:

            data = f.read(1024 * 1024)

            if not data:
                break

            sha.update(data)

    return sha.hexdigest()