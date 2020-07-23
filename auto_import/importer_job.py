#!/usr/bin/env python

"""Auto import script from a user directory
"""


import os
import json
import logging
import shutil
import subprocess
from datetime import date

from pathlib import Path

import yaml
import numpy as np
import omero
from omero.util import import_candidates
from omero.cli import CLI

log = logging.getLogger(__name__)


def get_configuration(pth):
    """walks up from the directory 'pth' until a file named omero_userconf.yml is found.

    Returns a dictionnary from the parsed file.

    Parameters
    ----------
    pth: string or Path
         the path from which to search the configuration file

    Returns
    -------
    conf: dict

    For example:

    .. code::
        {'base_path': 'User data root directory',
         'group': 'Prof Prakash',
         'password': 'XXXXX',
         'port': '4064',
         'project': 'Default Project',
         'server': 'omero.server.example.com',
         'username': 'E.Erhenfest'}


    Raises
    ------
    FileNotFoundError if there is no omero_userconf.yml in the file system

    """
    pth = Path(pth)
    conf = pth / "omero_userconf.yml"
    if conf.is_file():
        print(f"using {conf.absolute().as_posix()}")
        with open(conf, "r") as f:
            return yaml.safe_load(f)

    for parent in pth.parents:
        conf = parent / "omero_userconf.yml"
        if conf.is_file():
            print(f"using {conf.absolute().as_posix()} configuration file")
            with open(conf, "r") as f:
                return yaml.safe_load(f)
    else:
        raise FileNotFoundError("User configuration file not found")


def get_annotations(pth):
    """Walks up from the directory 'pth' until a file named omero_annotations.csv is found.

    Returns a numpy array from the parsed file.

    Parameters
    ----------
    pth: string or Path
         the path from which to search the configuration file

    Returns
    -------
    annotations: np.ndarray of shape (n, 2)
         key-value pairs to annotate the images with


    """

    ann = pth / "omero_annotations.csv"
    if ann.is_file():
        print(f"using {ann.absolute().as_posix()} annotation file")
        annotations = np.loadtxt(ann, dtype="object", delimiter=",")
        return annotations

    for parent in pth.parents:
        ann = parent / "omero_annotations.csv"
        if ann.is_file():
            print(f"using {ann.absolute().as_posix()} annotation file")
            annotations = np.loadtxt(ann, dtype="object", delimiter=",")
            return annotations
    else:
        log.info("No annotation file named omero_annotations.csv was found")
        return np.empty((0, 2))


def create_bulk_yml(**kwargs):
    """Creates the bulk.yml file in the current directory

    Any keyword argument will update the default setting.

    See https://docs.openmicroscopy.org/omero/5.6.2/users/cli/import-bulk.html
    for more info

    Defaults
    --------

    "path": "files.tsv",
    "columns": ["target", "name", "path"],
    "continue": True,
    "exclude": "clientpath",
    "checksum_algorithm": "CRC-32",

    Example
    -------

    # create a bulk.yml file that will result in a dry-run
    >>> create_bulk_yml(dry_run=True)

    """

    bulk_opts = {
        "path": "files.tsv",
        "columns": ["target", "name", "path"],
        "continue": True,
        "exclude": "clientpath",
        "checksum_algorithm": "CRC-32",
    }
    bulk_opts.update(kwargs)

    log.debug(f"bulk options: {bulk_opts}")
    with open("bulk.yml", "w") as yml_file:
        yaml.dump(bulk_opts, yml_file)


def create_bulk_tsv(candidates, base_path, conf):

    lines = []
    last_project = ""

    # group candidates by directory
    paths = sorted(candidates, key=lambda p: Path(p).parent.as_posix())
    for fullpath in paths:
        parts = Path(fullpath).relative_to(base_path).parts
        if len(parts) == 1:
            project = conf.get("project", "no_project")
            dataset = date.today().isoformat()
            name = parts[0].replace(" ", "_")

        elif len(parts) == 2:
            project = parts[0].replace(" ", "_")
            dataset = date.today().isoformat()
            name = parts[1].replace(" ", "_")

        elif len(parts) == 3:
            project = parts[0].replace(" ", "_")
            dataset = parts[1].replace(" ", "_")
            name = parts[2].replace(" ", "_")

        else:
            project = parts[0].replace(" ", "_")
            dataset = parts[1].replace(" ", "_")
            name = "-".join(parts[2:]).replace(" ", "_")

        if project == last_project:
            ## use the latest existing dataset
            target = f'Project:name:"{project}"/Dataset:+name:"{dataset}"'
        else:
            ## create a new dataset
            target = f'Project:name:"{project}"/Dataset:@name:"{dataset}"'
            last_project = project

        lines.append("\t".join((target, name, fullpath + "\n")))

    with open("files.tsv", "w") as f:
        f.writelines(lines)


def auto_import(directory, dry_run=False, reset=True):

    directory = Path(directory)

    conf = get_configuration(directory)
    create_bulk_yml(dry_run=dry_run)
    base_path = conf.get("base_path", directory.as_posix())

    if not Path("files.tsv").is_file() or reset:
        candidates = import_candidates.as_dictionary(directory.as_posix())
        create_bulk_tsv(candidates, base_path, conf)

    cmd = [
        "import",
        "-s",
        conf["server"],
        "-p",
        conf["port"],
        "-u",
        conf["username"],
        "-w",
        conf["password"],
        "-g",
        conf["group"],
        "--file",
        Path("out.txt").absolute().as_posix(),
        "--errs",
        Path("err.txt").absolute().as_posix(),
        "--bulk",
        "bulk.yml",
    ]
    cli = CLI()
    cli.loadplugins()
    cli.invoke(cmd)
    return candidates

    # print(cmd)


def auto_annotate(candidates):

    paths = sorted(candidates, key=lambda p: Path(p).parent.as_posix())
    for fullpath in paths:
        annotations = get_annotations(fullpath)
        if annotations.shape[0]:
            pass
    # TODO


def clean():

    # TODO
    pass
