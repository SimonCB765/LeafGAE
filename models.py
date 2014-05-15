from google.appengine.ext import ndb

class CullJob(ndb.Model):
    """Contains the information needed to specify a culling job"""

    similarity = ndb.FloatProperty(required=True)  # The requested maximum percentage sequence similarity permissible.
    minRes = ndb.FloatProperty(required=True)  # The requested minimum resolution permissible.
    maxRes = ndb.FloatProperty(required=True)  # The requested maximum resolution permissible.
    maxRVal = ndb.FloatProperty(required=True)  # The requested maximum r value permissible.
    minLen = ndb.IntegerProperty(required=True)  # The requested minimum sequence length permissible.
    maxLen = ndb.IntegerProperty(required=True)  # The requested minimum sequence length permissible.
    includeNonXray = ndb.BooleanProperty(required=True, default=True) # Whether chains with a structure determined by a means other than xray diffraction
                                                                      # should be included.
    includeAlphaCarbon = ndb.BooleanProperty(required=True, default=True) # Whether chains with a structure consisting solely of alpha carbons should be
                                                                          # included.
    requestDate = ndb.DateTimeProperty(auto_now=True)  # The date when the request was made.
    chains = ndb.TextProperty(required=True)  # The chains supplied by the user. The string takes the form 'chainA\nchainB\nchainC.....'.
    nonredundant = ndb.TextProperty()  # The nonredundant chains returned by the culling process. The string takes the form 'chainA\nchainB\nchainC.....'.
    email = ndb.StringProperty(required=True)  # The email address supplied.

class Chain(ndb.Model):
    """The information needed for each chain"""

    chain = ndb.StringProperty(required=True)  # The chain id for the chain. Also used as the unique id for the entity.
    resolution = ndb.FloatProperty(required=True)  # The resolution of the chain's structure.
    rVal = ndb.FloatProperty(required=True)  # The r value of the chain's structure.
    sequenceLength = ndb.IntegerProperty(required=True)  # The number of amino acids in the chain's sequence.
    nonXRay = ndb.BooleanProperty(required=True)  # Whether the chain's structure was determined using a means other than xray crystallography.
    alphaCarbonOnly = ndb.BooleanProperty(required=True)  # Whether the chain's structure contains only alpha carbons.
    representativeChainGrouping = ndb.StringProperty(required=True)  # The id of the chain grouping that represents all chains with the same sequence as this
                                                                     # chain.

class Similarity(ndb.Model):
    """The similarity information, grouped by chains with identical sequences."""

    chainGroupingA = ndb.StringProperty(required=True)  # The chain grouping id for one of the chain groups in the similarity relationship.
    chainGroupingB = ndb.StringProperty(required=True)  # The chain grouping id for the other chain group in the similarity relationship.
    similarity = ndb.FloatProperty(required=True)  # The similarity between the two chains.

class PreCulledList(ndb.Model):
    """The information about each pre-culled list"""

    details = ndb.StringProperty(required=True)  # Contains the information needed to uniquely identify the pre-culled list.
                                                 # The string is of the form A_B_C_D_E_F where:
                                                 # A is the similarity cutoff used
                                                 # B is the maximum resolution
                                                 # C is the maximum r value
                                                 # D is whether nonXRay structures are skipped (Y or N)
                                                 # E is whether alpha carbon only structures are skipped (Y or N)
                                                 # Also used as the unique id for the entity.
    listBlobKey = ndb.BlobKeyProperty(required=True)  # The blob key for the stored gzipped file.