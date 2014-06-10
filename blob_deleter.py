from google.appengine.ext import blobstore
import logging

def main(blobKey):
    """Task to delete a blob given its key"""

    # Setup logging.
    logging.getLogger().setLevel(logging.DEBUG)

    try:
        blobstore.delete(blobKey)
    except:
        logging.exception('Failed to delete blob with key {0}.'.format(blobKey))

    return ''