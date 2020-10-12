import os
import logging
import tempfile
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


log = logging.getLogger(__name__)
logfile = logging.FileHandler("auto_importer.log")
log.setLevel("INFO")
log.addHandler(logfile)


def auto_reconnect(fun):
    # assumes the connection object is the first argument
    def decorrated(*args, **kwargs):
        conn = args[0]
        if not conn.isConnected():
            conn.connect()
        return fun(*args, **kwargs)

    return decorrated


def auto_annotate(conf, dry_run=False):

    conn = BlitzGateway(
        username=conf["username"],
        passwd=conf["password"],
        host=conf["server"],
        port=conf["port"],
    )
    try:
        pairs = pair_annotation_to_datasets(conn, conf["base_dir"], conf["tsv_file"])
        log.info(f"Annotating {len(pairs)} dataset/annotation pairs")
        if dry_run:
            print("Would annotate:")
            print(pairs)
            return

        for dset_id, annotation_yml in pairs:
            annotate(conn, dset_id, annotation_yml, object_type="Dataset")
    finally:
        conn.close()


@auto_reconnect
def annotate(conn, object_id, annotation_yml, object_type="Dataset"):
    """Applies the annotations in `annotation_yml` to the dataset

    Parameters
    ----------
    conn: An `omero.gateway.BlitzGateway` connection
    dataset_id: int - the Id of the dataset to annotate
    annnotation_yml: str or `Path` a yml file containing the annotation

    """
    annotation_yml = Path(annotation_yml)
    annotated = conn.getObject(object_type, object_id)
    log.info(f"\n")
    log.info(f"Annotating {object_type} {object_id} with {annotation_yml.as_posix()}")

    with annotation_yml.open("r") as ann_yml:
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
        annotated.linkAnnotation(map_ann)

    for tag in ann.get("tags", []):
        log.info(f"Adding tag: {tag}")
        tag_ann = TagAnnotationWrapper(conn)
        tag_ann.setValue(tag)
        tag_ann.save()
        annotated.linkAnnotation(tag_ann)

    comment = ann.get("comment", "")
    if comment:
        log.info(f"Adding comment: {comment}")
        com_ann = CommentAnnotationWrapper(conn)
        com_ann.setValue(comment)
        com_ann.save()
        annotated.linkAnnotation(com_ann)


@auto_reconnect
def pair_annotation_to_datasets(conn, base_dir, tsv_file):

    base_dir = Path(base_dir)
    with open(tsv_file, "r") as tsvf:
        new_datasets = [
            _parse_tsv_line(line) for line in tsvf if "Dataset:@name:" in line
        ]

    annotation_ymls = collect_annotations(base_dir)
    log.info(annotation_ymls)
    pairs = []
    for dataset in new_datasets:
        dset_dir = dataset["directory"].relative_to(base_dir)
        dset_id = _find_dataset_id(conn, dataset)["dataset"]
        if dset_dir in annotation_ymls:
            pairs.append((dset_id, annotation_ymls[dset_dir]))
        else:
            for parent in list(dset_dir.parents)[::-1]:
                if parent in annotation_ymls:
                    pairs.append((dset_id, annotation_ymls[parent]))
                    break
            else:
                log.info(f"No annotation found above {dset_dir}")
    return pairs


@auto_reconnect
def _find_dataset_id(conn, dataset):

    dsets = conn.getObjects("Dataset", attributes={"name": dataset["dataset"]})
    for dset in dsets:
        projs = [p for p in dset.getAncestry() if p.name == dataset["project"]]
        if projs:
            log.info(
                f"Found dataset {dataset['dataset']} of project {dataset['project']}"
            )
            return {"dataset": dset.getId(), "project": projs[0].getId()}
    raise ValueError(f"No dataset {dataset} was found in the base")


def collect_annotations(base_dir):

    base_dir = Path(base_dir)
    all_ymls = base_dir.glob("**/*.yml")
    # This is relative to base_dir
    annotation_ymls = {
        yml.parent.relative_to(base_dir): base_dir / yml
        for yml in all_ymls
        if _is_annotation(base_dir / yml)
    }
    return annotation_ymls


def _parse_tsv_line(tsv_line):
    cols = tsv_line.split("\t")

    target = cols[0]
    project, dataset = target.split("/")
    directory = Path(cols[2]).parent
    return {
        "project": project.split(":")[-1],
        "dataset": dataset.split(":")[-1],
        "directory": directory,
    }


def _has_annotation(directory):
    ymls = Path(directory).glob("*.yml")
    if not ymls:
        return False
    for yml in ymls:
        if _is_annotation(yml):
            return yml
    return False


def _is_annotation(yml):
    with open(yml, "r") as fh:
        return "# omero annotation file" in fh.readline()