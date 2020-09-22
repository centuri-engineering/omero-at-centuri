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
from omero.gateway import (
    BlitzGateway,
    TagAnnotationWrapper,
    MapAnnotationWrapper,
    CommentAnnotationWrapper,
)

from omero.util import import_candidates
from omero.cli import CLI

log = logging.getLogger(__name__)
logfile = logging.FileHandler("auto_importer.log")
log.setLevel("INFO")
log.addHandler(logfile)


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
    raise FileNotFoundError("User configuration file not found")


def collect_annotations(base_dir):

    base_dir = Path(base_dir)
    annotations = base_dir.glob("**/omero_annotation.yml")


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

    if not Path("files.tsv").is_file() or reset:
        candidates = import_candidates.as_dictionary(directory.as_posix())
        create_bulk_tsv(candidates, directory, conf)

    all_ymls = directory.glob("**/*.yml")
    annotation_ymls = [yml for yml in all_ymls if _is_annotation(yml)]
    annotation_dirs = [yml.parent for yml in annotation_ymls]

    for annotation_yml in annotation_ymls:
        import_and_annotate(conf, annotation_yml)


def _is_annotation(yml):
    with open(yml, "r") as fh:
        return "# omero annotation file" in fh.readline()


def import_and_annotate(conf, annotation_yml):

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
    auto_annotate(conf, "out.txt", annotation_yml)


def auto_annotate(conf, out_file, annotation_yml):

    conn = BlitzGateway(
        conf["username"], conf["password"], host=conf["server"], port=conf["port"]
    )
    conn.connect()
    datasets = get_datasets(conn, out_file)
    for dataset_id in datasets:
        annotate(conn, dataset_id, annotation_yml)


def get_datasets(conn, out_file):

    datasets = []

    with open(out_file, "r") as out:
        for line in out:
            if not line.startswith("Image"):
                continue
            if "," in line:
                line = line.split(",")[0]
            im_id = int(line.split(":")[1])
            datasets.append(conn.getObject("Image", im_id).getParent().getId())
    return set(datasets)


def annotate(conn, dataset_id, annotation_yml):
    """Applies the annotations in `annotation_yml` to the dataset

    Parameters
    ----------
    conn: An `omero.gateway.BlitzGateway` connection
    dataset_id: int - the Id of the dataset to annotate
    annnotation_yml: str or `Path` a yml file containing the annotation

    """
    dataset = conn.GetObject("Dataset", dataset_id)
    log.info(f"\n")
    log.info(f"Annotating dataset {dataset_id}")

    with Path(annotation_yml).open("r") as ann_yml:
        ann = yaml.safe_load(ann_yml)

    key_value_pairs = list(ann.get("kv_pairs", {}).items())
    if key_value_pairs:
        log.info("Map annotations: ")
        log.info("\n".join([f"{k}: {v}" for k, v in key_value_pairs]))
        map_ann = MapAnnotationWrapper(conn)
        namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
        map_ann.setNs(namespace)
        map_ann.setValue(key_value_pairs)
        map_ann.save()
        dataset.linkAnnotation(map_ann)

    for tag in ann.get("tags", []):
        log.info(f"Adding tag: {tag}")
        tag_ann = TagAnnotationWrapper(conn)
        tag_ann.setValue(tag)
        tag_ann.save()
        dataset.linkAnnotation(tag_ann)

    comment = ann.get("comment", "")
    if comment:
        log.info(f"Adding comment: {comment}")
        com_ann = CommentAnnotationWrapper(conn)
        com_ann.setValue(comment)
        com_ann.save()
        dataset.linkAnnotation(com_ann)
