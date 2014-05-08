from google.appengine.ext import ndb

class CullJob(ndb.Model):
	"""Contains the information needed to specify a culling job"""
	similarity = ndb.FloatProperty(required=True)  # The requested maximum percentage sequence similarity permissible.
	minRes = ndb.FloatProperty(required=True)  # The requested minimum resolution permissible.
	maxRes = ndb.FloatProperty(required=True)  # The requested maximum resolution permissible.
	maxRVal = ndb.FloatProperty(required=True)  # The requested maximum r value permissible.
	minLen = ndb.IntegerProperty(required=True, default=-1)  # The requested minimum sequence length permissible.
	maxLen = ndb.IntegerProperty(required=True, default=-1)  # The requested minimum sequence length permissible.
	skipNonXRay = ndb.BooleanProperty(required=True, default=True) # Whether chains with a structure determined by a means other than xray crystallography
																   # should be considered.
	skipAlphaCarbonOnly = ndb.BooleanProperty(required=True, default=True) # Whether chains with a structure consisting solely of alpha carbons should be
																		   # considered.
	requestDate = ndb.DateTimeProperty(required=True)  # The date when the request was made.
	chains = ndb.TextProperty(required=True)  # The chains supplied by the user. The string takes the form 'chainA\nchainB\nchainC.....'.
	nonredundant = ndb.TextProperty()  # The nonredundant chains returned by the culling process. The string takes the form 'chainA\nchainB\nchainC.....'.
	email = ndb.StringProperty(required=True)  # The email address supplied.

class Chains(ndb.Model):
	"""The information needed for each chain"""
	chain = ndb.StringProperty(required=True)  # The chain id for the chain. Also used as the unique id for the entity.
	resolution = ndb.FloatProperty(required=True)  # The resolution of the chain's structure.
	rVal = ndb.FloatProperty(required=True)  # The r value of the chain's structure.
	sequence = ndb.TextProperty(required=True)  # The chain's sequence.
	sequenceLength = ndb.ComputedProperty(lambda self: len(self.sequence))  # The number of amino acids in the chain's sequence.
	nonXRay = ndb.BooleanProperty(required=True)  # Whether the chain's structure was determined using a means other than xray crystallography.
	alphaCarbonOnly = ndb.BooleanProperty(required=True)  # Whether the chain's structure contains only alpha carbons.
	representativeChain = ndb.StringProperty(required=True)  # The id of the chain with the same sequence as this chain that represents all chains with that
															 # sequence.

class Similarity(ndb.Model):
	"""The similarity information, grouped by chains with identical sequences."""
	chainA = ndb.StringProperty(required=True)  # The chain id for one of the chains in the similarity relationship.
	chainB = ndb.StringProperty(required=True)  # The chain id for the other chain in the similarity relationship.
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