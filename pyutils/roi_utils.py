import numpy as np

from skimage.draw import polygon2mask
import omero
from omero.rtypes import rint, rstring


def get_rois_as_labels(image, conn):
    """
    Parameters
    ----------
    image : omero `Image` obect
    conn : connection to the omero DB

    Returns
    -------
    labels : `np.ndarray` with the image shape

    """

    image = conn.getObject("Image", 1)
    imshape = (image.getSizeX(), image.getSizeY())

    roi_service = conn.getRoiService()
    rois = roi_service.findByImage(image.getId(), None).rois
    labels = np.zeros(imshape)
    for i, roi in enumerate(rois):
        for u in range(roi.sizeOfShapes()):
            shape = roi.getShape(u)
            labels += mask_from_polyon_shape(shape, imshape) * (i + 1)

    return labels


def mask_from_polyon_shape(shape, imshape):
    points = shape.getPoints()

    points = np.array(([float(v) for v in l.split(",")] for l in points.val.split(" ")))
    return polygon2mask(imshape, points).astype(np.uint8)


def polygon_to_shape(polygon, z=0, t=0, c=0):
    shape = omero.model.PolygonI()
    shape.theZ = rint(z)
    shape.theT = rint(t)
    shape.theC = rint(c)
    shape.points = rstring(", ".join((f"{int(p[0])},{int(p[1])}" for p in polygon)))
    return shape


def create_roi(img, polygons, conn):

    updateService = conn.getUpdateService()
    # create an ROI, link it to Image
    roi = omero.model.RoiI()
    # use the omero.model.ImageI that underlies the 'image' wrapper
    roi.setImage(img._obj)
    for poly in polygons:
        shape = polygon_to_shape(poly, z=0, t=0, c=0)
        roi.addShape(shape)
    # Save the ROI (saves any linked shapes too)
    return updateService.saveAndReturnObject(roi)
